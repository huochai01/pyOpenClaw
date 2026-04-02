from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
from typing import Any, AsyncIterator

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_deepseek import ChatDeepSeek

from config import ConfigStore
from graph.memory_indexer import MemoryIndexer
from graph.prompt_builder import build_system_prompt
from graph.session_manager import SessionManager
from tools import get_all_tools


class AgentManager:
    def __init__(self) -> None:
        self.base_dir: Path | None = None
        self.llm = None
        self.tools: list[Any] = []
        self.session_manager: SessionManager | None = None
        self.memory_indexer: MemoryIndexer | None = None
        self.config_store: ConfigStore | None = None

    def initialize(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.llm = ChatDeepSeek(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            temperature=0.3,
            streaming=True,
        )
        self.tools = get_all_tools(base_dir)
        self.session_manager = SessionManager(base_dir)
        self.memory_indexer = MemoryIndexer(base_dir)
        self.config_store = ConfigStore(base_dir)

    def _build_agent(self):
        if self.base_dir is None or self.config_store is None:
            raise RuntimeError("AgentManager is not initialized.")

        rag_mode = self.config_store.get_rag_mode()
        prompt = build_system_prompt(self.base_dir, rag_mode=rag_mode)
        signature = inspect.signature(create_agent)
        kwargs = {"model": self.llm, "tools": self.tools}
        if "system_prompt" in signature.parameters:
            kwargs["system_prompt"] = prompt
        elif "prompt" in signature.parameters:
            kwargs["prompt"] = prompt
        else:
            kwargs["system_message"] = prompt
        return create_agent(**kwargs)

    def _build_messages(self, history: list[dict[str, Any]], message: str) -> list[Any]:
        messages: list[Any] = []
        for item in history:
            role = item.get("role")
            content = item.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=message))
        return messages

    async def generate_title(self, message: str) -> str:
        prompt = (
            "请根据下面的用户首条消息生成一个不超过20字的中文会话标题，"
            "只返回标题，不要加引号或解释。\n\n"
            f"用户消息: {message}"
        )
        result = await self.llm.ainvoke(prompt)
        title = getattr(result, "content", "") if result else ""
        return str(title).strip()[:20] or "新对话"

    async def summarize_messages(self, messages: list[dict[str, Any]]) -> str:
        payload = json.dumps(messages, ensure_ascii=False, indent=2)
        prompt = (
            "请将以下对话总结为不超过500字的中文摘要，保留事实、偏好、任务进展与待办。\n\n"
            f"{payload}"
        )
        result = await self.llm.ainvoke(prompt)
        return str(getattr(result, "content", "")).strip()

    async def astream(self, message: str, history: list[dict[str, Any]]) -> AsyncIterator[dict[str, Any]]:
        if self.config_store is None or self.memory_indexer is None:
            raise RuntimeError("AgentManager is not initialized.")

        rag_mode = self.config_store.get_rag_mode()
        working_history = list(history)
        if rag_mode:
            retrieval_results = self.memory_indexer.retrieve(message, top_k=3)
            yield {"type": "retrieval", "data": {"query": message, "results": retrieval_results}}
            if retrieval_results:
                retrieval_text = "\n\n".join(
                    f"- {item['text']}" for item in retrieval_results if item.get("text")
                )
                working_history.append(
                    {
                        "role": "assistant",
                        "content": f"[记忆检索结果]\n{retrieval_text}",
                        "tool_calls": [],
                    }
                )

        agent = self._build_agent()
        messages = self._build_messages(working_history, message)
        print(messages)
        current_segment = ""
        all_segments: list[dict[str, Any]] = []
        current_tool_calls: list[dict[str, Any]] = []
        pending_new_response = False

        async for event in agent.astream_events({"messages": messages}, version="v2"):
            event_name = event.get("event")
            if event_name == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                content = _extract_chunk_text(chunk)
                if not content:
                    continue
                if pending_new_response:
                    if current_segment.strip() or current_tool_calls:
                        all_segments.append({"content": current_segment, "tool_calls": current_tool_calls})
                    current_segment = ""
                    current_tool_calls = []
                    pending_new_response = False
                    yield {"type": "new_response", "data": 0}
                current_segment += content
                yield {"type": "token", "data": {"content": content}}
            elif event_name == "on_tool_start":
                data = event.get("data", {})
                tool_name = event.get("name") or data.get("name") or "tool"
                yield {"type": "tool_start", "data": {"tool": tool_name, "input": data.get("input")}}
            elif event_name == "on_tool_end":
                data = event.get("data", {})
                tool_name = event.get("name") or "tool"
                tool_output = data.get("output")
                current_tool_calls.append(
                    {"tool": tool_name, "input": data.get("input"), "output": tool_output}
                )
                pending_new_response = True
                yield {"type": "tool_end", "data": {"tool": tool_name, "output": tool_output}}

        if current_segment.strip() or current_tool_calls:
            all_segments.append({"content": current_segment, "tool_calls": current_tool_calls})

        content = "\n\n".join(segment["content"] for segment in all_segments if segment["content"].strip())
        yield {"type": "done", "data": {"content": content, "segments": all_segments}}


def _extract_chunk_text(chunk: Any) -> str:
    if chunk is None:
        return ""
    if hasattr(chunk, "content") and isinstance(chunk.content, str):
        return chunk.content
    if hasattr(chunk, "text") and isinstance(chunk.text, str):
        return chunk.text
    content = getattr(chunk, "content", None)
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return str(chunk) if isinstance(chunk, str) else ""

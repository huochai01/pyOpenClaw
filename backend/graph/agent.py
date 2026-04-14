from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
from typing import Any, AsyncIterator

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_deepseek import ChatDeepSeek

from config import ConfigStore
from graph.memory_indexer import MemoryIndexer
from graph.prompt_builder import build_system_prompt
from graph.session_manager import SessionManager
from scheduler import ScheduledTaskStore
from tools import get_all_tools


class AgentManager:
    def __init__(self) -> None:
        self.base_dir: Path | None = None
        self.llm = None
        self.tools: list[Any] = []
        self.session_manager: SessionManager | None = None
        self.memory_indexer: MemoryIndexer | None = None
        self.config_store: ConfigStore | None = None
        self.task_store: ScheduledTaskStore | None = None

    def initialize(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.llm = ChatDeepSeek(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            temperature=0.3,
            streaming=True,
        )
        self.session_manager = SessionManager(base_dir)
        self.memory_indexer = MemoryIndexer(base_dir)
        self.config_store = ConfigStore(base_dir)
        self.task_store = ScheduledTaskStore(base_dir)
        self.tools = get_all_tools(base_dir)

    def _build_agent(self, session_id: str | None = None):
        if self.base_dir is None or self.config_store is None:
            raise RuntimeError("AgentManager is not initialized.")

        rag_mode = self.config_store.get_rag_mode()
        prompt = build_system_prompt(self.base_dir, rag_mode=rag_mode)
        signature = inspect.signature(create_agent)
        kwargs = {
            "model": self.llm,
            "tools": get_all_tools(
                self.base_dir,
                task_store=self.task_store,
                session_id=session_id,
            ),
        }
        if "system_prompt" in signature.parameters:
            kwargs["system_prompt"] = prompt
            print(prompt)
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

    async def astream(
        self,
        message: str,
        history: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
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

        agent = self._build_agent(session_id=session_id)
        messages = self._build_messages(working_history, message)
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
                yield {
                    "type": "tool_start",
                    "data": {"tool": tool_name, "input": _to_jsonable(data.get("input"))},
                }
            elif event_name == "on_tool_end":
                data = event.get("data", {})
                tool_name = event.get("name") or "tool"
                tool_output = _to_jsonable(data.get("output"))
                current_tool_calls.append(
                    {"tool": tool_name, "input": _to_jsonable(data.get("input")), "output": tool_output}
                )
                pending_new_response = True
                yield {"type": "tool_end", "data": {"tool": tool_name, "output": tool_output}}

        if current_segment.strip() or current_tool_calls:
            all_segments.append({"content": current_segment, "tool_calls": current_tool_calls})

        content = "\n\n".join(segment["content"] for segment in all_segments if segment["content"].strip())
        yield {"type": "done", "data": {"content": content, "segments": all_segments}}

    async def arun(self, message: str, session_id: str) -> dict[str, Any]:
        if self.session_manager is None:
            raise RuntimeError("Session manager is not initialized.")
        history = self.session_manager.load_session_for_agent(session_id)
        segments: list[dict[str, Any]] = []
        async for event in self.astream(message, history, session_id=session_id):
            if event["type"] == "done":
                segments = event["data"].get("segments", [])
        content = "\n\n".join(item.get("content", "") for item in segments if item.get("content", "").strip())
        tool_calls: list[dict[str, Any]] = []
        for item in segments:
            tool_calls.extend(item.get("tool_calls", []))
        return {"content": content, "tool_calls": _to_jsonable(tool_calls)}


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


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, BaseMessage):
        return {
            "type": value.__class__.__name__,
            "content": _to_jsonable(getattr(value, "content", "")),
            "name": getattr(value, "name", None),
            "tool_call_id": getattr(value, "tool_call_id", None),
        }
    if hasattr(value, "model_dump"):
        try:
            return _to_jsonable(value.model_dump())
        except Exception:
            return str(value)
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "__dict__"):
        try:
            return _to_jsonable(vars(value))
        except Exception:
            return str(value)
    return str(value)

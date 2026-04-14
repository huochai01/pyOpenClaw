from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

from graph.agent import AgentManager


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None
    stream: bool = True


def build_router(agent_manager: AgentManager) -> APIRouter:
    router = APIRouter()

    @router.post("/chat")
    async def chat(request: ChatRequest) -> StreamingResponse:
        if agent_manager.session_manager is None:
            raise HTTPException(status_code=500, detail="Session manager is not initialized.")

        session_id = request.session_id or uuid.uuid4().hex
        session = agent_manager.session_manager.ensure_session(session_id)
        is_first_message = len(session.get("messages", [])) == 0
        history = agent_manager.session_manager.load_session_for_agent(session_id)

        async def event_generator():
            assistant_segments: list[dict[str, Any]] = []
            user_saved = False
            try:
                async for event in agent_manager.astream(request.message, history, session_id=session_id):
                    if event["type"] == "done":
                        assistant_segments = event["data"].get("segments", [])
                        event["data"]["session_id"] = session_id
                    yield _sse(event["type"], event["data"])

                agent_manager.session_manager.save_message(session_id, "user", request.message)
                user_saved = True
                for segment in assistant_segments:
                    if segment.get("content", "").strip() or segment.get("tool_calls"):
                        agent_manager.session_manager.save_message(
                            session_id,
                            "assistant",
                            segment.get("content", ""),
                            tool_calls=_to_jsonable(segment.get("tool_calls", [])),
                        )
                if is_first_message:
                    title = await agent_manager.generate_title(request.message)
                    agent_manager.session_manager.rename_session(session_id, title)
                    yield _sse("title", {"session_id": session_id, "title": title})
            except Exception as exc:  # pragma: no cover
                if not user_saved:
                    agent_manager.session_manager.save_message(session_id, "user", request.message)
                error_text = f"发生错误: {exc}"
                agent_manager.session_manager.save_message(session_id, "assistant", error_text)
                yield _sse("error", {"error": str(exc)})

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return router


def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(_to_jsonable(data), ensure_ascii=False)}\n\n"


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

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from graph.agent import AgentManager
from graph.prompt_builder import build_system_prompt


class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=50)


def build_router(agent_manager: AgentManager) -> APIRouter:
    router = APIRouter()

    @router.get("/sessions")
    async def list_sessions():
        return agent_manager.session_manager.list_sessions()

    @router.post("/sessions")
    async def create_session():
        return agent_manager.session_manager.create_session()

    @router.put("/sessions/{session_id}")
    async def rename_session(session_id: str, request: RenameRequest):
        return agent_manager.session_manager.rename_session(session_id, request.title)

    @router.delete("/sessions/{session_id}")
    async def delete_session(session_id: str):
        agent_manager.session_manager.delete_session(session_id)
        return {"ok": True}

    @router.get("/sessions/{session_id}/messages")
    async def get_messages(session_id: str):
        session = agent_manager.session_manager.load_session_file(session_id)
        prompt = build_system_prompt(
            agent_manager.base_dir,
            rag_mode=agent_manager.config_store.get_rag_mode(),
        )
        return {"system_prompt": prompt, **session}

    @router.get("/sessions/{session_id}/history")
    async def get_history(session_id: str):
        return agent_manager.session_manager.load_session_file(session_id)

    @router.post("/sessions/{session_id}/generate-title")
    async def generate_title(session_id: str):
        session = agent_manager.session_manager.load_session_file(session_id)
        first_user_message = next(
            (item.get("content", "") for item in session.get("messages", []) if item.get("role") == "user"),
            "",
        )
        title = await agent_manager.generate_title(first_user_message or "新对话")
        agent_manager.session_manager.rename_session(session_id, title)
        return {"session_id": session_id, "title": title}

    return router

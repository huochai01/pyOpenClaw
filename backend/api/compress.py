from __future__ import annotations

from fastapi import APIRouter, HTTPException

from graph.agent import AgentManager


def build_router(agent_manager: AgentManager) -> APIRouter:
    router = APIRouter()

    @router.post("/sessions/{session_id}/compress")
    async def compress_session(session_id: str):
        session = agent_manager.session_manager.load_session_file(session_id)
        messages = session.get("messages", [])
        if len(messages) < 4:
            raise HTTPException(status_code=400, detail="At least 4 messages are required for compression.")

        count = max(4, len(messages) // 2)
        summary = await agent_manager.summarize_messages(messages[:count])
        return agent_manager.session_manager.compress_history(session_id, summary, count)

    return router

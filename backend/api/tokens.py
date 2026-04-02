from __future__ import annotations

from pathlib import Path

import tiktoken
from fastapi import APIRouter
from pydantic import BaseModel

from graph.prompt_builder import build_system_prompt
from graph.session_manager import SessionManager
from utils.text_files import read_text_file


class TokenFilesRequest(BaseModel):
    paths: list[str]


def build_router(base_dir: Path, session_manager: SessionManager, config_store) -> APIRouter:
    router = APIRouter()
    encoder = tiktoken.get_encoding("cl100k_base")

    @router.get("/tokens/session/{session_id}")
    async def count_session_tokens(session_id: str):
        system_prompt = build_system_prompt(base_dir, rag_mode=config_store.get_rag_mode())
        session = session_manager.load_session_file(session_id)
        message_text = "\n".join(item.get("content", "") for item in session.get("messages", []))
        system_tokens = len(encoder.encode(system_prompt))
        message_tokens = len(encoder.encode(message_text))
        return {
            "system_tokens": system_tokens,
            "message_tokens": message_tokens,
            "total_tokens": system_tokens + message_tokens,
        }

    @router.post("/tokens/files")
    async def count_file_tokens(request: TokenFilesRequest):
        result = {}
        for raw_path in request.paths:
            path = (base_dir / raw_path).resolve()
            text = read_text_file(path, errors="replace") if path.exists() else ""
            result[raw_path] = len(encoder.encode(text))
        return result

    return router

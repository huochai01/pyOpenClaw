from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from config import ConfigStore


class RagModeRequest(BaseModel):
    enabled: bool


def build_router(config_store: ConfigStore) -> APIRouter:
    router = APIRouter()

    @router.get("/config/rag-mode")
    async def get_rag_mode():
        return {"enabled": config_store.get_rag_mode()}

    @router.put("/config/rag-mode")
    async def set_rag_mode(request: RagModeRequest):
        config_store.set_rag_mode(request.enabled)
        return {"enabled": request.enabled}

    return router

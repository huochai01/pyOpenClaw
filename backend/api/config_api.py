from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from config import ConfigStore
from tools.skills_scanner import scan_skills


class RagModeRequest(BaseModel):
    enabled: bool


class SkillToggleRequest(BaseModel):
    enabled: bool


def build_router(config_store: ConfigStore, base_dir) -> APIRouter:
    router = APIRouter()

    @router.get("/config/rag-mode")
    async def get_rag_mode():
        return {"enabled": config_store.get_rag_mode()}

    @router.put("/config/rag-mode")
    async def set_rag_mode(request: RagModeRequest):
        config_store.set_rag_mode(request.enabled)
        return {"enabled": request.enabled}

    @router.put("/config/skills/{skill_name}")
    async def set_skill_enabled(skill_name: str, request: SkillToggleRequest):
        config_store.set_skill_enabled(skill_name, request.enabled)
        scan_skills(base_dir, disabled_skills=set(config_store.get_disabled_skills()))
        return {"name": skill_name, "enabled": request.enabled}

    return router

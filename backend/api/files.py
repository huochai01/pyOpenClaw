from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from graph.memory_indexer import MemoryIndexer
from utils.text_files import read_text_file, write_text_file


ALLOWED_PREFIXES = ("workspace/", "memory/", "skills/", "knowledge/")
ALLOWED_ROOT_FILES = {"SKILLS_SNAPSHOT.md"}


class SaveFileRequest(BaseModel):
    path: str
    content: str


def build_router(base_dir: Path, memory_indexer: MemoryIndexer) -> APIRouter:
    router = APIRouter()

    @router.get("/files")
    async def get_file(path: str = Query(...)):
        file_path = _validate_path(base_dir, path)
        return {"path": path, "content": read_text_file(file_path, errors="replace")}

    @router.post("/files")
    async def save_file(request: SaveFileRequest):
        file_path = _validate_path(base_dir, request.path)
        write_text_file(file_path, request.content)
        if request.path == "memory/MEMORY.md":
            memory_indexer.rebuild_index()
        return {"ok": True, "path": request.path}

    @router.get("/skills")
    async def list_skills():
        skills = []
        for skill_path in sorted((base_dir / "skills").glob("*/SKILL.md")):
            skills.append(
                {
                    "name": skill_path.parent.name,
                    "path": skill_path.relative_to(base_dir).as_posix(),
                }
            )
        return skills

    return router


def _validate_path(base_dir: Path, raw_path: str) -> Path:
    normalized = raw_path.replace("\\", "/").lstrip("/")
    if normalized not in ALLOWED_ROOT_FILES and not normalized.startswith(ALLOWED_PREFIXES):
        raise HTTPException(status_code=400, detail="Path is not allowed.")

    path = (base_dir / normalized).resolve()
    if base_dir.resolve() not in path.parents and path != base_dir.resolve():
        raise HTTPException(status_code=400, detail="Path traversal is not allowed.")
    return path

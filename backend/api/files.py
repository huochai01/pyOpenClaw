from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from config import ConfigStore
from graph.memory_indexer import MemoryIndexer
from tools.search_knowledge_tool import SearchKnowledgeBaseTool
from tools.skills_scanner import scan_skills
from utils.text_files import normalize_text_content, read_text_file, write_text_file


ALLOWED_PREFIXES = ("workspace/", "memory/", "skills/", "knowledge/")
ALLOWED_ROOT_FILES = {"SKILLS_SNAPSHOT.md"}
ALLOWED_KNOWLEDGE_SUFFIXES = {".md", ".txt", ".json"}


class SaveFileRequest(BaseModel):
    path: str
    content: str


def build_router(base_dir: Path, memory_indexer: MemoryIndexer, config_store: ConfigStore) -> APIRouter:
    router = APIRouter()
    knowledge_indexer = SearchKnowledgeBaseTool(root_dir=base_dir)

    @router.get("/files")
    async def get_file(path: str = Query(...)):
        file_path = _validate_path(base_dir, path)
        return {"path": path, "content": read_text_file(file_path, errors="replace")}

    @router.post("/files")
    async def save_file(request: SaveFileRequest):
        file_path = _validate_path(base_dir, request.path)
        write_text_file(file_path, normalize_text_content(request.content))
        if request.path == "memory/MEMORY.md":
            memory_indexer.rebuild_index()
        if request.path.startswith("skills/") and request.path.endswith("/SKILL.md"):
            scan_skills(base_dir, disabled_skills=set(config_store.get_disabled_skills()))
        return {"ok": True, "path": request.path}

    @router.get("/skills")
    async def list_skills():
        skills = []
        for skill_path in sorted((base_dir / "skills").glob("*/SKILL.md")):
            skills.append(
                {
                    "name": skill_path.parent.name,
                    "path": skill_path.relative_to(base_dir).as_posix(),
                    "enabled": config_store.is_skill_enabled(skill_path.parent.name),
                }
            )
        return skills

    @router.get("/knowledge/files")
    async def list_knowledge_files():
        items = []
        knowledge_dir = base_dir / "knowledge"
        for file_path in sorted(knowledge_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in ALLOWED_KNOWLEDGE_SUFFIXES:
                continue
            items.append(
                {
                    "name": file_path.name,
                    "path": file_path.relative_to(base_dir).as_posix(),
                }
            )
        return items

    @router.post("/knowledge/upload")
    async def upload_knowledge_file(file: UploadFile = File(...)):
        if not file.filename:
            raise HTTPException(status_code=400, detail="File name is required.")

        safe_name = Path(file.filename).name
        suffix = Path(safe_name).suffix.lower()
        if suffix not in ALLOWED_KNOWLEDGE_SUFFIXES:
            raise HTTPException(status_code=400, detail="Only .md, .txt, .json files are supported.")

        destination = _validate_path(base_dir, f"knowledge/{safe_name}")
        data = await file.read()
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise HTTPException(status_code=400, detail="Only UTF-8 text files are supported.") from exc

        write_text_file(destination, normalize_text_content(text))
        knowledge_indexer.rebuild_index()
        return {"ok": True, "path": destination.relative_to(base_dir).as_posix()}

    @router.delete("/knowledge/files")
    async def delete_knowledge_file(path: str = Query(...)):
        file_path = _validate_path(base_dir, path)
        if not path.startswith("knowledge/"):
            raise HTTPException(status_code=400, detail="Only knowledge files can be deleted here.")
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Knowledge file not found.")

        file_path.unlink()
        knowledge_indexer.rebuild_index()
        return {"ok": True, "path": path}

    return router


def _validate_path(base_dir: Path, raw_path: str) -> Path:
    normalized = raw_path.replace("\\", "/").lstrip("/")
    if normalized not in ALLOWED_ROOT_FILES and not normalized.startswith(ALLOWED_PREFIXES):
        raise HTTPException(status_code=400, detail="Path is not allowed.")

    path = (base_dir / normalized).resolve()
    if base_dir.resolve() not in path.parents and path != base_dir.resolve():
        raise HTTPException(status_code=400, detail="Path traversal is not allowed.")
    return path

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from utils.text_files import read_text_file


class ReadFileInput(BaseModel):
    path: str = Field(..., description="相对于项目根目录的文件路径")


class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = "读取项目根目录内的文件内容。"
    args_schema: ClassVar[type[BaseModel]] = ReadFileInput
    root_dir: Path
    max_output_chars: int = 10000

    def _run(self, path: str) -> str:
        resolved = _resolve_safe_path(self.root_dir, path)
        if not resolved.exists() or not resolved.is_file():
            return f"File not found: {path}"

        text = read_text_file(resolved, errors="replace")
        if len(text) > self.max_output_chars:
            text = text[: self.max_output_chars] + "\n...[truncated]"
        return text

    async def _arun(self, path: str) -> str:
        return self._run(path)


def _resolve_safe_path(root_dir: Path, path: str) -> Path:
    candidate = (root_dir / path).resolve()
    if root_dir not in candidate.parents and candidate != root_dir:
        raise ValueError("Path escapes root directory.")
    return candidate

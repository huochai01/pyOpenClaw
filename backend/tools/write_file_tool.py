from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from utils.text_files import read_text_file, write_text_file


class WriteFileInput(BaseModel):
    path: str = Field(..., description="相对项目根目录的目标文件路径")
    content: str = Field(..., description="要写入文件的完整文本内容")
    append: bool = Field(default=False, description="是否追加到文件末尾")


class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = "安全写入项目内文本文件，可覆盖文件或仅追加。修改 Markdown、记忆、配置、代码等文本文件时优先使用此工具。"
    args_schema: ClassVar[type[BaseModel]] = WriteFileInput
    root_dir: Path

    def _run(self, path: str, content: str, append: bool = False) -> str:
        resolved = _resolve_safe_path(self.root_dir, path)
        existing = ""
        if append and resolved.exists():
            existing = read_text_file(resolved, errors="replace")

        next_content = f"{existing}{content}" if append else content
        write_text_file(resolved, next_content)
        return f"Saved UTF-8 text file: {path}"

    async def _arun(self, path: str, content: str, append: bool = False) -> str:
        return self._run(path, content, append)


def _resolve_safe_path(root_dir: Path, path: str) -> Path:
    candidate = (root_dir / path).resolve()
    if root_dir not in candidate.parents and candidate != root_dir:
        raise ValueError("Path escapes root directory.")
    return candidate

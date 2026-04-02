from __future__ import annotations

import subprocess
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool


class TerminalInput(BaseModel):
    command: str = Field(..., description="需要执行的 shell 命令")


class TerminalTool(BaseTool):
    name: str = "terminal"
    description: str = "在项目根目录内执行安全的 shell 命令。适合查询环境、运行脚本和检查状态，不建议用来重定向写入文本文件。"
    args_schema: ClassVar[type[BaseModel]] = TerminalInput
    root_dir: Path
    timeout_seconds: int = 10
    max_output_chars: int = 5000
    blacklist: list[str] = [
        "rm -rf /",
        "rm -rf *",
        "mkfs",
        "shutdown",
        "reboot",
        "poweroff",
        ":(){:|:&};:",
        "del /f /s /q",
        "format ",
    ]

    def _run(self, command: str) -> str:
        lowered = command.lower()
        if any(token in lowered for token in self.blacklist):
            return "Command blocked by terminal sandbox."

        completed = subprocess.run(
            command,
            cwd=self.root_dir,
            shell=True,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            encoding="utf-8",
            errors="replace",
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        if not output.strip():
            output = f"Command finished with exit code {completed.returncode}."
        return _truncate(output, self.max_output_chars)

    async def _arun(self, command: str) -> str:
        return self._run(command)


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"

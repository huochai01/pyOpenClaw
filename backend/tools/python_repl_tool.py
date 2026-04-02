from __future__ import annotations

import contextlib
import io
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class PythonReplInput(BaseModel):
    code: str = Field(..., description="需要执行的 Python 代码")


class PythonReplTool(BaseTool):
    name: str = "python_repl"
    description: str = "执行 Python 代码并返回 stdout。"
    args_schema: ClassVar[type[BaseModel]] = PythonReplInput
    root_dir: Path
    max_output_chars: int = 5000

    def _run(self, code: str) -> str:
        stdout = io.StringIO()
        scope = {
            "__builtins__": __builtins__,
            "__name__": "__main__",
            "ROOT_DIR": str(self.root_dir),
        }
        with contextlib.redirect_stdout(stdout):
            exec(code, scope, scope)
        output = stdout.getvalue().strip() or "Python code executed successfully."
        return output[: self.max_output_chars]

    async def _arun(self, code: str) -> str:
        return self._run(code)

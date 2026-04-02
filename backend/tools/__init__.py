from __future__ import annotations

from pathlib import Path

from .fetch_url_tool import FetchUrlTool
from .python_repl_tool import PythonReplTool
from .read_file_tool import ReadFileTool
from .search_knowledge_tool import SearchKnowledgeBaseTool
from .terminal_tool import TerminalTool
from .write_file_tool import WriteFileTool


def get_all_tools(base_dir: Path) -> list:
    return [
        TerminalTool(root_dir=base_dir),
        PythonReplTool(root_dir=base_dir),
        FetchUrlTool(),
        ReadFileTool(root_dir=base_dir),
        WriteFileTool(root_dir=base_dir),
        SearchKnowledgeBaseTool(root_dir=base_dir),
    ]

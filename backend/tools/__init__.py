from __future__ import annotations

from pathlib import Path

from .fetch_url_tool import FetchUrlTool
from .python_repl_tool import PythonReplTool
from .read_file_tool import ReadFileTool
from .schedule_task_tool import CancelScheduledTaskTool, ListScheduledTasksTool, ScheduleTaskTool
from .search_knowledge_tool import SearchKnowledgeBaseTool
from .terminal_tool import TerminalTool
from .write_file_tool import WriteFileTool


def get_all_tools(base_dir: Path, *, task_store=None, session_id: str | None = None) -> list:
    tools = [
        TerminalTool(root_dir=base_dir),
        PythonReplTool(root_dir=base_dir),
        FetchUrlTool(),
        ReadFileTool(root_dir=base_dir),
        WriteFileTool(root_dir=base_dir),
        SearchKnowledgeBaseTool(root_dir=base_dir),
        ScheduleTaskTool(root_dir=base_dir, task_store=task_store, session_id=session_id or ""),
        ListScheduledTasksTool(task_store=task_store, session_id=session_id or ""),
        CancelScheduledTaskTool(task_store=task_store, session_id=session_id or ""),
    ]
    return tools

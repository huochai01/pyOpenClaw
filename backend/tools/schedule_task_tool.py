from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool
from scheduler.task_store import ScheduledTaskStore


class ScheduleTaskInput(BaseModel):
    title: str = Field(..., description="任务标题，例如：晚八点吃药提醒")
    prompt: str = Field(..., description="定时触发后要执行的任务内容")
    time_of_day: str = Field(..., description="每天执行时间，格式 HH:MM，例如 20:00")
    timezone: str = Field(default="Asia/Shanghai", description="IANA 时区名称")


class ScheduleTaskTool(BaseTool):
    name: str = "schedule_task"
    description: str = "创建每天固定时间执行的定时任务，并绑定到当前会话。"
    args_schema: ClassVar[type[BaseModel]] = ScheduleTaskInput
    root_dir: Path
    task_store: ScheduledTaskStore | None = None
    session_id: str = ""

    def _run(self, title: str, prompt: str, time_of_day: str, timezone: str = "Asia/Shanghai") -> str:
        if self.task_store is None or not self.session_id:
            return json.dumps({"error": "No active session available for scheduling."}, ensure_ascii=False, indent=2)
        task = self.task_store.create_task(
            session_id=self.session_id,
            title=title,
            prompt=prompt,
            time_of_day=time_of_day,
            timezone=timezone,
        )
        return json.dumps(task, ensure_ascii=False, indent=2)

    async def _arun(self, title: str, prompt: str, time_of_day: str, timezone: str = "Asia/Shanghai") -> str:
        return self._run(title, prompt, time_of_day, timezone)


class ListScheduledTasksInput(BaseModel):
    include_inactive: bool = Field(default=False, description="是否包含已停用任务")


class ListScheduledTasksTool(BaseTool):
    name: str = "list_scheduled_tasks"
    description: str = "列出当前会话的定时任务。"
    args_schema: ClassVar[type[BaseModel]] = ListScheduledTasksInput
    task_store: ScheduledTaskStore | None = None
    session_id: str = ""

    def _run(self, include_inactive: bool = False) -> str:
        if self.task_store is None or not self.session_id:
            return json.dumps({"error": "No active session available for listing tasks."}, ensure_ascii=False, indent=2)
        items = []
        for item in self.task_store.list_tasks():
            if item.get("session_id") != self.session_id:
                continue
            if not include_inactive and not item.get("active", True):
                continue
            items.append(item)
        return json.dumps(items, ensure_ascii=False, indent=2)

    async def _arun(self, include_inactive: bool = False) -> str:
        return self._run(include_inactive)


class CancelScheduledTaskInput(BaseModel):
    task_id: str = Field(..., description="待取消的定时任务 ID")


class CancelScheduledTaskTool(BaseTool):
    name: str = "cancel_scheduled_task"
    description: str = "取消一个已创建的定时任务。"
    args_schema: ClassVar[type[BaseModel]] = CancelScheduledTaskInput
    task_store: ScheduledTaskStore | None = None
    session_id: str = ""

    def _run(self, task_id: str) -> str:
        if self.task_store is None or not self.session_id:
            return json.dumps({"error": "No active session available for canceling tasks."}, ensure_ascii=False, indent=2)
        task = self.task_store.cancel_task(task_id)
        if task is None or task.get("session_id") != self.session_id:
            return json.dumps({"error": "Task not found."}, ensure_ascii=False, indent=2)
        return json.dumps(task, ensure_ascii=False, indent=2)

    async def _arun(self, task_id: str) -> str:
        return self._run(task_id)
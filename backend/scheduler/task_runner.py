from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime
from zoneinfo import ZoneInfo

from graph.agent import AgentManager
from scheduler.task_store import ScheduledTaskStore


class ScheduledTaskRunner:
    def __init__(self, agent_manager: AgentManager, task_store: ScheduledTaskStore) -> None:
        self.agent_manager = agent_manager
        self.task_store = task_store
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        self._task = None

    async def _run_loop(self) -> None:
        while not self._stop.is_set():
            try:
                for task in self.task_store.due_tasks():
                    await self._run_one(task)
            except Exception as exc:  # pragma: no cover
                print(f"ScheduledTaskRunner error: {exc}")
            await asyncio.sleep(10)

    async def _run_one(self, task: dict) -> None:
        session_id = str(task.get("session_id"))
        timezone = str(task.get("timezone", "Asia/Shanghai"))
        local_now = datetime.now(ZoneInfo(timezone))
        local_date = local_now.date().isoformat()
        trigger_message = (
            f"[定时任务触发]\n"
            f"任务标题: {task.get('title', '定时任务')}\n"
            f"执行时间: {task.get('time_of_day', '00:00')} {timezone}\n"
            f"请执行以下任务并直接给出结果：{task.get('prompt', '')}"
        )
        self.agent_manager.session_manager.ensure_session(session_id)
        self.agent_manager.session_manager.save_message(session_id, "user", trigger_message)
        assistant_index = self.agent_manager.session_manager.append_message(session_id, "assistant", "")

        content = ""
        tool_calls: list[dict] = []
        current_tool_input = None

        try:
            history = self.agent_manager.session_manager.load_session_for_agent(session_id)
            async for event in self.agent_manager.astream(trigger_message, history, session_id=session_id):
                event_type = event.get("type")
                data = event.get("data", {})
                if event_type == "token":
                    content += data.get("content", "")
                    self.agent_manager.session_manager.update_message(
                        session_id,
                        assistant_index,
                        content=content,
                        tool_calls=tool_calls,
                    )
                elif event_type == "tool_start":
                    current_tool_input = data.get("input")
                    tool_calls.append(
                        {
                            "tool": data.get("tool", "tool"),
                            "input": current_tool_input,
                        }
                    )
                    self.agent_manager.session_manager.update_message(
                        session_id,
                        assistant_index,
                        content=content,
                        tool_calls=tool_calls,
                    )
                elif event_type == "tool_end":
                    if tool_calls:
                        tool_calls[-1] = {
                            **tool_calls[-1],
                            "output": data.get("output"),
                        }
                    self.agent_manager.session_manager.update_message(
                        session_id,
                        assistant_index,
                        content=content,
                        tool_calls=tool_calls,
                    )
                elif event_type == "done":
                    final_content = data.get("content", "")
                    if final_content:
                        content = final_content
            self.agent_manager.session_manager.update_message(
                session_id,
                assistant_index,
                content=content,
                tool_calls=tool_calls,
            )
        except Exception as exc:
            error_text = f"{content}\n\n[定时任务执行失败]\n{exc}".strip()
            self.agent_manager.session_manager.update_message(
                session_id,
                assistant_index,
                content=error_text,
                tool_calls=tool_calls,
            )
        finally:
            self.task_store.mark_ran(str(task.get("id")), local_date=local_date)

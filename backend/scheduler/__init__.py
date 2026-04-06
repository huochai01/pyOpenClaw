from __future__ import annotations

__all__ = ["ScheduledTaskRunner", "ScheduledTaskStore"]


def __getattr__(name: str):
    if name == "ScheduledTaskStore":
        from .task_store import ScheduledTaskStore

        return ScheduledTaskStore
    if name == "ScheduledTaskRunner":
        from .task_runner import ScheduledTaskRunner

        return ScheduledTaskRunner
    raise AttributeError(name)

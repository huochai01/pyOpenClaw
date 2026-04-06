from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from utils.text_files import write_text_file


class ScheduledTaskStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.storage_dir = base_dir / "storage"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.storage_dir / "scheduled_tasks.json"
        if not self.path.exists():
            self._write([])

    def list_tasks(self) -> list[dict[str, Any]]:
        data = self._read()
        data.sort(key=lambda item: item.get("created_at", 0), reverse=True)
        return data

    def create_task(
        self,
        *,
        session_id: str,
        title: str,
        prompt: str,
        time_of_day: str,
        timezone: str = "Asia/Shanghai",
        schedule_type: str = "daily",
    ) -> dict[str, Any]:
        _validate_time_of_day(time_of_day)
        ZoneInfo(timezone)
        now = time.time()
        payload = {
            "id": uuid.uuid4().hex,
            "session_id": session_id,
            "title": title.strip() or "定时任务",
            "prompt": prompt.strip(),
            "schedule_type": schedule_type,
            "time_of_day": time_of_day,
            "timezone": timezone,
            "active": True,
            "last_run_local_date": None,
            "created_at": now,
            "updated_at": now,
        }
        items = self._read()
        items.append(payload)
        self._write(items)
        return payload

    def cancel_task(self, task_id: str) -> dict[str, Any] | None:
        items = self._read()
        for item in items:
            if item.get("id") == task_id:
                item["active"] = False
                item["updated_at"] = time.time()
                self._write(items)
                return item
        return None

    def mark_ran(self, task_id: str, *, local_date: str) -> None:
        items = self._read()
        for item in items:
            if item.get("id") == task_id:
                item["last_run_local_date"] = local_date
                item["updated_at"] = time.time()
                break
        self._write(items)

    def due_tasks(self, now_ts: float | None = None) -> list[dict[str, Any]]:
        now_ts = now_ts or time.time()
        due: list[dict[str, Any]] = []
        for item in self._read():
            if not item.get("active", True):
                continue
            if item.get("schedule_type") != "daily":
                continue

            tz = ZoneInfo(item.get("timezone", "Asia/Shanghai"))
            local_now = _to_local(now_ts, tz)
            target_hour, target_minute = _parse_time_of_day(item.get("time_of_day", "00:00"))
            if (local_now.hour, local_now.minute) < (target_hour, target_minute):
                continue

            local_date = local_now.date().isoformat()
            if item.get("last_run_local_date") == local_date:
                continue
            due.append(item)
        return due

    def _read(self) -> list[dict[str, Any]]:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []

    def _write(self, data: list[dict[str, Any]]) -> None:
        write_text_file(self.path, json.dumps(data, ensure_ascii=False, indent=2))


def _parse_time_of_day(value: str) -> tuple[int, int]:
    parts = value.split(":", 1)
    if len(parts) != 2:
        raise ValueError("time_of_day must use HH:MM format.")
    hour = int(parts[0])
    minute = int(parts[1])
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("time_of_day is out of range.")
    return hour, minute


def _validate_time_of_day(value: str) -> None:
    _parse_time_of_day(value)


def _to_local(timestamp: float, timezone: ZoneInfo):
    from datetime import datetime

    return datetime.fromtimestamp(timestamp, timezone)

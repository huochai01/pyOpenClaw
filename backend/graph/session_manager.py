from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from utils.text_files import write_text_file


class SessionManager:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.sessions_dir = base_dir / "sessions"
        self.archive_dir = self.sessions_dir / "archive"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, title: str = "新对话") -> dict[str, Any]:
        session_id = uuid.uuid4().hex
        now = time.time()
        payload = {
            "id": session_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "compressed_context": "",
            "messages": [],
        }
        self._write_session(session_id, payload)
        return payload

    def list_sessions(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for path in self.sessions_dir.glob("*.json"):
            session = self._read_session_file(path)
            items.append(
                {
                    "id": path.stem,
                    "title": session.get("title", "新对话"),
                    "created_at": session.get("created_at"),
                    "updated_at": session.get("updated_at"),
                    "message_count": len(session.get("messages", [])),
                }
            )
        items.sort(key=lambda item: item.get("updated_at") or 0, reverse=True)
        return items

    def delete_session(self, session_id: str) -> None:
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()

    def rename_session(self, session_id: str, title: str) -> dict[str, Any]:
        session = self._read_session(session_id)
        session["title"] = title
        session["updated_at"] = time.time()
        self._write_session(session_id, session)
        return session

    def load_session(self, session_id: str) -> list[dict[str, Any]]:
        return self._read_session(session_id).get("messages", [])

    def load_session_file(self, session_id: str) -> dict[str, Any]:
        return self._read_session(session_id)

    def load_session_for_agent(self, session_id: str) -> list[dict[str, Any]]:
        session = self._read_session(session_id)
        messages = session.get("messages", [])
        merged: list[dict[str, Any]] = []
        for message in messages:
            if merged and merged[-1]["role"] == "assistant" and message.get("role") == "assistant":
                merged[-1]["content"] = "\n\n".join(
                    part for part in [merged[-1].get("content", ""), message.get("content", "")] if part
                )
                merged[-1].setdefault("tool_calls", []).extend(message.get("tool_calls", []))
            else:
                merged.append(
                    {
                        "role": message.get("role"),
                        "content": message.get("content", ""),
                        "tool_calls": list(message.get("tool_calls", [])),
                    }
                )

        compressed_context = session.get("compressed_context", "")
        if compressed_context:
            merged.insert(
                0,
                {
                    "role": "assistant",
                    "content": f"[以下是之前对话的摘要]\n{compressed_context}",
                    "tool_calls": [],
                },
            )
        return merged

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        session = self._read_session(session_id)
        session.setdefault("messages", []).append(
            {"role": role, "content": content, "tool_calls": tool_calls or []}
        )
        session["updated_at"] = time.time()
        self._write_session(session_id, session)
        return session

    def compress_history(self, session_id: str, summary: str, count: int) -> dict[str, Any]:
        session = self._read_session(session_id)
        messages = session.get("messages", [])
        archived = messages[:count]
        remaining = messages[count:]
        archive_path = self.archive_dir / f"{session_id}_{int(time.time())}.json"
        write_text_file(archive_path, json.dumps(archived, ensure_ascii=False, indent=2))

        previous = session.get("compressed_context", "")
        session["compressed_context"] = f"{previous}\n---\n{summary}".strip() if previous else summary
        session["messages"] = remaining
        session["updated_at"] = time.time()
        self._write_session(session_id, session)
        return {"archived_count": len(archived), "remaining_count": len(remaining)}

    def get_compressed_context(self, session_id: str) -> str:
        return self._read_session(session_id).get("compressed_context", "")

    def ensure_session(self, session_id: str) -> dict[str, Any]:
        path = self._session_path(session_id)
        if path.exists():
            return self._read_session(session_id)
        now = time.time()
        payload = {
            "id": session_id,
            "title": "新对话",
            "created_at": now,
            "updated_at": now,
            "compressed_context": "",
            "messages": [],
        }
        self._write_session(session_id, payload)
        return payload

    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def _read_session(self, session_id: str) -> dict[str, Any]:
        path = self._session_path(session_id)
        if not path.exists():
            return self.ensure_session(session_id)
        return self._read_session_file(path)

    def _read_session_file(self, path: Path) -> dict[str, Any]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            now = time.time()
            return {
                "id": path.stem,
                "title": "迁移会话",
                "created_at": now,
                "updated_at": now,
                "compressed_context": "",
                "messages": data,
            }
        return data

    def _write_session(self, session_id: str, payload: dict[str, Any]) -> None:
        path = self._session_path(session_id)
        payload["id"] = session_id
        write_text_file(path, json.dumps(payload, ensure_ascii=False, indent=2))

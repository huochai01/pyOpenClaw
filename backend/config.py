from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

from utils.text_files import write_text_file


@dataclass(slots=True)
class RuntimeConfig:
    rag_mode: bool = False


class ConfigStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.path = base_dir / "config.json"
        self._lock = RLock()
        self._config = RuntimeConfig()
        self.load()

    def load(self) -> RuntimeConfig:
        with self._lock:
            if not self.path.exists():
                write_text_file(
                    self.path,
                    json.dumps({"rag_mode": self._config.rag_mode}, ensure_ascii=False, indent=2),
                )
                return self._config

            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._config = RuntimeConfig(rag_mode=bool(data.get("rag_mode", False)))
            return self._config

    def save(self, config: RuntimeConfig | None = None) -> RuntimeConfig:
        with self._lock:
            if config is not None:
                self._config = config
            write_text_file(
                self.path,
                json.dumps({"rag_mode": self._config.rag_mode}, ensure_ascii=False, indent=2),
            )
            return self._config

    def get_rag_mode(self) -> bool:
        return self.load().rag_mode

    def set_rag_mode(self, enabled: bool) -> RuntimeConfig:
        return self.save(RuntimeConfig(rag_mode=enabled))

    def as_dict(self) -> dict[str, Any]:
        config = self.load()
        return {"rag_mode": config.rag_mode}

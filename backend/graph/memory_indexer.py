from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex, load_index_from_storage
    from llama_index.core.node_parser import SentenceSplitter
except Exception:  # pragma: no cover
    Document = Settings = StorageContext = VectorStoreIndex = load_index_from_storage = SentenceSplitter = None

from graph.embedding_factory import build_embedding_model
from utils.text_files import read_text_file, write_text_file


class MemoryIndexer:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.memory_path = base_dir / "memory" / "MEMORY.md"
        self.storage_dir = base_dir / "storage" / "memory_index"
        self.manifest_path = self.storage_dir / "manifest.json"
        self._index = None
        self._retriever = None

    def rebuild_index(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        if not self.memory_path.exists() or Document is None:
            return

        text = read_text_file(self.memory_path, errors="replace")
        splitter = SentenceSplitter(chunk_size=256, chunk_overlap=32) if SentenceSplitter else None
        chunks = splitter.split_text(text) if splitter else [text]
        documents = [Document(text=chunk, metadata={"source": "memory/MEMORY.md"}) for chunk in chunks if chunk.strip()]
        if not documents:
            return

        embedding_model = build_embedding_model()
        if embedding_model is not None:
            Settings.embed_model = embedding_model
        self._index = VectorStoreIndex.from_documents(documents)
        self._index.storage_context.persist(persist_dir=str(self.storage_dir))
        self._retriever = self._index.as_retriever(similarity_top_k=3)
        write_text_file(
            self.manifest_path,
            json.dumps({"hash": self._compute_hash()}, ensure_ascii=False, indent=2),
        )

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        self._maybe_rebuild()
        if self._retriever is None and self.storage_dir.exists() and StorageContext is not None:
            try:
                embedding_model = build_embedding_model()
                if embedding_model is not None:
                    Settings.embed_model = embedding_model
                storage_context = StorageContext.from_defaults(persist_dir=str(self.storage_dir))
                self._index = load_index_from_storage(storage_context)
                self._retriever = self._index.as_retriever(similarity_top_k=top_k)
            except Exception:
                return []

        if self._retriever is None:
            return []

        nodes = self._retriever.retrieve(query)
        results: list[dict[str, Any]] = []
        for node in nodes[:top_k]:
            results.append(
                {
                    "text": node.text,
                    "score": float(getattr(node, "score", 0.0) or 0.0),
                    "source": "memory/MEMORY.md",
                }
            )
        return results

    def _maybe_rebuild(self) -> None:
        current_hash = self._compute_hash()
        previous_hash = None
        if self.manifest_path.exists():
            previous_hash = json.loads(self.manifest_path.read_text(encoding="utf-8")).get("hash")
        if current_hash != previous_hash:
            self.rebuild_index()

    def _compute_hash(self) -> str:
        if not self.memory_path.exists():
            return ""
        return hashlib.md5(self.memory_path.read_bytes()).hexdigest()

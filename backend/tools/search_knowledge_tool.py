from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, Field, PrivateAttr

from langchain_core.tools import BaseTool
from rank_bm25 import BM25Okapi

try:
    from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex, load_index_from_storage
    from llama_index.core.node_parser import SentenceSplitter
except Exception:  # pragma: no cover
    Document = Settings = StorageContext = VectorStoreIndex = load_index_from_storage = SentenceSplitter = None

from graph.embedding_factory import build_embedding_model
from utils.text_files import read_text_file, write_text_file


@dataclass(slots=True)
class KnowledgeChunk:
    id: str
    text: str
    source: str
    tokens: list[str]


class SearchKnowledgeInput(BaseModel):
    query: str = Field(..., description="需要检索的问题")


class SearchKnowledgeBaseTool(BaseTool):
    name: str = "search_knowledge_base"
    description: str = "对 knowledge 目录执行混合检索，综合关键词 BM25 和向量搜索。"
    args_schema: ClassVar[type[BaseModel]] = SearchKnowledgeInput
    root_dir: Path
    knowledge_dir: Path
    storage_dir: Path
    manifest_path: Path
    _chunks: list[KnowledgeChunk] = PrivateAttr(default_factory=list)
    _bm25: BM25Okapi | None = PrivateAttr(default=None)
    _vector_index: Any = PrivateAttr(default=None)
    _vector_retriever: Any = PrivateAttr(default=None)

    def __init__(self, root_dir: Path, **kwargs) -> None:
        root = root_dir.resolve()
        super().__init__(
            root_dir=root,
            knowledge_dir=root / "knowledge",
            storage_dir=root / "storage" / "knowledge_index",
            manifest_path=root / "storage" / "knowledge_index" / "manifest.json",
            **kwargs,
        )

    def _run(self, query: str) -> str:
        results = self.search(query)
        return json.dumps(results, ensure_ascii=False, indent=2)

    async def _arun(self, query: str) -> str:
        return self._run(query)

    def rebuild_index(self) -> None:
        self._rebuild()

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        self._maybe_rebuild()
        if not self._chunks:
            return []

        bm25_scores = self._bm25.get_scores(_tokenize(query)) if self._bm25 else [0.0] * len(self._chunks)
        vector_scores = self._search_vector(query, top_k=max(top_k * 2, 6))
        vector_map = {item["id"]: item["score"] for item in vector_scores}
        merged: list[dict[str, Any]] = []
        for index, chunk in enumerate(self._chunks):
            bm25 = float(bm25_scores[index]) if bm25_scores is not None else 0.0
            vector = float(vector_map.get(chunk.id, 0.0))
            score = _normalize_bm25(bm25) * 0.45 + vector * 0.55
            if score <= 0:
                continue
            merged.append(
                {
                    "id": chunk.id,
                    "text": chunk.text,
                    "source": chunk.source,
                    "score": round(score, 4),
                }
            )
        merged.sort(key=lambda item: item["score"], reverse=True)
        return merged[:top_k]

    def _maybe_rebuild(self) -> None:
        current_hash = self._compute_hash()
        previous_hash = None
        if self.manifest_path.exists():
            previous_hash = json.loads(self.manifest_path.read_text(encoding="utf-8")).get("hash")
        needs_bootstrap = not self._chunks or self._bm25 is None
        if current_hash != previous_hash or needs_bootstrap:
            self._rebuild()

    def _rebuild(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64) if SentenceSplitter else None
        chunks: list[KnowledgeChunk] = []
        documents = []
        for file_path in sorted(self.knowledge_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in {".md", ".txt", ".json"}:
                continue
            text = read_text_file(file_path, errors="replace")
            pieces = splitter.split_text(text) if splitter else [text]
            for offset, piece in enumerate(pieces):
                chunk_id = f"{file_path.relative_to(self.root_dir).as_posix()}::{offset}"
                chunks.append(
                    KnowledgeChunk(
                        id=chunk_id,
                        text=piece,
                        source=file_path.relative_to(self.root_dir).as_posix(),
                        tokens=_tokenize(piece),
                    )
                )
                if Document is not None:
                    documents.append(Document(text=piece, metadata={"source": file_path.name, "chunk_id": chunk_id}))

        self._chunks = chunks
        self._bm25 = BM25Okapi([chunk.tokens for chunk in chunks]) if chunks else None

        if Document is not None and documents:
            embedding_model = build_embedding_model()
            if embedding_model is not None:
                Settings.embed_model = embedding_model
            self._vector_index = VectorStoreIndex.from_documents(documents)
            self._vector_index.storage_context.persist(persist_dir=str(self.storage_dir))
            self._vector_retriever = self._vector_index.as_retriever(similarity_top_k=8)

        write_text_file(
            self.manifest_path,
            json.dumps({"hash": self._compute_hash()}, ensure_ascii=False, indent=2),
        )

    def _search_vector(self, query: str, top_k: int) -> list[dict[str, Any]]:
        if self._vector_retriever is None and self.storage_dir.exists() and StorageContext is not None:
            try:
                embedding_model = build_embedding_model()
                if embedding_model is not None:
                    Settings.embed_model = embedding_model
                storage_context = StorageContext.from_defaults(persist_dir=str(self.storage_dir))
                self._vector_index = load_index_from_storage(storage_context)
                self._vector_retriever = self._vector_index.as_retriever(similarity_top_k=8)
            except Exception:
                self._vector_retriever = None

        if self._vector_retriever is None:
            return []

        nodes = self._vector_retriever.retrieve(query)
        results: list[dict[str, Any]] = []
        for node in nodes[:top_k]:
            metadata = getattr(node, "metadata", {}) or {}
            chunk_id = metadata.get("chunk_id")
            score = getattr(node, "score", None)
            if chunk_id is None:
                continue
            results.append({"id": chunk_id, "score": _normalize_vector_score(float(score or 0.0))})
        return results

    def _compute_hash(self) -> str:
        digest = hashlib.md5()
        for file_path in sorted(self.knowledge_dir.rglob("*")):
            if file_path.is_file():
                digest.update(file_path.relative_to(self.root_dir).as_posix().encode("utf-8"))
                digest.update(file_path.read_bytes())
        return digest.hexdigest()


def _tokenize(text: str) -> list[str]:
    return [token for token in text.lower().replace("\n", " ").split() if token]


def _normalize_bm25(score: float) -> float:
    return 0.0 if score <= 0 else min(1.0, math.log1p(score) / 3)


def _normalize_vector_score(score: float) -> float:
    if score <= 0:
        return 0.0
    return max(0.0, min(1.0, score))

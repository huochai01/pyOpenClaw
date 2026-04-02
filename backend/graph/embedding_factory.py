from __future__ import annotations

import os
from typing import Any

try:
    from llama_index.embeddings.openai import OpenAIEmbedding
except Exception:  # pragma: no cover
    OpenAIEmbedding = None


def build_embedding_model() -> Any:
    if OpenAIEmbedding is None:
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    kwargs: dict[str, Any] = {"model": model}
    if api_key:
        kwargs["api_key"] = api_key
    if api_base:
        kwargs["api_base"] = api_base

    return OpenAIEmbedding(**kwargs)

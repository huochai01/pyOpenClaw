from __future__ import annotations

from pathlib import Path


COMMON_ENCODINGS = ("utf-8", "utf-8-sig", "gb18030", "gbk", "utf-16")


def read_text_file(path: Path, *, errors: str = "strict") -> str:
    data = path.read_bytes()
    last_error: Exception | None = None

    for encoding in COMMON_ENCODINGS:
        try:
            return data.decode(encoding, errors=errors)
        except UnicodeDecodeError as exc:
            last_error = exc

    if errors != "strict":
        return data.decode("utf-8", errors=errors)

    if last_error is not None:
        raise last_error
    return data.decode("utf-8", errors=errors)


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

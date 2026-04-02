from __future__ import annotations

from pathlib import Path

from utils.text_files import read_text_file


MAX_COMPONENT_CHARS = 20_000


def build_system_prompt(base_dir: Path, rag_mode: bool) -> str:
    components = [
        ("Skills Snapshot", base_dir / "SKILLS_SNAPSHOT.md"),
        ("Soul", base_dir / "workspace" / "SOUL.md"),
        ("Identity", base_dir / "workspace" / "IDENTITY.md"),
        ("User Profile", base_dir / "workspace" / "USER.md"),
        ("Agents Guide", base_dir / "workspace" / "AGENTS.md"),
    ]

    if rag_mode:
        memory_text = (
            "<!-- Long-term Memory -->\n"
            "长期记忆不会直接内联在系统提示词中。\n"
            "如当前会话启用了 RAG，相关记忆会在提问前通过检索结果动态注入。"
        )
    else:
        components.append(("Long-term Memory", base_dir / "memory" / "MEMORY.md"))
        memory_text = None

    rendered: list[str] = []
    for label, path in components:
        rendered.append(f"<!-- {label} -->\n{_read_limited(path)}")

    if memory_text is not None:
        rendered.append(memory_text)

    return "\n\n".join(rendered)


def _read_limited(path: Path) -> str:
    text = read_text_file(path, errors="replace") if path.exists() else ""
    if len(text) > MAX_COMPONENT_CHARS:
        return text[:MAX_COMPONENT_CHARS] + "\n...[truncated]"
    return text

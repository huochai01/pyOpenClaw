from __future__ import annotations

from pathlib import Path
from utils.text_files import write_text_file

import yaml


def scan_skills(base_dir: Path, disabled_skills: set[str] | None = None) -> Path:
    skills_dir = base_dir / "skills"
    snapshot_path = base_dir / "SKILLS_SNAPSHOT.md"
    entries: list[str] = ["<available_skills>"]
    disabled = disabled_skills or set()

    for skill_file in sorted(skills_dir.glob("*/SKILL.md")):
        raw_text = skill_file.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(raw_text)
        canonical_name = skill_file.parent.name
        if canonical_name in disabled:
            continue
        description = frontmatter.get("description") or "No description"
        location = f"./{skill_file.relative_to(base_dir).as_posix()}"
        entries.extend(
            [
                "  <skill>",
                f"    <name>{canonical_name}</name>",
                f"    <description>{description}</description>",
                f"    <location>{location}</location>",
                "  </skill>",
            ]
        )

    entries.append("</available_skills>")
    write_text_file(snapshot_path, "\n".join(entries) + "\n")
    return snapshot_path


def _parse_frontmatter(content: str) -> dict[str, str]:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    data = yaml.safe_load(parts[1]) or {}
    return {str(key): str(value) for key, value in data.items()}

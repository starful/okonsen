#!/usr/bin/env python3
"""Normalize malformed markdown frontmatter across app/content."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "app" / "content"
GUIDES = CONTENT / "guides"


def normalize_markdown_source(raw_text: str) -> str:
    text = raw_text.lstrip("\ufeff")
    text = re.sub(r"^```markdown\s*\n", "", text, count=1, flags=re.IGNORECASE)
    text = re.sub(r"\n```\s*$", "", text)
    text = re.sub(r"^\s*yaml\s*\n(?=---\s*\n)", "", text, count=1, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(
        r"^---\s*\n\{\}\s*\n---\s*\n(?=---\s*\n)",
        "",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    return text


def main():
    changed = 0
    for base in (CONTENT, GUIDES):
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            original = path.read_text(encoding="utf-8")
            cleaned = normalize_markdown_source(original)
            if cleaned != original:
                path.write_text(cleaned, encoding="utf-8")
                changed += 1
                print(f"fixed: {path.relative_to(ROOT)}")
    print(f"done. changed={changed}")


if __name__ == "__main__":
    main()

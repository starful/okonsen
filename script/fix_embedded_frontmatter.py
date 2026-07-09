#!/usr/bin/env python3
"""Strip duplicate YAML blocks accidentally embedded in markdown body."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import frontmatter
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))
from rewrite_ai_onsen import dump_meta, strip_leading_yaml_in_body  # noqa: E402

CONTENT = ROOT / "app" / "content"


def needs_fix(body: str) -> bool:
    body = body.strip()
    return body.startswith("lang:") or (
        body.startswith("---") and re.search(r"^lang:\s", body, re.M) is not None
    )


def fix_file(path: Path) -> bool:
    raw = path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw)
    if not needs_fix(post.content):
        return False
    body = strip_leading_yaml_in_body(post.content)
    text = f"---\n{dump_meta(dict(post.metadata))}\n---\n\n{body.strip()}\n"
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    fixed = 0
    for path in sorted(CONTENT.rglob("*.md")):
        if fix_file(path):
            fixed += 1
            print(f"fixed {path.relative_to(ROOT)}")
    print(f"Done: {fixed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

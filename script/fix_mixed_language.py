#!/usr/bin/env python3
"""Strip Korean from EN pages and English from KO pages (OKOnsen)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "app" / "content"
GUIDES = CONTENT / "guides"

RAMEN_EN_HEADERS = (
    (re.compile(r"^## Overview / 요약\s*$", re.M), "## Overview"),
    (re.compile(r"^## What to order / 주문\s*$", re.M), "## What to order"),
    (re.compile(r"^## Queue & ordering / 웨이팅·주문\s*$", re.M), "## Queue & ordering"),
    (re.compile(r"^## Area & nearby / 동선\s*$", re.M), "## Area & nearby"),
    (re.compile(r"^## Introduction / 소개\s*$", re.M), "## Introduction"),
    (re.compile(r"^## History & tradition / 역사와 전통\s*$", re.M), "## History & tradition"),
    (re.compile(r"^## Baths & water / 온천과 수질\s*$", re.M), "## Baths & water"),
    (re.compile(r"^## Rooms & architecture / 객실과 건축\s*$", re.M), "## Rooms & architecture"),
    (re.compile(r"^## Dining / 식사.*\s*$", re.M), "## Dining"),
    (re.compile(r"^## Local area / 주변 관광\s*$", re.M), "## Local area"),
    (re.compile(r"^## Practical tips / 실용 정보\s*$", re.M), "## Practical tips"),
    (re.compile(r"^## Access / 오시는 길\s*$", re.M), "## Access"),
)

KO_IN_EN = re.compile(
    r"\s*\(Korean:.*?\[다른 가이드\]\(/guides?\)\)",
    re.I | re.S,
)
EN_IN_KO = re.compile(
    r"\s*\(English:.*?\[More guides\]\(/guides?\)\)",
    re.I | re.S,
)

EN_FOOTER_GUIDE = "\n\n[Find onsen on the OKOnsen map](/) · [More guides](/guides)"
KO_FOOTER_GUIDE = "\n\n[OKOnsen 지도에서 온천 찾기](/) · [다른 가이드](/guides)"


def fix_en_text(text: str, *, is_guide: bool) -> str:
    for pat, repl in RAMEN_EN_HEADERS:
        text = pat.sub(repl, text)
    text = KO_IN_EN.sub("", text)
    if is_guide:
        text = re.sub(
            r"\[Find onsen on the OKOnsen map\]\(/\)\s*·\s*\[More guides\]\(/guides\)\s*",
            "",
            text,
        )
        if EN_FOOTER_GUIDE.strip() not in text:
            text = text.rstrip() + EN_FOOTER_GUIDE + "\n"
    return text


def fix_ko_text(text: str, *, is_guide: bool) -> str:
    text = EN_IN_KO.sub("", text)
    if is_guide:
        text = re.sub(
            r"\[OKOnsen 지도에서 온천 찾기\]\(/\)\s*·\s*\[다른 가이드\]\(/guides\)\s*",
            "",
            text,
        )
        if KO_FOOTER_GUIDE.strip() not in text:
            text = text.rstrip() + KO_FOOTER_GUIDE + "\n"
    return text


def main() -> int:
    changed = 0
    for path in list(CONTENT.glob("*_en.md")) + list(GUIDES.glob("*_en.md")):
        raw = path.read_text(encoding="utf-8")
        fixed = fix_en_text(raw, is_guide="guides" in path.parts)
        if fixed != raw:
            path.write_text(fixed, encoding="utf-8")
            changed += 1
    for path in list(CONTENT.glob("*_ko.md")) + list(GUIDES.glob("*_ko.md")):
        raw = path.read_text(encoding="utf-8")
        fixed = fix_ko_text(raw, is_guide="guides" in path.parts)
        if fixed != raw:
            path.write_text(fixed, encoding="utf-8")
            changed += 1
    print(f"✅ Fixed {changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

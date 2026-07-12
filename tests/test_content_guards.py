"""Tests for generation quality / duplicate-topic guards."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

from content_guards import (  # noqa: E402
    duplicate_guide_reason,
    validate_generated_markdown,
)


GOOD_EN_BODY = (
    "## Introduction\n"
    + ("This onsen ryokan offers a deep sense of place. " * 80)
    + "\n## History\n"
    + ("The property has stood for generations near the spring. " * 80)
    + "\n## Baths\n"
    + ("Mineral water and outdoor baths define the stay. " * 80)
    + "\n## Access\n"
    + ("Trains and buses connect the town to major cities. " * 40)
)

GOOD_KO_BODY = (
    "## 소개\n"
    + ("이 온천 료칸은 깊은 장소감을 선사합니다. " * 80)
    + "\n## 역사\n"
    + ("대대로 이어진 온천과 전통이 살아 있습니다. " * 80)
    + "\n## 온천\n"
    + ("노천탕과 수질이 여행의 핵심입니다. " * 80)
    + "\n## 오시는 길\n"
    + ("기차와 버스로 쉽게 접근할 수 있습니다. " * 40)
)


def _wrap(lang: str, body: str, *, onsen: bool = False) -> str:
    extra = ""
    if onsen:
        extra = (
            'lat: "35.0"\n'
            'lng: "139.0"\n'
            'address: "Hakone"\n'
            'categories: ["Luxury"]\n'
            'thumbnail: "https://example.com/x.jpg"\n'
        )
    return (
        f"---\nlang: {lang}\ntitle: \"Sample\"\nsummary: \"A summary\"\n"
        f'date: "2026-07-12"\n{extra}---\n{body}\n'
    )


def test_duplicate_guide_alias_blocked(tmp_path: Path):
    (tmp_path / "beppu_hell_tour_guide_en.md").write_text("x", encoding="utf-8")
    reason = duplicate_guide_reason("beppu_eight_hells_tour", tmp_path)
    assert reason and reason.startswith("duplicate_of:")


def test_duplicate_guide_alias_blocked_without_canonical(tmp_path: Path):
    reason = duplicate_guide_reason("beppu_eight_hells_tour", tmp_path)
    assert reason and reason.startswith("alias_blocked:")


def test_canonical_guide_allowed(tmp_path: Path):
    assert duplicate_guide_reason("beppu_hell_tour_guide", tmp_path) is None


def test_quality_accepts_good_onsen_en():
    ok, errors = validate_generated_markdown(
        _wrap("en", GOOD_EN_BODY, onsen=True),
        kind="onsen",
        lang="en",
    )
    assert ok, errors


def test_quality_rejects_short_body():
    raw = _wrap("en", "## Intro\nToo short.\n## More\nStill short.\n## End\nNope.\n", onsen=True)
    ok, errors = validate_generated_markdown(raw, kind="onsen", lang="en")
    assert not ok
    assert any(e.startswith("too_short:") for e in errors)


def test_quality_rejects_en_with_too_much_hangul():
    raw = _wrap("en", GOOD_KO_BODY, onsen=True)
    ok, errors = validate_generated_markdown(raw, kind="onsen", lang="en")
    assert not ok
    assert any(e.startswith("en_too_much_hangul:") for e in errors)


def test_sibling_fill_requires_higher_min():
    # ~4800 chars: passes new-page bar (4500), fails sibling-fill bar (5500).
    chunk = "Decent English travel copy for testing length gates. "
    body = (
        "## Introduction\n"
        + chunk * 30
        + "\n## History\n"
        + chunk * 30
        + "\n## Baths\n"
        + chunk * 30
    )
    assert 4500 <= len(body) < 5500
    raw = _wrap("en", body, onsen=True)
    ok_new, err_new = validate_generated_markdown(
        raw, kind="onsen", lang="en", sibling_exists=False
    )
    ok_fill, errors = validate_generated_markdown(
        raw, kind="onsen", lang="en", sibling_exists=True
    )
    assert ok_new, err_new
    assert not ok_fill
    assert any(e.startswith("too_short:") for e in errors)

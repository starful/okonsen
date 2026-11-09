"""Tests for the index status batch audit (thin/duplicate/missing-sitemap flags)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "script"))

from seo import flag_unindexable_reason  # noqa: E402
from index_status_report import BASE_URL, classify  # noqa: E402


def test_flag_unindexable_reason_thin():
    seen: set[str] = set()
    item = {"body_chars": 100, "body_hash": "h1"}
    assert flag_unindexable_reason(item, kind="onsen", seen_hashes=seen) == "thin"


def test_flag_unindexable_reason_duplicate():
    seen = {"h1"}
    item = {"body_chars": 5000, "body_hash": "h1"}
    assert flag_unindexable_reason(item, kind="onsen", seen_hashes=seen) == "duplicate"


def test_flag_unindexable_reason_ok():
    seen: set[str] = set()
    item = {"body_chars": 5000, "body_hash": "h2"}
    assert flag_unindexable_reason(item, kind="onsen", seen_hashes=seen) is None


def test_classify_flags_thin_duplicate_missing_and_ok():
    items = [
        {"id": "a", "link": "/onsen/a_en", "body_chars": 5000, "body_hash": "h1"},
        {"id": "b", "link": "/onsen/b_en", "body_chars": 5000, "body_hash": "h1"},  # dup of a
        {"id": "c", "link": "/onsen/c_en", "body_chars": 100, "body_hash": "h2"},  # thin
        {"id": "d", "link": "/onsen/d_en", "body_chars": 5000, "body_hash": "h3"},  # not in sitemap
        {"id": "e", "link": "/onsen/e_en", "body_chars": 5000, "body_hash": "h4"},
    ]
    sitemap = {f"{BASE_URL}/onsen/a_en", f"{BASE_URL}/onsen/e_en"}

    rows = classify(items, kind="onsen", sitemap=sitemap)
    reasons = {r["id"]: r["reason"] for r in rows}
    assert reasons == {
        "a": "ok",
        "b": "duplicate",
        "c": "thin",
        "d": "missing_sitemap",
        "e": "ok",
    }

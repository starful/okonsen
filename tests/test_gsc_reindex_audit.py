"""Tests for the GSC not-indexed CSV diff / reindex queue builder."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

from gsc_reindex_audit import BASE_URL, build_queue, load_gsc_not_indexed  # noqa: E402


def test_load_gsc_not_indexed_with_header(tmp_path):
    csv_path = tmp_path / "export.csv"
    csv_path.write_text(
        "URL,Last crawled\n"
        f"{BASE_URL}/onsen/foo_en,2026-10-01\n"
        f"{BASE_URL}/guide/bar_ko,2026-10-02\n"
        "https://example.com/not-ours,2026-10-02\n",
        encoding="utf-8",
    )
    urls = load_gsc_not_indexed(csv_path)
    assert urls == {f"{BASE_URL}/onsen/foo_en", f"{BASE_URL}/guide/bar_ko"}


def test_load_gsc_not_indexed_finds_url_column_anywhere(tmp_path):
    csv_path = tmp_path / "export.csv"
    csv_path.write_text(
        "Last crawled,URL\n"
        f"2026-10-01,{BASE_URL}/onsen/foo_en\n",
        encoding="utf-8",
    )
    urls = load_gsc_not_indexed(csv_path)
    assert urls == {f"{BASE_URL}/onsen/foo_en"}


def test_load_gsc_not_indexed_without_header(tmp_path):
    csv_path = tmp_path / "export.csv"
    csv_path.write_text(f"{BASE_URL}/onsen/foo_en\n{BASE_URL}/onsen/baz_ko\n", encoding="utf-8")
    urls = load_gsc_not_indexed(csv_path)
    assert urls == {f"{BASE_URL}/onsen/foo_en", f"{BASE_URL}/onsen/baz_ko"}


def test_build_queue_excludes_thin_and_ranks_priority():
    not_indexed = {
        f"{BASE_URL}/onsen/kusatsu_onsen_ryokan_yoshinoya_en",  # priority
        f"{BASE_URL}/onsen/random_other_en",  # not priority, still actionable
        f"{BASE_URL}/onsen/thin_page_en",  # flagged thin
        f"{BASE_URL}/onsen/not_in_sitemap_en",  # not advertised anymore
    }
    sitemap = {
        f"{BASE_URL}/onsen/kusatsu_onsen_ryokan_yoshinoya_en",
        f"{BASE_URL}/onsen/random_other_en",
        f"{BASE_URL}/onsen/thin_page_en",
    }
    thin_links = {"/onsen/thin_page_en"}

    queue = build_queue(not_indexed, sitemap, thin_links, limit=0)
    assert queue == [
        f"{BASE_URL}/onsen/kusatsu_onsen_ryokan_yoshinoya_en",
        f"{BASE_URL}/onsen/random_other_en",
    ]


def test_build_queue_respects_limit():
    not_indexed = {f"{BASE_URL}/onsen/a_en", f"{BASE_URL}/onsen/b_en"}
    sitemap = set(not_indexed)
    queue = build_queue(not_indexed, sitemap, thin_links=set(), limit=1)
    assert len(queue) == 1

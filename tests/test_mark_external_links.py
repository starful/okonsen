"""Tests for markdown external-link marking."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from content_loader import mark_external_links  # noqa: E402


def test_marks_external_and_keeps_internal():
    html = (
        '<p><a href="/onsen/hakone_gora_kadan_ko">내부</a> and '
        '<a href="https://okramen.net/guide/tokyo_ramen_day_course_ko">라멘</a></p>'
    )
    out = mark_external_links(html, lang="ko")
    assert 'class="md-link--internal"' in out or "md-link--internal" in out
    assert "md-link--external" in out
    assert 'target="_blank"' in out
    assert "noopener" in out
    assert "↗외부" in out
    assert "/onsen/hakone_gora_kadan_ko" in out
    # Internal must not open new tab
    assert out.index("md-link--internal") < out.index("md-link--external")


def test_same_host_absolute_is_internal():
    html = '<a href="https://okonsen.net/guide/hakone_day_trip_guide_ko">당일</a>'
    out = mark_external_links(html, lang="ko", site_url="https://okonsen.net")
    assert "md-link--internal" in out
    assert "md-link--external" not in out
    assert "target" not in out.lower() or 'target="_blank"' not in out


def test_english_badge():
    html = '<a href="https://okcaddie.net/course/x">Golf</a>'
    out = mark_external_links(html, lang="en")
    assert "↗ext" in out
    assert "Opens in a new tab" in out

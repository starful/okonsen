"""Rakuten Travel affiliate slug → region mapping."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from rakuten_affiliate import (  # noqa: E402
    DEFAULT_REGION,
    resolve_region_from_slug,
    rakuten_context,
)


def test_slug_region_kusatsu():
    assert resolve_region_from_slug("kusatsu_onsen_tokinoniwa_en") == "kusatsu"


def test_slug_region_hakone_embedded():
    assert resolve_region_from_slug("hotel_indigo_hakone_gora_en") == "hakone"


def test_slug_alias_matsuzakaya():
    assert resolve_region_from_slug("matsuzakaya_honten_en") == "kinosaki"


def test_slug_alias_yubatake():
    assert resolve_region_from_slug("yubatake_souan_en") == "kusatsu"


def test_guide_slug_beppu():
    assert resolve_region_from_slug("beppu_hell_tour_guide_ko") == "beppu"


def test_unknown_slug_defaults_kusatsu():
    assert resolve_region_from_slug("tattoo_friendly_master_list_en") == DEFAULT_REGION


def test_rakuten_context_has_travel_hgc():
    ctx = rakuten_context("kurokawa_onsen_nanjoen_en", lang="en")
    assert "hb.afl.rakuten.co.jp/hgc/" in ctx["rakuten_search_url"]
    assert "kw.travel.rakuten.co.jp" in ctx["rakuten_search_url"]
    assert ctx["rakuten_region"] == "kurokawa"
    assert "Kurokawa" in ctx["rakuten_button_label"]
    assert "new tab" in ctx["booking_desc"].lower() or "external" in ctx["booking_desc"].lower()


def test_rakuten_context_korean_labels():
    ctx = rakuten_context("hakone_pax_yoshino_ko", lang="ko")
    assert ctx["region_label"] == "하코네"
    assert "하코네" in ctx["rakuten_button_label"]
    assert "새 탭" in ctx["booking_desc"]

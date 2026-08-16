"""Rakuten Travel affiliate slug → region mapping."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from rakuten_affiliate import (  # noqa: E402
    DEFAULT_REGION,
    resolve_region_from_slug,
    resolve_klook_intent,
    klook_url_for,
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
    assert ctx["show_klook"] is False
    assert not ctx["klook_url"]
    assert "Klook" not in ctx["booking_desc"]


def test_rakuten_context_korean_labels():
    ctx = rakuten_context("hakone_pax_yoshino_ko", lang="ko")
    assert ctx["region_label"] == "하코네"
    assert "하코네" in ctx["rakuten_button_label"]
    assert "쿠팡" in ctx["booking_desc"] or "라쿠텐" in ctx["booking_desc"]
    assert ctx["show_coupang"] is True
    assert ctx["show_klook"] is False
    assert not ctx["klook_url"]


def test_klook_helpers_still_resolve_urls():
    """Legacy Klook URL map kept for bookmarks; not shown in UI."""
    assert resolve_klook_intent("hakone_day_trip_guide_ko") == "hakone_daypass"
    assert "3Jx17AsJ" in klook_url_for("hakone_day_trip_guide_ko", lang="ko")
    assert "2KjDnw12" in klook_url_for("hakone_day_trip_guide_en", lang="en")
    assert resolve_klook_intent("hakone_weekend_guide_ko") == "hakone_tours"
    assert "AenqagWg" in klook_url_for("hakone_weekend_guide_ko", lang="ko")
    assert resolve_klook_intent("kusatsu_onsen_tokinoniwa_en") == "kusatsu"
    assert "mK6ms91p" in klook_url_for("kusatsu_onsen_tokinoniwa_en", lang="en")
    assert "NlkzKCnF" in klook_url_for("kusatsu_onsen_tokinoniwa_ko", lang="ko")

def test_travel_daybath_vs_stay():
    from urllib.parse import unquote

    from rakuten_affiliate import resolve_travel_intent, rakuten_url_for

    assert resolve_travel_intent("hakone_day_trip_guide_ko") == "daybath"
    assert resolve_travel_intent("hakone_pax_yoshino_ko") == "stay"
    day = unquote(unquote(rakuten_url_for("hakone_day_trip_guide_ko")))
    stay = unquote(unquote(rakuten_url_for("hakone_pax_yoshino_ko")))
    assert "日帰り入浴" in day
    assert "旅館" in stay
    ctx = rakuten_context("hakone_day_trip_guide_ko", lang="ko")
    assert ctx["travel_intent"] == "daybath"
    assert "당일" in ctx["rakuten_button_label"]


def test_coupang_ko_only_and_hakone_intent():
    from rakuten_affiliate import coupang_url_for, resolve_coupang_intent

    assert resolve_coupang_intent("hakone_day_trip_guide_ko") == "hakone"
    assert "f28SBETBgi" in coupang_url_for("hakone_day_trip_guide_ko")
    assert resolve_coupang_intent("kusatsu_onsen_tokinoniwa_ko") == "japan"
    ctx_ko = rakuten_context("hakone_pax_yoshino_ko", lang="ko")
    assert ctx_ko["show_coupang"] is True
    assert "f28SBETBgi" in ctx_ko["coupang_url"]
    assert "쿠팡 파트너스" in ctx_ko["coupang_disclosure"]
    ctx_en = rakuten_context("hakone_pax_yoshino_en", lang="en")
    assert ctx_en["show_coupang"] is False
    assert not ctx_en["coupang_url"]

"""Rakuten Travel affiliate slug → region mapping."""

import importlib.util
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

APP = Path(__file__).resolve().parents[1] / "app"
spec = importlib.util.spec_from_file_location("rakuten_affiliate", APP / "rakuten_affiliate.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["rakuten_affiliate"] = mod
spec.loader.exec_module(mod)
rakuten_context = mod.rakuten_context
rakuten_url_for = mod.rakuten_url_for
resolve_region_from_slug = mod.resolve_region_from_slug
resolve_travel_intent = mod.resolve_travel_intent


def _search_keyword(url: str) -> str:
    dest = unquote(parse_qs(urlparse(url).query)["pc"][0])
    return unquote(parse_qs(urlparse(dest).query).get("f_key", [""])[0])


def test_resolve_region_kurokawa():
    assert resolve_region_from_slug("kurokawa_onsen_nanjoen_en") == "kurokawa"


def test_resolve_region_matsuzakaya_alias():
    assert resolve_region_from_slug("matsuzakaya_honten_ko") == "kinosaki"


def test_day_trip_intent():
    assert resolve_travel_intent("hakone_day_trip_guide_en") == "daybath"


def test_rakuten_context_has_travel_hgc():
    ctx = rakuten_context("kurokawa_onsen_nanjoen_en", lang="en")
    assert "hb.afl.rakuten.co.jp/hgc/" in ctx["rakuten_search_url"]
    assert "kw.travel.rakuten.co.jp" in ctx["rakuten_search_url"]
    assert ctx["rakuten_region"] == "kurokawa"
    assert "Kurokawa" in ctx["rakuten_button_label"]


def test_rakuten_context_korean_labels():
    ctx = rakuten_context("hakone_pax_yoshino_ko", lang="ko")
    assert ctx["region_label"]
    assert "하코네" in ctx["rakuten_button_label"]


def test_unmapped_famous_onsens_do_not_fall_back_to_kusatsu():
    cases = {
        "nyuto_onsen_kuroyu_en": ("nyuto", "乳頭"),
        "nyuto_onsen_seclusion_en": ("nyuto", "乳頭"),
        "ginzan_onsen_showakan_ko": ("ginzan", "銀山"),
        "jozankei_onsen_hatago_sakura_ko": ("jozankei", "定山渓"),
        "jozankei_sapporo_access_en": ("jozankei", "定山渓"),
        "takaragawa_onsen_ousenkaku_en": ("takaragawa", "宝川"),
        "amane_resort_seikai_en": ("beppu", "別府"),
    }
    for slug, (region, token) in cases.items():
        assert resolve_region_from_slug(slug) == region, slug
        keyword = _search_keyword(rakuten_url_for(slug))
        assert token in keyword, (slug, keyword)
        assert "草津" not in keyword, (slug, keyword)


def test_generic_guides_still_default_to_kusatsu():
    assert resolve_region_from_slug("onsen_etiquette_guide_en") == "kusatsu"
    assert "草津" in _search_keyword(rakuten_url_for("onsen_etiquette_guide_en"))

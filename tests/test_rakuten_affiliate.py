"""Rakuten Travel affiliate slug → region mapping."""

import importlib.util
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
spec = importlib.util.spec_from_file_location("rakuten_affiliate", APP / "rakuten_affiliate.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["rakuten_affiliate"] = mod
spec.loader.exec_module(mod)
rakuten_context = mod.rakuten_context
resolve_region_from_slug = mod.resolve_region_from_slug
resolve_travel_intent = mod.resolve_travel_intent


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

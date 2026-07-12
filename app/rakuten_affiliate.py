"""Rakuten Travel affiliate links for OKOnsen (slug → region → search URL)."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote, quote_plus

# Rakuten Travel affiliate ID (override via env).
RAKUTEN_HGC = os.getenv(
    "RAKUTEN_TRAVEL_HGC", "55b9427b.a63c2df8.55b9427c.3a0d270c"
)
_RAKUTEN_UT = "eyJwYWdlIjoidXJsIiwidHlwZSI6InRleHQiLCJjb2wiOjF9"

DEFAULT_REGION = "kusatsu"

# Slug prefix or alias → region key.
REGION_PREFIXES: tuple[str, ...] = (
    "kurokawa",
    "kinosaki",
    "kusatsu",
    "yufuin",
    "hakone",
    "beppu",
    "arima",
)

SLUG_ALIASES: dict[str, str] = {
    "matsuzakaya": "kinosaki",
    "yubatake": "kusatsu",
}

# f_key search URLs (UTF-8, single-encoded query values).
_REGION_F_KEY_RAW: dict[str, str] = {
    "kusatsu": "https://kw.travel.rakuten.co.jp/keyword/Search.do?"
    + "f_key=" + quote_plus("草津温泉 宿"),
    "hakone": "https://kw.travel.rakuten.co.jp/keyword/Search.do?"
    + "f_key=" + quote_plus("箱根 温泉 旅館"),
    "kurokawa": "https://kw.travel.rakuten.co.jp/keyword/Search.do?"
    + "f_key=" + quote_plus("黒川温泉 宿"),
    "yufuin": "https://kw.travel.rakuten.co.jp/keyword/Search.do?"
    + "f_key=" + quote_plus("由布院 温泉 旅館"),
    "kinosaki": "https://kw.travel.rakuten.co.jp/keyword/Search.do?"
    + "f_key=" + quote_plus("城崎温泉 旅館"),
    "beppu": "https://kw.travel.rakuten.co.jp/keyword/Search.do?"
    + "f_key=" + quote_plus("別府 温泉 旅館"),
    "arima": "https://kw.travel.rakuten.co.jp/keyword/Search.do?"
    + "f_key=" + quote_plus("有馬温泉 旅館"),
}


def _affiliate_wrap(destination_url: str) -> str:
    pc = quote(destination_url, safe="")
    return (
        f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_HGC}/"
        f"?pc={pc}&link_type=text&ut={_RAKUTEN_UT}"
    )


REGION_URLS: dict[str, str] = {
    region: _affiliate_wrap(raw) for region, raw in _REGION_F_KEY_RAW.items()
}

REGION_LABELS: dict[str, tuple[str, str]] = {
    "kusatsu": ("Kusatsu", "쿠사츠"),
    "hakone": ("Hakone", "하코네"),
    "kurokawa": ("Kurokawa", "구로카와"),
    "yufuin": ("Yufuin", "유후인"),
    "kinosaki": ("Kinosaki", "기노사키"),
    "beppu": ("Beppu", "벳푸"),
    "arima": ("Arima", "아리마"),
}


def resolve_region_from_slug(slug: str) -> str:
    """Map onsen/guide slug to a travel search region key."""
    base = (slug or "").strip().lower()
    if base.endswith("_en") or base.endswith("_ko"):
        base = base.rsplit("_", 1)[0]

    for alias, region in SLUG_ALIASES.items():
        if base == alias or base.startswith(alias + "_"):
            return region

    parts = base.split("_")
    for region in REGION_PREFIXES:
        if region in parts:
            return region

    return DEFAULT_REGION


def rakuten_context(slug: str, *, lang: str = "en") -> dict[str, Any]:
    """Template vars for booking CTA (Klook + Rakuten Travel)."""
    region = resolve_region_from_slug(slug)
    is_ko = (lang or "en").lower() == "ko"
    label_en, label_ko = REGION_LABELS.get(
        region, REGION_LABELS[DEFAULT_REGION]
    )
    region_label = label_ko if is_ko else label_en

    if is_ko:
        booking_title = (
            f"예약은 외부 사이트에서 {region_label} 지역 숙소·투어를 검색하세요"
        )
        booking_desc = (
            "이 페이지는 소개 글입니다. 버튼을 누르면 새 탭에서 "
            "Klook 또는 라쿠텐 트래블이 열리며, 이 료칸의 직접 예약 페이지가 "
            "아닐 수 있습니다."
        )
        klook_button_label = "Klook에서 투어·패스 보기 ↗"
        rakuten_button_label = f"라쿠텐에서 {region_label} 료칸 검색 ↗"
    else:
        booking_title = (
            f"Book via external sites — search {region_label} area stays"
        )
        booking_desc = (
            "This page is a guide, not a booking form. Buttons open Klook or "
            "Rakuten Travel in a new tab to search tours and ryokan in the "
            f"{region_label} area — not always this exact property."
        )
        klook_button_label = "Tours & passes on Klook ↗"
        rakuten_button_label = f"Search {region_label} ryokan on Rakuten ↗"

    return {
        "rakuten_region": region,
        "region_label": region_label,
        "rakuten_search_url": REGION_URLS.get(
            region, REGION_URLS[DEFAULT_REGION]
        ),
        "booking_title": booking_title,
        "booking_desc": booking_desc,
        "klook_button_label": klook_button_label,
        "rakuten_button_label": rakuten_button_label,
    }

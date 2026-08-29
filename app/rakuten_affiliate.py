"""Rakuten Travel affiliate links for OKOnsen (slug → region → search URL)."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote, quote_plus

RAKUTEN_HGC = os.getenv(
    "RAKUTEN_TRAVEL_HGC", "55b9427b.a63c2df8.55b9427c.3a0d270c"
)
_RAKUTEN_UT = "eyJwYWdlIjoidXJsIiwidHlwZSI6InRleHQiLCJjb2wiOjF9"

DEFAULT_REGION = "kusatsu"

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

_REGION_STAY_KEYWORDS: dict[str, dict[str, str]] = {
    "kusatsu": {
        "stay": "草津温泉 宿",
        "daybath": "草津 日帰り入浴",
    },
    "hakone": {
        "stay": "箱根 温泉 旅館",
        "daybath": "箱根 日帰り入浴",
    },
    "kurokawa": {
        "stay": "黒川温泉 宿",
        "daybath": "黒川温泉 日帰り",
    },
    "yufuin": {
        "stay": "由布院 温泉 旅館",
        "daybath": "由布院 日帰り入浴",
    },
    "kinosaki": {
        "stay": "城崎温泉 旅館",
        "daybath": "城崎温泉 日帰り",
    },
    "beppu": {
        "stay": "別府 温泉 旅館",
        "daybath": "別府 日帰り入浴",
    },
    "arima": {
        "stay": "有馬温泉 旅館",
        "daybath": "有馬温泉 日帰り",
    },
}


def _travel_search_raw(keyword: str) -> str:
    return (
        "https://kw.travel.rakuten.co.jp/keyword/Search.do?"
        + "f_key="
        + quote_plus(keyword)
    )


def _affiliate_wrap(destination_url: str) -> str:
    pc = quote(destination_url, safe="")
    return (
        f"https://hb.afl.rakuten.co.jp/hgc/{RAKUTEN_HGC}/"
        f"?pc={pc}&link_type=text&ut={_RAKUTEN_UT}"
    )


REGION_URLS: dict[str, str] = {
    region: _affiliate_wrap(_travel_search_raw(kws["stay"]))
    for region, kws in _REGION_STAY_KEYWORDS.items()
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


def _strip_lang_suffix(slug: str) -> str:
    base = (slug or "").strip().lower()
    if base.endswith("_en") or base.endswith("_ko"):
        base = base.rsplit("_", 1)[0]
    return base


def resolve_travel_intent(slug: str) -> str:
    """day_trip guides → daybath search; otherwise lodging/ryokan search."""
    base = _strip_lang_suffix(slug)
    if (
        "day_trip" in base
        or "daytrip" in base
        or "daybath" in base
        or "day_bath" in base
        or "higaeri" in base
    ):
        return "daybath"
    return "stay"


def rakuten_url_for(slug: str) -> str:
    region = resolve_region_from_slug(slug)
    intent = resolve_travel_intent(slug)
    kws = _REGION_STAY_KEYWORDS.get(region, _REGION_STAY_KEYWORDS[DEFAULT_REGION])
    keyword = kws.get(intent) or kws["stay"]
    return _affiliate_wrap(_travel_search_raw(keyword))


def resolve_region_from_slug(slug: str) -> str:
    """Map onsen/guide slug to a travel search region key."""
    base = _strip_lang_suffix(slug)

    for alias, region in SLUG_ALIASES.items():
        if base == alias or base.startswith(alias + "_"):
            return region

    parts = base.split("_")
    for region in REGION_PREFIXES:
        if region in parts:
            return region

    return DEFAULT_REGION


def rakuten_context(slug: str, *, lang: str = "en") -> dict[str, Any]:
    """Template vars for booking CTA (Rakuten Travel)."""
    region = resolve_region_from_slug(slug)
    travel_intent = resolve_travel_intent(slug)
    is_ko = (lang or "en").lower() == "ko"
    label_en, label_ko = REGION_LABELS.get(
        region, REGION_LABELS[DEFAULT_REGION]
    )
    region_label = label_ko if is_ko else label_en

    if is_ko:
        if travel_intent == "daybath":
            booking_title = (
                f"당일 입욕은 외부 사이트에서 {region_label} 지역을 검색하세요"
            )
            booking_desc = (
                "이 페이지는 소개 글입니다. 라쿠텐에서 숙소·당일 입욕을 "
                "검색할 수 있습니다."
            )
            rakuten_button_label = f"라쿠텐에서 {region_label} 당일 입욕 검색 ↗"
        else:
            booking_title = (
                f"예약은 외부 사이트에서 {region_label} 지역 숙소·투어를 검색하세요"
            )
            booking_desc = (
                "이 페이지는 소개 글입니다. 라쿠텐 트래블로 연결되며, "
                "이 료칸의 직접 예약 페이지가 아닐 수 있습니다."
            )
            rakuten_button_label = f"라쿠텐에서 {region_label} 료칸 검색 ↗"
    elif travel_intent == "daybath":
        booking_title = (
            f"Day-trip bathing — search {region_label} on external sites"
        )
        booking_desc = (
            "This page is a guide, not a booking form. The button opens "
            "Rakuten Travel (day-bath search) in a new tab."
        )
        rakuten_button_label = (
            f"Search {region_label} day bathing on Rakuten ↗"
        )
    else:
        booking_title = (
            f"Book via external sites — search {region_label} area stays"
        )
        booking_desc = (
            "This page is a guide, not a booking form. The button opens "
            "Rakuten Travel in a new tab to search ryokan in the "
            f"{region_label} area — not always this exact property."
        )
        rakuten_button_label = f"Search {region_label} ryokan on Rakuten ↗"

    return {
        "rakuten_region": region,
        "region_label": region_label,
        "rakuten_search_url": rakuten_url_for(slug),
        "travel_intent": travel_intent,
        "booking_title": booking_title,
        "booking_desc": booking_desc,
        "rakuten_button_label": rakuten_button_label,
    }

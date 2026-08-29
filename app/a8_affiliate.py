"""A8.net affiliate banners for OK Onsen."""

from __future__ import annotations

import os
from typing import Any

_BANNERS: dict[str, dict[str, str]] = {
    "yumeyado": {
        "id": "yumeyado",
        "click_url": "https://px.a8.net/svt/ejp?a8mat=4BAH9J+4GR6QQ+44YI+HY069",
        "image_url": "https://www20.a8.net/svt/bgt?aid=260829415270&wid=007&eno=01&mid=s00000019305003014000&mc=1",
        "pixel_url": "https://www15.a8.net/0.gif?a8mat=4BAH9J+4GR6QQ+44YI+HY069",
        "label_en": "Yumeyado — weekday ryokan deals",
        "label_ko": "유메야도 — 평일 온천·숙박",
        "desc_en": "Weekday discount stays at onsen inns across Japan.",
        "desc_ko": "일본 온천·료칸 평일 특가.",
        "alt_en": "Yumeyado — affiliate",
        "alt_ko": "유메야도 — 제휴",
    },
    "agoda": {
        "id": "agoda",
        "click_url": "https://px.a8.net/svt/ejp?a8mat=4BAH9J+13ARC2+4X1W+5ZMCH",
        "image_url": "https://www26.a8.net/svt/bgt?aid=260829415066&wid=007&eno=01&mid=s00000022946001006000&mc=1",
        "pixel_url": "https://www19.a8.net/0.gif?a8mat=4BAH9J+13ARC2+4X1W+5ZMCH",
        "label_en": "Agoda — hotels near onsen",
        "label_ko": "Agoda — 온천 주변 숙소",
        "desc_en": "Search hotels and ryokan near this area.",
        "desc_ko": "이 지역 주변 숙소 검색.",
        "alt_en": "Agoda — affiliate",
        "alt_ko": "Agoda — 제휴",
    },
    "tora_esim": {
        "id": "tora_esim",
        "click_url": "https://px.a8.net/svt/ejp?a8mat=4BAH9I+GEM5IA+5NG6+5ZEMP",
        "image_url": "https://www22.a8.net/svt/bgt?aid=260829414992&wid=007&eno=01&mid=s00000026367001005000&mc=1",
        "pixel_url": "https://www16.a8.net/0.gif?a8mat=4BAH9I+GEM5IA+5NG6+5ZEMP",
        "label_en": "TORA eSIM — Japan travel",
        "label_ko": "TORA eSIM — 일본 여행",
        "desc_en": "Travel eSIM before you arrive in Japan.",
        "desc_ko": "일본 도착 전 eSIM 준비.",
        "alt_en": "TORA eSIM — affiliate",
        "alt_ko": "TORA eSIM — 제휴",
    },
}


def _enabled() -> bool:
    return os.getenv("A8_OKONSEN_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _copy(banner_id: str, *, lang: str) -> dict[str, str]:
    src = _BANNERS[banner_id]
    is_ko = (lang or "en").lower() == "ko"
    suffix = "ko" if is_ko else "en"
    key = banner_id.upper()
    return {
        "id": src["id"],
        "click_url": os.getenv(f"A8_{key}_CLICK_URL", src["click_url"]),
        "image_url": os.getenv(f"A8_{key}_BANNER_URL", src["image_url"]),
        "pixel_url": os.getenv(f"A8_{key}_PIXEL_URL", src["pixel_url"]),
        "label": src[f"label_{suffix}"],
        "desc": src[f"desc_{suffix}"],
        "alt": src[f"alt_{suffix}"],
    }


def a8_banners_context(*, lang: str = "en") -> dict[str, Any]:
    if not _enabled():
        return {"show_a8_banners": False, "a8_banners": []}
    is_ko = (lang or "en").lower() == "ko"
    banners = [_copy(k, lang=lang) for k in ("yumeyado", "agoda", "tora_esim")]
    return {
        "show_a8_banners": True,
        "a8_banners": banners,
        "a8_banners_title": (
            "숙박·여행 제휴" if is_ko else "Stay & trip partners"
        ),
        "a8_banners_note": (
            "제휴 광고 · 새 탭에서 열림"
            if is_ko
            else "Affiliate ads · opens in new tab"
        ),
    }

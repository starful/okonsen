"""Amazon JP Associates — content-kind search links (tag=starful06-22)."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote_plus

TAG = os.getenv("AMAZON_JP_TAG", "starful06-22")

# kind → Japanese search keyword (Amazon.co.jp)
_KEYWORDS: dict[str, str] = {
    "default": "温泉 グッズ",
    "onsen": "温泉 タオル アメニティ",
    "guide": "温泉 旅行 グッズ",
    "daybath": "温泉 入浴剤",
    "ryokan": "旅館 浴衣",
}


def search_url(keyword: str) -> str:
    k = (keyword or "").strip() or _KEYWORDS["default"]
    return (
        f"https://www.amazon.co.jp/s?k={quote_plus(k)}"
        f"&tag={TAG}&linkCode=ll2&ref_=as_li_ss_tl"
    )


def _enabled() -> bool:
    return os.getenv("AMAZON_OKONSEN_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def amazon_context(*, kind: str = "default", lang: str = "en") -> dict[str, Any]:
    if not _enabled():
        return {"show_amazon": False, "amazon_cta": None}
    key = (kind or "default").strip().lower() or "default"
    keyword = _KEYWORDS.get(key) or _KEYWORDS["default"]
    is_ko = (lang or "en").lower() == "ko"
    return {
        "show_amazon": True,
        "amazon_cta": {
            "id": "amazon",
            "click_url": search_url(keyword),
            "label": "Amazon — 온천 준비물" if is_ko else "Amazon — onsen essentials",
            "desc": "타월·입욕제·여행용품." if is_ko else "Towels, bath goods, travel essentials.",
            "keyword": keyword,
        },
    }

"""Agoda Partners CTA context for OK Onsen — replaces the retired A8.net banners."""

from __future__ import annotations

import os
from typing import Any

try:
    from .agoda_partners import url_for_location
except ImportError:
    from agoda_partners import url_for_location


def _enabled() -> bool:
    # Prefer AFFILIATE_*; keep A8_* as legacy alias so existing .env still works.
    raw = os.getenv("AFFILIATE_OKONSEN_ENABLED") or os.getenv("A8_OKONSEN_ENABLED", "1")
    return raw.strip().lower() in ("1", "true", "yes", "on")


def agoda_cta_context(
    *,
    lang: str = "en",
    lat: float | None = None,
    lng: float | None = None,
) -> dict[str, Any]:
    """Template vars for the Agoda "nearby stays" CTA (used in booking_box.html)."""
    if not _enabled():
        return {"show_agoda_cta": False, "agoda_cta": None}

    is_ko = (lang or "en").lower() == "ko"
    click_url = url_for_location(
        lang=lang,
        lat=lat,
        lng=lng,
        country="jp",
        default_city=5085,
    )
    agoda_cta = {
        "id": "agoda",
        "click_url": click_url,
        "label": "Agoda — 온천 주변 숙소" if is_ko else "Agoda — near this onsen",
        "desc": "이 지역 주변 숙소 검색." if is_ko else "Search hotels and ryokan near this area.",
    }
    return {"show_agoda_cta": True, "agoda_cta": agoda_cta}

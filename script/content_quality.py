"""Quality / theme gates for okonsen generation."""

from __future__ import annotations

ONSEN_THEME_MARKERS = (
    "onsen",
    "ryokan",
    "rotenburo",
    "hot spring",
    "hotspring",
    "bath",
    "kashikiri",
    "yukata",
    "温泉",
    "旅館",
    "노천",
    "온천",
    "료칸",
)

FOREIGN_THEME_MARKERS = (
    "cafe",
    "latte",
    "roast",
    "espresso",
    "kissaten",
    "dessert",
    "bakery",
    "coffee",
    "brew",
    "ramen",
    "tonkotsu",
    "menya",
    "noodle",
    "라멘",
    "golf",
    "golfer",
    "country club",
    "fairway",
    "골프",
)


def is_off_onsen_theme(
    safe_name: str,
    display_name: str = "",
    *,
    features: str = "",
    address: str = "",
) -> bool:
    """True when the row is off-theme for an onsen site (reject)."""
    blob = f"{safe_name} {display_name} {features} {address}".lower()
    if any(m in blob for m in FOREIGN_THEME_MARKERS):
        return True
    if any(m in blob for m in ONSEN_THEME_MARKERS):
        return False
    return True

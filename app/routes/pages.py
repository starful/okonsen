"""Home and guide hub pages."""

from __future__ import annotations

from flask import Blueprint, render_template, request

try:
    from ..config import GOOGLE_MAPS_API_KEY
    from ..content_loader import get_all_guides, get_priority_guides
    from ..data_cache import (
        CACHED_DATA,
        ensure_onsen_cache,
        get_featured_onsens,
        get_footer_stats,
        public_onsen,
    )
except ImportError:
    from config import GOOGLE_MAPS_API_KEY
    from content_loader import get_all_guides, get_priority_guides
    from data_cache import (
        CACHED_DATA,
        ensure_onsen_cache,
        get_featured_onsens,
        get_footer_stats,
        public_onsen,
    )

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    lang = request.args.get("lang", "en")
    priority_guides = get_priority_guides(lang, limit=3)
    top_guides = priority_guides if priority_guides else get_all_guides(lang)[:3]
    boost_guides = get_priority_guides(lang, limit=8)
    featured_onsens = get_featured_onsens(lang)
    stats = get_footer_stats(lang)
    return render_template(
        "index.html",
        lang=lang,
        guides=top_guides,
        boost_guides=boost_guides,
        featured_onsens=featured_onsens,
        google_maps_api_key=GOOGLE_MAPS_API_KEY,
        **stats,
    )


@pages_bp.route("/guides")
def guide_list():
    lang = request.args.get("lang", "en")
    all_guides = get_all_guides(lang)
    boost_guides = get_priority_guides(lang, limit=8)
    stats = get_footer_stats(lang)
    return render_template(
        "guide_list.html",
        guides=all_guides,
        boost_guides=boost_guides,
        lang=lang,
        **stats,
    )


def _onsen_base_id(item_id: str) -> str:
    if item_id.endswith("_en") or item_id.endswith("_ko"):
        return item_id.rsplit("_", 1)[0]
    return item_id


@pages_bp.route("/compare")
def compare_page():
    lang = request.args.get("lang", "en")
    if lang not in ("en", "ko"):
        lang = "en"
    raw_ids = [x.strip() for x in (request.args.get("ids") or "").split(",") if x.strip()]
    ids = []
    for rid in raw_ids:
        base = _onsen_base_id(rid)
        if base not in ids:
            ids.append(base)
        if len(ids) >= 3:
            break
    ensure_onsen_cache()
    by_base = {}
    for row in CACHED_DATA.get("onsens", []):
        if row.get("lang") != lang:
            continue
        base = _onsen_base_id(row.get("id", ""))
        item = public_onsen(row)
        item["base_id"] = base
        by_base[base] = item
    selected = [by_base[i] for i in ids if i in by_base]
    meta_title = "온천·료칸 비교 | OKOnsen" if lang == "ko" else "Compare onsen & ryokan | OKOnsen"
    meta_desc = (
        "선택한 온천·료칸을 특징·지역·요약으로 비교합니다."
        if lang == "ko"
        else "Compare selected onsen and ryokan stays by features, area, and summary."
    )
    stats = get_footer_stats(lang)
    return render_template(
        "compare.html",
        lang=lang,
        selected=selected,
        meta_title=meta_title,
        meta_desc=meta_desc,
        **stats,
    )

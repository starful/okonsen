"""Home and guide hub pages."""

from __future__ import annotations

from flask import Blueprint, render_template, request

try:
    from ..config import GOOGLE_MAPS_API_KEY
    from ..content_loader import get_all_guides, get_priority_guides
    from ..data_cache import get_featured_onsens, get_footer_stats
except ImportError:
    from config import GOOGLE_MAPS_API_KEY
    from content_loader import get_all_guides, get_priority_guides
    from data_cache import get_featured_onsens, get_footer_stats

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

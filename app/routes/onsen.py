"""Onsen detail, social card, and map API routes."""

from __future__ import annotations

import os

import frontmatter
import markdown
from flask import Blueprint, abort, jsonify, render_template, request

try:
    from ..config import CATEGORY_MAPPING, CONTENT_DIR, FAMILY_SITE_ID, SITE_URL
    from ..rakuten_affiliate import rakuten_context
    from ..content_loader import get_all_guides, normalize_markdown_source
    from ..data_cache import (
        CACHED_DATA,
        ensure_onsen_cache,
        get_featured_onsens,
        get_footer_stats,
        public_onsen,
    )
    from ..family_sites import cross_links_for, inject_family_context
    from ..images import card_path, gcs_image_url, og_image_context, thumbnail_cache_v, thumbnail_with_v
    from ..seo import share_context
except ImportError:
    from config import CATEGORY_MAPPING, CONTENT_DIR, FAMILY_SITE_ID, SITE_URL
    from rakuten_affiliate import rakuten_context
    from content_loader import get_all_guides, normalize_markdown_source
    from data_cache import (
        CACHED_DATA,
        ensure_onsen_cache,
        get_featured_onsens,
        get_footer_stats,
        public_onsen,
    )
    from family_sites import cross_links_for, inject_family_context
    from images import card_path, gcs_image_url, og_image_context, thumbnail_cache_v, thumbnail_with_v
    from seo import share_context

onsen_bp = Blueprint("onsen", __name__)


@onsen_bp.route("/api/onsens")
def api_onsens():
    requested_lang = request.args.get("lang", "en")
    ensure_onsen_cache()
    data_list = CACHED_DATA.get("onsens", [])
    filtered = [o for o in data_list if o.get("lang") == requested_lang]
    if not filtered:
        filtered = [o for o in data_list if o.get("lang") == "en"]

    spoofed_list = []
    for onsen in filtered:
        spoofed = public_onsen(onsen)
        spoofed["lang"] = "en"  # JS Spoofing
        new_cats = [
            CATEGORY_MAPPING.get(c.strip(), c.strip())
            for c in spoofed.get("categories", [])
        ]
        spoofed["categories"] = list(set(new_cats))
        spoofed_list.append(spoofed)
    return jsonify({"onsens": spoofed_list, "last_updated": CACHED_DATA.get("last_updated")})


@onsen_bp.route("/onsen/<onsen_id>")
def onsen_detail(onsen_id):
    md_path = os.path.join(CONTENT_DIR, f"{onsen_id}.md")
    if not os.path.exists(md_path):
        abort(404)
    with open(md_path, "r", encoding="utf-8") as f:
        post = frontmatter.loads(normalize_markdown_source(f.read()))

    if isinstance(post.get("categories"), str):
        post["categories"] = [c.strip() for c in post["categories"].split(",")]

    base_id = onsen_id.rsplit("_", 1)[0]
    cache_v = thumbnail_cache_v(post.get("date") or post.get("published"))
    thumb = post.get("thumbnail") or gcs_image_url(f"{base_id}.jpg")
    post["thumbnail"] = thumbnail_with_v(thumb, cache_v)
    lang = post.get("lang", "en")

    content_html = markdown.markdown(post.content, extensions=["tables"])
    related_guides = get_all_guides(lang)[:6]
    featured_onsens = [
        o for o in get_featured_onsens(lang, limit=10) if o.get("id") != onsen_id
    ][:8]
    stats = get_footer_stats(lang)
    share_ctx = share_context(
        onsen_id,
        post.get("title", "OKOnsen"),
        lang,
        f"/onsen/{onsen_id}",
        base_id=base_id,
    )

    return render_template(
        "detail.html",
        post=post,
        content=content_html,
        base_id=base_id,
        onsen_id=onsen_id,
        lang=lang,
        related_guides=related_guides,
        featured_onsens=featured_onsens,
        cross_site_links=cross_links_for(
            FAMILY_SITE_ID, lang, address=post.get("address")
        ),
        **inject_family_context(FAMILY_SITE_ID, lang),
        **og_image_context(base_id),
        **stats,
        **share_ctx,
        **rakuten_context(onsen_id, lang=lang),
    )


@onsen_bp.route("/card/<onsen_id>")
def onsen_social_card(onsen_id):
    """Lightweight share landing page for X/OG crawlers."""
    md_path = os.path.join(CONTENT_DIR, f"{onsen_id}.md")
    if not os.path.exists(md_path):
        abort(404)

    with open(md_path, "r", encoding="utf-8") as f:
        post = frontmatter.loads(normalize_markdown_source(f.read()))

    base_id = onsen_id.rsplit("_", 1)[0]
    lang = post.get("lang", "en")
    title = post.get("title", "OKOnsen")
    summary = post.get("summary", "")
    page_path = f"/onsen/{onsen_id}"

    return render_template(
        "social_card.html",
        lang=lang,
        title=title,
        seo_title=f"{title} - OKOnsen",
        seo_desc=summary,
        page_url=f"{SITE_URL}{page_path}",
        card_url=f"{SITE_URL}{card_path(onsen_id)}",
        **og_image_context(base_id),
    )

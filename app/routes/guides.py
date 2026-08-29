"""Guide detail pages."""

from __future__ import annotations

import os
import re

import frontmatter
import markdown
from flask import Blueprint, abort, render_template, request

try:
    from ..config import FAMILY_SITE_ID, GUIDE_DIR
    from ..a8_affiliate import a8_banners_context
    from ..rakuten_affiliate import rakuten_context
    from ..content_loader import (
        extract_faq_items,
        get_all_guides,
        get_mapped_image,
        mark_external_links,
        normalize_markdown_source,
    )
    from ..data_cache import get_featured_onsens, get_footer_stats
    from ..family_sites import cross_links_for, inject_family_context
    from ..seo import hreflang_flags, share_context
except ImportError:
    from config import FAMILY_SITE_ID, GUIDE_DIR
    from a8_affiliate import a8_banners_context
    from rakuten_affiliate import rakuten_context
    from content_loader import (
        extract_faq_items,
        get_all_guides,
        get_mapped_image,
        mark_external_links,
        normalize_markdown_source,
    )
    from data_cache import get_featured_onsens, get_footer_stats
    from family_sites import cross_links_for, inject_family_context
    from seo import hreflang_flags, share_context

guides_bp = Blueprint("guides", __name__)


@guides_bp.route("/guide/<guide_id>")
def guide_detail(guide_id):
    inferred_lang = "ko" if guide_id.endswith("_ko") else "en"
    lang = request.args.get("lang", inferred_lang)
    if lang not in ("en", "ko"):
        lang = inferred_lang
    path = os.path.join(GUIDE_DIR, f"{guide_id}.md")
    if not os.path.exists(path):
        abort(404)

    with open(path, "r", encoding="utf-8") as f:
        raw_content = normalize_markdown_source(f.read())
        post = frontmatter.loads(raw_content)
        title = post.get("title")
        summary = post.get("summary")
        body = post.content
        if not title or title == "None":
            title_match = re.search(r'title:\s*"(.*?)"', raw_content)
            title = title_match.group(1) if title_match else "Travel Guide"
        if not summary or summary == "None":
            summary = post.content[:160].replace("\n", " ").strip()

        body = re.sub(r"---.*?---", "", body, flags=re.DOTALL)
        body = body.replace("```markdown", "").replace("```", "").strip()

    content_html = mark_external_links(
        markdown.markdown(body, extensions=["tables", "toc", "fenced_code"]),
        lang=lang,
    )
    base_id = guide_id.rsplit("_", 1)[0]
    image_url = get_mapped_image(base_id)
    faq_items = extract_faq_items(body)
    related_guides = [g for g in get_all_guides(lang) if g.get("id") != guide_id][:6]
    featured_onsens = get_featured_onsens(lang, limit=10)
    stats = get_footer_stats(lang)
    share_ctx = share_context(guide_id, title, lang, f"/guide/{guide_id}")
    # Prefer region cross-links (e.g. Hakone → ramen then golf) over bare homepages.
    guide_address = None
    gid_lower = guide_id.lower()
    for region in (
        "hakone",
        "kurokawa",
        "kusatsu",
        "yufuin",
        "kinosaki",
        "beppu",
        "arima",
        "tokyo",
        "kyoto",
        "osaka",
        "hokkaido",
        "okinawa",
        "fukuoka",
    ):
        if region in gid_lower:
            guide_address = f"{region.title()}, Japan"
            break

    return render_template(
        "guide_detail.html",
        title=title,
        summary=summary,
        content=content_html,
        lang=lang,
        image_url=image_url,
        base_id=base_id,
        faq_items=faq_items,
        related_guides=related_guides,
        featured_onsens=featured_onsens,
        cross_site_links=cross_links_for(
            FAMILY_SITE_ID, lang, address=guide_address
        ),
        **inject_family_context(FAMILY_SITE_ID, lang),
        **stats,
        **share_ctx,
        **hreflang_flags("guide", base_id),
        **rakuten_context(guide_id, lang=lang),
        **a8_banners_context(lang=lang),
    )

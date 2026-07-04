"""SEO URL normalization and social sharing context."""

from __future__ import annotations

import os
from urllib.parse import quote

from flask import Flask, redirect, request

try:
    from .config import CONTENT_DIR, GUIDE_DIR, SITE_URL
    from .images import card_path
except ImportError:
    from config import CONTENT_DIR, GUIDE_DIR, SITE_URL
    from images import card_path


def linkedin_inspector_url(page_url: str) -> str:
    return f"https://www.linkedin.com/post-inspector/inspect/{quote(page_url, safe='')}"


def share_context(
    slug: str, title: str, lang: str, page_path: str, base_id: str = ""
) -> dict:
    share_url = f"{SITE_URL}{page_path}"
    share_url_x = f"{SITE_URL}{card_path(slug)}"
    if lang == "ko":
        share_tweet = f"{title} — OKOnsen"
    else:
        share_tweet = f"{title} — Japan onsen guide on OKOnsen"
    return {
        "share_id": slug,
        "share_url": share_url,
        "share_url_x": share_url_x,
        "share_tweet": share_tweet,
        "share_lang": lang if lang in ("en", "ko") else "en",
        "og_page_url": share_url,
        "linkedin_inspector_url": linkedin_inspector_url(share_url),
    }


def resolve_lang_slug_redirect(prefix: str, slug: str, content_dir: str):
    """Redirect /guide/base or /onsen/base to the canonical *_en/*_ko URL."""
    if not slug or slug.endswith("_en") or slug.endswith("_ko"):
        return None
    en_path = os.path.join(content_dir, f"{slug}_en.md")
    ko_path = os.path.join(content_dir, f"{slug}_ko.md")
    if os.path.exists(en_path):
        return redirect(f"{prefix}/{slug}_en", code=301)
    if os.path.exists(ko_path):
        return redirect(f"{prefix}/{slug}_ko", code=301)
    return None


def register_seo_middleware(app: Flask) -> None:
    @app.before_request
    def seo_url_normalization():
        if request.method not in ("GET", "HEAD"):
            return None
        p = request.path
        if p.startswith("/static/") or p.startswith("/api/"):
            return None
        if p in (
            "/sitemap.xml",
            "/sitemap-core.xml",
            "/sitemap-longtail.xml",
            "/robots.txt",
        ):
            return None
        if request.headers.get("X-Forwarded-Proto", "").lower() == "http":
            return redirect(request.url.replace("http://", "https://", 1), code=301)
        args = request.args
        keys = set(args.keys())
        if p == "/" and keys == {"lang"} and args.get("lang") == "en":
            return redirect("/", code=301)
        if p == "/guides" and keys == {"lang"} and args.get("lang") == "en":
            return redirect("/guides", code=301)
        if p in ("/about.html", "/privacy.html"):
            return redirect(p.replace(".html", ""), code=301)

        if p.startswith("/guide/") and len(p) > len("/guide/"):
            slug = p.rsplit("/", 1)[-1]
            target = resolve_lang_slug_redirect("/guide", slug, GUIDE_DIR)
            if target:
                return target
            if keys == {"lang"}:
                return redirect(p, code=301)
        if p.startswith("/onsen/") and len(p) > len("/onsen/"):
            slug = p.rsplit("/", 1)[-1]
            target = resolve_lang_slug_redirect("/onsen", slug, CONTENT_DIR)
            if target:
                return target
            if keys == {"lang"}:
                return redirect(p, code=301)
        return None

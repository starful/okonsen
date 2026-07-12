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


# Removed thin/duplicate pages → surviving sibling or canonical topic (GSC 2026-07-12).
CONTENT_GONE_REDIRECTS = {
    "/guide/private_bath_kashikiri_ko": "/guide/private_bath_kashikiri_en",
    "/guide/kurokawa_hidden_gems_ko": "/guide/kurokawa_hidden_gems_en",
    "/guide/ryokan_kaiseki_experience_en": "/guide/ryokan_kaiseki_experience_ko",
    "/guide/beppu_eight_hells_tour_en": "/guide/beppu_hell_tour_guide_en",
    "/guide/beppu_eight_hells_tour_ko": "/guide/beppu_hell_tour_guide_ko",
    "/onsen/beppu_showaen_ko": "/onsen/beppu_showaen_en",
    "/onsen/kinosaki_onsen_mikuniya_ko": "/onsen/kinosaki_onsen_mikuniya_en",
    "/onsen/kurokawa_onsen_gosho_gekkoju_ko": "/onsen/kurokawa_onsen_gosho_gekkoju_en",
    "/onsen/kurokawa_onsen_nanjoen_ko": "/onsen/kurokawa_onsen_nanjoen_en",
    "/onsen/kusatsu_onsen_hotel_village_ko": "/onsen/kusatsu_onsen_hotel_village_en",
    "/onsen/kusatsu_onsen_ryokan_yoshinoya_ko": "/onsen/kusatsu_onsen_ryokan_yoshinoya_en",
    "/onsen/kusatsu_onsen_tokinoniwa_ko": "/onsen/kusatsu_onsen_tokinoniwa_en",
    "/onsen/yufuin_baien_en": "/onsen/yufuin_baien_ko",
    "/onsen/yufuin_sansou_waremokou_en": "/onsen/yufuin_sansou_waremokou_ko",
    "/onsen/amane_resort_seikai_ko": "/onsen/amane_resort_seikai_en",
    "/onsen/beppu_daiiti_hotel_ko": "/onsen/beppu_daiiti_hotel_en",
    "/onsen/yubatake_souan_ko": "/onsen/yubatake_souan_en",
    "/onsen/yufuin_hotel_shumeikan_ko": "/onsen/yufuin_hotel_shumeikan_en",
    "/onsen/kinosaki_onsen_tajimaya_ko": "/onsen/kinosaki_onsen_tajimaya_en",
    "/onsen/kurokawa_onsen_shinmeikan_ko": "/onsen/kurokawa_onsen_shinmeikan_en",
    "/onsen/hotel_indigo_hakone_gora_ko": "/onsen/hotel_indigo_hakone_gora_en",
    "/onsen/the_prince_hakone_lake_ashinoko_ko": "/onsen/the_prince_hakone_lake_ashinoko_en",
    "/onsen/kusatsu_onsen_daitokan_en": "/onsen/kusatsu_onsen_daitokan_ko",
    "/onsen/kusatsu_onsen_hotel_sakurai_en": "/onsen/kusatsu_onsen_hotel_sakurai_ko",
    "/onsen/kurokawa_onsen_fujiya_ko": "/onsen/kurokawa_onsen_fujiya_en",
    "/onsen/kusatsu_onsen_konoha_en": "/onsen/kusatsu_onsen_konoha_ko",
    "/onsen/hakone_suimeisou_en": "/onsen/hakone_suimeisou_ko",
    "/onsen/kinosaki_onsen_tsubakino_ryokan_ko": "/onsen/kinosaki_onsen_tsubakino_ryokan_en",
    "/onsen/kurokawa_onsen_hozantei_ko": "/onsen/kurokawa_onsen_hozantei_en",
    # Legacy slug typos / doubles (no local content)
    "/onsen/arima_onsen_tocen_goshobo_en": "/onsen/arima_onsen_tosen_goshobo_en",
    "/onsen/arima_onsen_tocen_goshobo_ko": "/onsen/arima_onsen_tosen_goshobo_ko",
    "/onsen/kinosaki_onsen_koyado_en_en": "/onsen/kinosaki_onsen_shinmatsuya_en",
}


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

        gone_target = CONTENT_GONE_REDIRECTS.get(p)
        if gone_target:
            return redirect(gone_target, code=301)

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

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

# GSC 2026-07-30 Coverage Drilldown — Not found (404). Prefer area hub / sibling.
GSC_404_REDIRECTS = {
    "/onsen/": "/",
    "/card/winter_onsen_experience_ko": "/guides",
    "/guide/arima_onsen_golden_water_en": "/onsen/arima_onsen_tosen_goshobo_en",
    "/guide/dogo_onsen_studio_ghibli_en": "/guides",
    "/guide/dogo_onsen_studio_ghibli_ko": "/guides",
    "/guide/guide_expand_001_en": "/guides",
    "/guide/guide_expand_002_en": "/guides",
    "/guide/guide_seed_003_en": "/guides",
    "/guide/kinosaki_seven_bath_crawl_en": "/onsen/kinosaki_onsen_mikuniya_en",
    "/guide/winter_yukimi_rotemburo_ko": "/guides",
    "/guide/yufuin_scenic_walk_en": "/onsen/yufuin_onsen_yufuin-so_en",
    "/onsen/beppu_onsen_takegawara_en": "/guide/beppu_hell_tour_guide_en",
    "/onsen/beppu_onsen_takegawara_ko": "/guide/beppu_hell_tour_guide_ko",
    "/onsen/bettei_haruki_ko": "/",
    "/onsen/fujiya_hotel_en": "/",
    "/onsen/gallo_resort_beppu_en": "/guide/beppu_hell_tour_guide_en",
    "/onsen/hakodate_morning_market_cafe_en": "/",
    "/onsen/hakone_ginyu_ko": "/guide/hakone_day_trip_guide_ko",
    "/onsen/hakone_kamon_ko": "/guide/hakone_day_trip_guide_ko",
    "/onsen/hiroshima_peace_park_cafe_en": "/",
    "/onsen/hoshino_resorts_kai_hakone_en": "/guide/hakone_day_trip_guide_en",
    "/onsen/hoshino_resorts_kai_yufuin_en": "/onsen/yufuin_onsen_yufuin-so_en",
    "/onsen/kamakura_komachi_drip_en": "/",
    "/onsen/kamenoi_bessou_ko": "/",
    "/onsen/kinosaki_onsen_kinosaki_yamata_ko": "/onsen/kinosaki_onsen_mikuniya_en",
    "/onsen/kinosaki_onsen_nishimuraya_ricca_en": "/onsen/kinosaki_onsen_mikuniya_en",
    "/onsen/kurokawa_onsen_kurokawaso_ko": "/onsen/kurokawa_onsen_oku_no_yu_ko",
    "/onsen/kusatsu_onsen_boun_ko": "/onsen/kusatsu_onsen_ryokan_yoshinoya_en",
    "/onsen/kusatsu_onsen_eidaya_en": "/onsen/kusatsu_onsen_ryokan_yoshinoya_en",
    "/onsen/kusatsu_onsen_eidaya_ko": "/onsen/kusatsu_onsen_ryokan_yoshinoya_en",
    "/onsen/kusatsu_onsen_naraya_en": "/onsen/kusatsu_onsen_ryokan_yoshinoya_en",
    "/onsen/kusatsu_onsen_yugokoro_tei_ko": "/onsen/kusatsu_onsen_ryokan_yoshinoya_en",
    "/onsen/nara_parkside_kissaten_en": "/",
    "/onsen/noboribetsu_onsen_hotel_yumoto_ko": "/",
    "/onsen/noboribetsu_onsen_kokorono_resort_en": "/",
    "/onsen/noboribetsu_onsen_oyado_kiyomizuya_ko": "/",
    "/onsen/ryokan_yuri_en": "/",
    "/onsen/ryoutei_matsudaya_ko": "/",
    "/onsen/sendai_ichibancho_latte_en": "/",
    "/onsen/yamada_bessou_en": "/",
    "/onsen/yamada_bessou_ko": "/",
    "/onsen/yoshiike_ryokan_ko": "/",
    "/onsen/yufuin_uraku_ko": "/onsen/yufuin_onsen_yufuin-so_ko",
    "/onsen/yufuin_yasuha_ko": "/onsen/yufuin_onsen_yufuin-so_ko",
}

# Union used by middleware + sitemap exclusion.
SEO_REDIRECTS = {**CONTENT_GONE_REDIRECTS, **GSC_404_REDIRECTS}


def is_indexable_path(path: str) -> bool:
    """True when path is not a permanent SEO redirect source."""
    return path not in SEO_REDIRECTS


def sibling_is_indexable(prefix: str, base_id: str, lang: str) -> bool:
    """Whether /{prefix}/{base_id}_{lang} should be advertised (hreflang / lang switcher)."""
    path = f"/{prefix}/{base_id}_{lang}"
    if not is_indexable_path(path):
        return False
    content_dir = GUIDE_DIR if prefix == "guide" else CONTENT_DIR
    return os.path.exists(os.path.join(content_dir, f"{base_id}_{lang}.md"))


def hreflang_flags(prefix: str, base_id: str) -> dict:
    return {
        "has_en": sibling_is_indexable(prefix, base_id, "en"),
        "has_ko": sibling_is_indexable(prefix, base_id, "ko"),
    }


def register_seo_middleware(app: Flask) -> None:
    @app.before_request
    def seo_url_normalization():
        if request.method not in ("GET", "HEAD"):
            return None
        p = request.path

        # Junk API path that GSC reported as 404 (before /api/ skip).
        if p.rstrip("/") == "/api/reactions":
            return redirect("/", code=301)

        if p.startswith("/static/") or p.startswith("/api/"):
            return None
        if p in (
            "/sitemap.xml",
            "/sitemap-core.xml",
            "/sitemap-longtail.xml",
            "/robots.txt",
            "/ads.txt",
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

        # Prefer explicit SEO maps before slash-normalization (/onsen/ etc.).
        for candidate in dict.fromkeys((p, p.rstrip("/") if p != "/" else p)):
            gone_target = SEO_REDIRECTS.get(candidate)
            if gone_target:
                return redirect(gone_target, code=301)

        # Trailing slash → slashless (except site root).
        if len(p) > 1 and p.endswith("/"):
            qs = request.query_string.decode("utf-8") if request.query_string else ""
            target = p.rstrip("/")
            if qs:
                target = f"{target}?{qs}"
            return redirect(target, code=301)

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

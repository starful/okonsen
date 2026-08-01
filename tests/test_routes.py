"""Core route and SEO redirect regression tests."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from __init__ import app as flask_app  # noqa: E402
from seo import GSC_404_REDIRECTS, SEO_REDIRECTS  # noqa: E402


@pytest.fixture()
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_home_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"OKOnsen" in r.data or b"onsen" in r.data.lower()


def test_guides_hub(client):
    r = client.get("/guides")
    assert r.status_code == 200


def test_about_page(client):
    r = client.get("/about")
    assert r.status_code == 200


def test_about_html_redirect(client):
    r = client.get("/about.html", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["Location"].endswith("/about")


def test_privacy_html_redirect(client):
    r = client.get("/privacy.html", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["Location"].endswith("/privacy")


def test_home_lang_en_redirect(client):
    r = client.get("/?lang=en", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["Location"].endswith("/")


def test_onsen_lang_query_stripped(client):
    r = client.get(
        "/onsen/kusatsu_onsen_ryokan_yoshinoya_en?lang=en", follow_redirects=False
    )
    assert r.status_code == 301
    assert r.headers["Location"].endswith(
        "/onsen/kusatsu_onsen_ryokan_yoshinoya_en"
    )


def test_gone_content_redirect(client):
    r = client.get("/guide/beppu_eight_hells_tour_en", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["Location"].endswith("/guide/beppu_hell_tour_guide_en")


def test_gsc_404_redirect(client):
    r = client.get("/onsen/sendai_ichibancho_latte_en", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["Location"].endswith("/")


def test_trailing_slash_redirect(client):
    r = client.get("/guides/", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["Location"].endswith("/guides")


def test_onsen_hub_slash_redirect(client):
    r = client.get("/onsen/", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["Location"].endswith("/")


def test_api_reactions_redirect(client):
    r = client.get("/api/reactions/", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["Location"].endswith("/")


def test_social_card_noindex(client):
    r = client.get("/card/kurokawa_onsen_hozantei_en")
    if r.status_code == 404:
        pytest.skip("sample onsen missing")
    assert r.status_code == 200
    assert b"noindex" in r.data


def test_hreflang_skips_gone_sibling(client):
    # yoshinoya_ko is CONTENT_GONE → EN page must not advertise KO hreflang
    r = client.get("/onsen/kusatsu_onsen_ryokan_yoshinoya_en")
    assert r.status_code == 200
    body = r.data.decode("utf-8")
    assert 'hreflang="en"' in body
    assert "kusatsu_onsen_ryokan_yoshinoya_ko" not in body


def test_seo_redirects_cover_gsc_404s():
    for path in GSC_404_REDIRECTS:
        assert path in SEO_REDIRECTS


def test_api_onsens(client):
    r = client.get("/api/onsens?lang=en")
    assert r.status_code == 200
    data = r.get_json()
    assert "onsens" in data
    assert "last_updated" in data
    assert isinstance(data["onsens"], list)


def test_robots_txt(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    text = r.data.decode("utf-8")
    assert "Disallow: /api/" in text
    assert "Disallow: /card/" in text
    assert "Sitemap:" in text


def test_ads_txt(client):
    r = client.get("/ads.txt")
    assert r.status_code == 200
    text = r.data.decode("utf-8")
    assert "google.com, pub-8780435268193938, DIRECT, f08c47fec0942fa0" in text

"""Core route and SEO redirect regression tests."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from __init__ import app as flask_app  # noqa: E402


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

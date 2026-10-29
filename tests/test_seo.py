"""SEO and X card regression tests."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from __init__ import app as flask_app  # noqa: E402
from seo import dedupe_longtail, is_thin_body  # noqa: E402


@pytest.fixture()
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_onsen_detail_has_social_meta(client):
    r = client.get("/onsen/kusatsu_onsen_ryokan_yoshinoya_en")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "share-bar" in html
    assert "share-btn-x" in html
    assert "/social/kusatsu_onsen_ryokan_yoshinoya.jpg" in html
    assert 'name="twitter:image"' in html
    assert "card/kusatsu_onsen_ryokan_yoshinoya_en" in html


def test_social_image_endpoint(client):
    r = client.get("/social/kusatsu_onsen_ryokan_yoshinoya.jpg")
    assert r.status_code == 200
    assert r.headers.get("Content-Type", "").startswith("image/jpeg")
    assert len(r.get_data()) > 1000


def test_social_card_page(client):
    r = client.get("/card/kusatsu_onsen_ryokan_yoshinoya_en")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'property="og:url" content="https://okonsen.net/card/kusatsu_onsen_ryokan_yoshinoya_en"' in html
    assert "/social/kusatsu_onsen_ryokan_yoshinoya.jpg" in html
    assert "View onsen guide" in html


def test_is_thin_body():
    assert is_thin_body(100, "onsen") is True
    assert is_thin_body(5000, "onsen") is False
    assert is_thin_body(3000, "guide") is True
    assert is_thin_body(4500, "guide") is False


def test_dedupe_longtail_drops_thin_and_duplicate_bodies():
    items = [
        {"id": "a", "body_chars": 5000, "body_hash": "h1"},
        {"id": "b", "body_chars": 5000, "body_hash": "h1"},  # duplicate of a
        {"id": "c", "body_chars": 100, "body_hash": "h2"},  # too thin
        {"id": "d", "body_chars": 5000, "body_hash": "h3"},
    ]
    kept = dedupe_longtail(items, kind="onsen")
    assert [i["id"] for i in kept] == ["a", "d"]

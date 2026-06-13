"""Smoke tests for reactions API and detail templates."""
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


def test_reactions_api(client):
    r = client.get("/api/reactions/test-slug")
    assert r.status_code == 200
    data = r.get_json()
    assert "likes" in data
    assert "dislikes" in data


def test_onsen_detail_has_reaction_panel(client):
    r = client.get("/onsen/kusatsu_onsen_ryokan_yoshinoya_en")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "reaction-panel" in html
    assert "/api/reactions/" in html
    assert "share-bar" in html

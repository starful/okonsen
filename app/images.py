"""Image URL helpers and on-site social/OG image generation."""

from __future__ import annotations

import io
import re
import urllib.request

from flask import Response, abort

try:
    from .config import GCS_ASSET_PREFIX, SITE_URL
except ImportError:
    from config import GCS_ASSET_PREFIX, SITE_URL


def gcs_image_url(filename: str) -> str:
    return f"https://storage.googleapis.com/ok-project-assets/{GCS_ASSET_PREFIX}/{filename}"


def thumbnail_cache_v(published_or_date: str | None) -> str:
    v = str(published_or_date or "").strip()[:10]
    return v if len(v) >= 8 else ""


def thumbnail_with_v(url: str, cache_v: str | None = None) -> str:
    if not url:
        return url
    v = thumbnail_cache_v(cache_v)
    base = url.split("?", 1)[0]
    return f"{base}?v={v}" if v else base


def social_image_url(base_id: str) -> str:
    safe = re.sub(r"[^a-z0-9_-]", "", base_id.lower())
    return f"{SITE_URL}/social/{safe}.jpg"


def og_image_context(base_id: str) -> dict:
    og_image_abs = social_image_url(base_id)
    return {
        "og_image_abs": og_image_abs,
        "og_image_width": 1200,
        "og_image_height": 630,
    }


def card_path(onsen_id: str) -> str:
    return f"/card/{onsen_id}"


def jpeg_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=78, optimize=True, progressive=True)
    return buf.getvalue()


def build_social_image_response(slug: str) -> Response:
    """Serve onsen thumbnail on-site for OG/Twitter (1200x630 JPEG, no redirect)."""
    safe = re.sub(r"[^a-z0-9_-]", "", slug.lower())
    if not safe:
        abort(404)
    gcs_url = gcs_image_url(f"{safe}.jpg")
    try:
        with urllib.request.urlopen(gcs_url, timeout=15) as resp:
            raw = resp.read()
            if not raw:
                abort(404)
    except Exception:
        abort(404)

    try:
        from PIL import Image, ImageOps

        img = Image.open(io.BytesIO(raw)).convert("RGB")
        data = jpeg_bytes(ImageOps.fit(img, (1200, 630), Image.Resampling.LANCZOS))
    except Exception:
        data = raw

    return Response(
        data,
        mimetype="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )

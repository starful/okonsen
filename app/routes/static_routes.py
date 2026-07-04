"""Static assets, sitemap, and informational pages."""

from __future__ import annotations

import os

from flask import Blueprint, redirect, render_template, request, send_from_directory

try:
    from ..config import STATIC_DIR
    from ..images import build_social_image_response
except ImportError:
    from config import STATIC_DIR
    from images import build_social_image_response

static_bp = Blueprint("static_routes", __name__)


@static_bp.route("/sitemap.xml")
def sitemap_xml():
    """Search Console / crawlers expect https://okonsen.net/sitemap.xml (see robots.txt)."""
    return send_from_directory(STATIC_DIR, "sitemap.xml", mimetype="application/xml")


@static_bp.route("/sitemap-core.xml")
def sitemap_core_xml():
    return send_from_directory(
        STATIC_DIR, "sitemap-core.xml", mimetype="application/xml"
    )


@static_bp.route("/sitemap-longtail.xml")
def sitemap_longtail_xml():
    return send_from_directory(
        STATIC_DIR, "sitemap-longtail.xml", mimetype="application/xml"
    )


@static_bp.route("/robots.txt")
def robots_txt():
    return send_from_directory(STATIC_DIR, "robots.txt", mimetype="text/plain")


@static_bp.route("/favicon.ico")
def favicon_ico():
    return redirect("/static/images/favicons.ico", code=301)


@static_bp.route("/static/images/<path:filename>")
def serve_images(filename):
    """이미지는 GCS가 기준 — okadmin 업로드 즉시 반영."""
    images_root = os.path.join(STATIC_DIR, "images")
    if any(x in filename for x in ["favicon", "apple-touch"]):
        local_path = os.path.join(images_root, filename)
        if os.path.isfile(local_path):
            return send_from_directory(images_root, filename)
    url = f"https://storage.googleapis.com/ok-project-assets/okonsen/{filename}"
    if request.query_string:
        url = f"{url}?{request.query_string.decode()}"
    return redirect(url, code=302)


@static_bp.route("/social/<slug>.jpg")
def social_image(slug):
    return build_social_image_response(slug)


@static_bp.route("/about")
@static_bp.route("/about.html")
def about_page():
    return render_template("about.html")


@static_bp.route("/privacy")
@static_bp.route("/privacy.html")
def privacy_page():
    return render_template("privacy.html")

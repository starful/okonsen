"""Route blueprint registration."""

from __future__ import annotations

from flask import Flask

try:
    from .guides import guides_bp
    from .onsen import onsen_bp
    from .pages import pages_bp
    from .static_routes import static_bp
except ImportError:
    from app.routes.guides import guides_bp
    from app.routes.onsen import onsen_bp
    from app.routes.pages import pages_bp
    from app.routes.static_routes import static_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(static_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(guides_bp)
    app.register_blueprint(onsen_bp)

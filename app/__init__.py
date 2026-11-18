"""OKOnsen Flask application."""

from __future__ import annotations

import os

from flask import Flask, request
from flask_compress import Compress

try:
    from .config import FAMILY_SITE_ID
    from .family_sites import inject_family_context
    from .reactions import reactions_bp
    from .routes import register_routes
    from .seo import register_seo_middleware
except ImportError:
    from config import FAMILY_SITE_ID
    from family_sites import inject_family_context
    from reactions import reactions_bp
    from routes import register_routes
    from seo import register_seo_middleware

app = Flask(__name__)
Compress(app)

app.register_blueprint(reactions_bp)
register_routes(app)
register_seo_middleware(app)


@app.context_processor
def inject_family_sites():
    lang = request.args.get("lang", "en") if request else "en"
    return inject_family_context(FAMILY_SITE_ID, lang)



# Anonymous visit log for Starful HQ「이용자 보기」
from pathlib import Path as _VisitPath
try:
    from visitkit.flask_api import register_visitlog as _register_visitlog
except ImportError:
    import sys as _sys
    _sys.path.insert(0, str(_VisitPath(__file__).resolve().parents[1]))
    from visitkit.flask_api import register_visitlog as _register_visitlog
_register_visitlog(app, site_id="okonsen", db_path=_VisitPath(__file__).resolve().parents[1] / "data" / "visitlog.sqlite3")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

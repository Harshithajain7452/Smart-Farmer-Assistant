"""
Smart Farmer Assistant — application factory.

Run locally:
    python app.py
Run in production:
    gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 3 --timeout 120
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, g, render_template, request, session
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from config.config import get_config
from extensions import csrf, db, login_manager
from utils.i18n import get_locale, translate


def create_app(config_object=None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object or get_config())

    # Correct client IP / scheme behind Render, Railway or an AWS ALB.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    _ensure_directories(app)
    _init_extensions(app)
    _register_blueprints(app)
    _register_hooks(app)
    _register_error_handlers(app)
    _configure_logging(app)

    with app.app_context():
        from models import models  # noqa: F401 — register mappers
        db.create_all()
        from utils.seed_data import seed_all
        seed_all()

    return app


# ---------------------------------------------------------------------------
def _ensure_directories(app):
    for path in (app.config["UPLOAD_FOLDER"], app.config["MODEL_DIR"],
                 app.config["DATASET_DIR"]):
        os.makedirs(path, exist_ok=True)
    for sub in ("disease", "pest", "avatars"):
        os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], sub), exist_ok=True)


def _init_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from models.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


def _register_blueprints(app):
    from routes.admin import admin_bp
    from routes.advisor import advisor_bp
    from routes.api import api_bp
    from routes.auth import auth_bp
    from routes.chatbot import chatbot_bp
    from routes.dashboard import dashboard_bp
    from routes.detection import detection_bp
    from routes.knowledge import knowledge_bp
    from routes.main import main_bp
    from routes.market import market_bp
    from routes.weather import weather_bp

    for bp in (main_bp, auth_bp, dashboard_bp, detection_bp, weather_bp, market_bp,
               knowledge_bp, advisor_bp, chatbot_bp, admin_bp, api_bp):
        app.register_blueprint(bp)

    # JSON endpoints are session-authenticated and same-origin: exempt from
    # form-token CSRF (the browser fetch() calls still send the session cookie).
    csrf.exempt(api_bp)
    csrf.exempt(chatbot_bp)


def _register_hooks(app):
    from services.notification_service import unread_count

    @app.before_request
    def resolve_language():
        g.lang = get_locale()

    @app.context_processor
    def inject_globals():
        return {
            "t": translate,
            "current_lang": getattr(g, "lang", "en"),
            "languages": app.config["SUPPORTED_LANGUAGES"],
            "unread_notifications": (unread_count(current_user.id)
                                     if current_user.is_authenticated else 0),
            "active_endpoint": request.endpoint or "",
            "theme": session.get("theme", "light"),
            "maps_key": app.config.get("GOOGLE_MAPS_API_KEY", ""),
        }

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(self), microphone=(), camera=()")
        return response


def _register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(_):
        return render_template("errors/error.html", code=403,
                               message="You do not have permission to view this page."), 403

    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors/error.html", code=404,
                               message="The page you are looking for does not exist."), 404

    @app.errorhandler(413)
    def too_large(_):
        return render_template("errors/error.html", code=413,
                               message="That file is larger than the 8 MB upload limit."), 413

    @app.errorhandler(500)
    def server_error(exc):
        db.session.rollback()
        app.logger.exception("Unhandled error: %s", exc)
        return render_template("errors/error.html", code=500,
                               message="Something went wrong on our side. Please retry."), 500


def _configure_logging(app):
    if app.debug or app.testing:
        return
    os.makedirs("logs", exist_ok=True)
    handler = RotatingFileHandler("logs/smart_farmer.log", maxBytes=1_000_000, backupCount=5)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(module)s:%(lineno)d] %(message)s"))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)),
            debug=app.config.get("DEBUG", False))

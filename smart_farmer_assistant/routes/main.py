"""Public pages and language switching."""
from flask import (Blueprint, current_app, redirect, render_template, request,
                   session, url_for, jsonify)
from flask_login import current_user

from extensions import db
from models.models import GovernmentScheme, User

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard" if current_user.is_admin
                                else "dashboard.home"))
    stats = {
        "farmers": User.query.filter_by(role="farmer").count(),
        "schemes": GovernmentScheme.query.filter_by(is_active=True).count(),
        "languages": len(current_app.config["SUPPORTED_LANGUAGES"]),
    }
    return render_template("index.html", stats=stats)


@main_bp.route("/set-language/<lang>")
def set_language(lang):
    if lang in current_app.config["SUPPORTED_LANGUAGES"]:
        session["lang"] = lang
        if current_user.is_authenticated and current_user.profile:
            current_user.profile.preferred_language = lang
            db.session.commit()
    return redirect(request.referrer or url_for("main.index"))


@main_bp.route("/healthz")
def healthz():
    """Health probe for Render / Railway / ECS load balancers."""
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "ok"}), 200
    except Exception as exc:
        return jsonify({"status": "degraded", "detail": str(exc)}), 503

"""Farmer dashboard, profile management and notification centre."""
from datetime import datetime, timedelta

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_required

from extensions import db
from models.models import (ChatbotHistory, CropCalendar, DiseasePrediction,
                           GovernmentScheme, Notification, PestPrediction,
                           WeatherLog, YieldPrediction)
from services import notification_service
from services.knowledge_base import CROPS, DISTRICTS, SOIL_TYPES, STATES
from services.market_service import top_movers
from services.weather_service import build_weather_alerts, get_weather
from utils.validators import clean_text, save_upload, to_float

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def home():
    profile = current_user.profile

    # --- Weather (profile location, cached into weather_logs) --------------
    weather = get_weather(lat=profile.latitude if profile else None,
                          lon=profile.longitude if profile else None,
                          city=(profile.district or profile.state) if profile else None)
    _log_weather(weather)

    alerts = build_weather_alerts(weather)
    notification_service.refresh_for_user(current_user, weather)

    # --- Stats ------------------------------------------------------------
    stats = {
        "diseases": DiseasePrediction.query.filter_by(user_id=current_user.id).count(),
        "pests": PestPrediction.query.filter_by(user_id=current_user.id).count(),
        "chats": ChatbotHistory.query.filter_by(user_id=current_user.id).count(),
        "yields": YieldPrediction.query.filter_by(user_id=current_user.id).count(),
        "farm_size": profile.farm_size if profile else 0,
        "crops": len(profile.crop_list) if profile else 0,
    }

    recent_diseases = (DiseasePrediction.query
                       .filter_by(user_id=current_user.id)
                       .order_by(DiseasePrediction.created_at.desc()).limit(4).all())

    schemes = (GovernmentScheme.query
               .filter(GovernmentScheme.is_active.is_(True))
               .filter((GovernmentScheme.scheme_type == "central") |
                       (GovernmentScheme.state == (profile.state if profile else None)))
               .order_by(GovernmentScheme.id.desc()).limit(3).all())

    calendar_rows = []
    if profile and profile.state:
        crops = profile.crop_list or []
        q = CropCalendar.query.filter(CropCalendar.state == profile.state)
        if crops:
            q = q.filter(CropCalendar.crop.in_(crops))
        calendar_rows = q.limit(4).all()

    notifications = (Notification.query.filter_by(user_id=current_user.id)
                     .order_by(Notification.created_at.desc()).limit(6).all())

    # Chart series: last 14 days of logged temperature/humidity for this user
    since = datetime.utcnow() - timedelta(days=14)
    logs = (WeatherLog.query.filter(WeatherLog.user_id == current_user.id,
                                    WeatherLog.recorded_at >= since)
            .order_by(WeatherLog.recorded_at).all())

    return render_template(
        "dashboard/home.html",
        weather=weather, alerts=alerts, stats=stats, schemes=schemes,
        recent_diseases=recent_diseases, calendar_rows=calendar_rows,
        notifications=notifications, prices=top_movers(6),
        weather_history={
            "labels": [l.recorded_at.strftime("%d %b %H:%M") for l in logs],
            "temperature": [l.temperature for l in logs],
            "humidity": [l.humidity for l in logs],
        },
    )


def _log_weather(bundle):
    """Persist one weather snapshot per user per hour."""
    cutoff = datetime.utcnow() - timedelta(hours=1)
    recent = WeatherLog.query.filter(WeatherLog.user_id == current_user.id,
                                     WeatherLog.recorded_at >= cutoff).first()
    if recent:
        return
    cur = bundle["current"]
    db.session.add(WeatherLog(
        user_id=current_user.id, city=bundle["location"],
        temperature=cur["temperature"], humidity=cur["humidity"],
        wind_speed=cur["wind_speed"], pressure=cur["pressure"],
        rain_probability=cur["rain_probability"], condition=cur["condition"]))
    db.session.commit()


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
@dashboard_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    prof = current_user.profile
    if prof is None:
        from models.models import Profile
        prof = Profile(user_id=current_user.id)
        db.session.add(prof)
        db.session.commit()

    if request.method == "POST":
        current_user.name = clean_text(request.form.get("name"), 120) or current_user.name
        prof.state = clean_text(request.form.get("state"), 80)
        prof.district = clean_text(request.form.get("district"), 80)
        prof.village = clean_text(request.form.get("village"), 120)
        prof.farm_size = to_float(request.form.get("farm_size"), 0, 0, 100000)
        prof.soil_type = clean_text(request.form.get("soil_type"), 60)
        prof.crops_grown = ", ".join(clean_text(c, 40) for c in request.form.getlist("crops_grown"))
        prof.preferred_language = (request.form.get("preferred_language") or "en")[:5]
        prof.latitude = to_float(request.form.get("latitude"), None, -90, 90) or None
        prof.longitude = to_float(request.form.get("longitude"), None, -180, 180) or None

        avatar = request.files.get("avatar")
        if avatar and avatar.filename:
            try:
                prof.avatar = save_upload(avatar, "avatars")
            except ValueError as exc:
                flash(str(exc), "danger")

        db.session.commit()
        session["lang"] = prof.preferred_language
        flash("Profile updated successfully.", "success")
        return redirect(url_for("dashboard.profile"))

    return render_template("dashboard/profile.html", profile=prof, states=STATES,
                           districts=DISTRICTS, crops=CROPS, soils=SOIL_TYPES)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
@dashboard_bp.route("/notifications")
@login_required
def notifications():
    page = request.args.get("page", 1, type=int)
    items = (Notification.query.filter_by(user_id=current_user.id)
             .order_by(Notification.created_at.desc())
             .paginate(page=page, per_page=15, error_out=False))
    return render_template("dashboard/notifications.html", items=items)


@dashboard_bp.post("/notifications/read-all")
@login_required
def read_all():
    count = notification_service.mark_all_read(current_user.id)
    return jsonify({"success": True, "marked": count})


@dashboard_bp.post("/notifications/<int:nid>/read")
@login_required
def read_one(nid):
    note = Notification.query.filter_by(id=nid, user_id=current_user.id).first_or_404()
    note.is_read = True
    db.session.commit()
    return jsonify({"success": True})


@dashboard_bp.route("/history")
@login_required
def history():
    """Combined AI prediction history for the signed-in farmer."""
    return render_template(
        "dashboard/history.html",
        diseases=(DiseasePrediction.query.filter_by(user_id=current_user.id)
                  .order_by(DiseasePrediction.created_at.desc()).limit(30).all()),
        pests=(PestPrediction.query.filter_by(user_id=current_user.id)
               .order_by(PestPrediction.created_at.desc()).limit(30).all()),
        yields=(YieldPrediction.query.filter_by(user_id=current_user.id)
                .order_by(YieldPrediction.created_at.desc()).limit(30).all()),
    )

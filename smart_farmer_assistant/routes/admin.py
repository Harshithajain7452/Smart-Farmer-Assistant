"""Admin panel — users, content management and analytics."""
from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from extensions import db
from models.models import (ChatbotHistory, CropCalendar, DiseasePrediction,
                           GovernmentScheme, MarketPrice, PestPrediction,
                           Profile, SoilInformation, User)
from services.knowledge_base import CROPS, SEASONS, SOIL_TYPES, STATES
from services.ml_service import model_status
from utils.decorators import admin_required
from utils.validators import clean_text, to_float

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@admin_required
def dashboard():
    since = datetime.utcnow() - timedelta(days=30)
    signups = (db.session.query(func.date(User.created_at), func.count(User.id))
               .filter(User.created_at >= since)
               .group_by(func.date(User.created_at)).all())
    intents = (db.session.query(ChatbotHistory.intent, func.count(ChatbotHistory.id))
               .group_by(ChatbotHistory.intent)
               .order_by(func.count(ChatbotHistory.id).desc()).limit(8).all())
    top_diseases = (db.session.query(DiseasePrediction.disease_name,
                                     func.count(DiseasePrediction.id))
                    .group_by(DiseasePrediction.disease_name)
                    .order_by(func.count(DiseasePrediction.id).desc()).limit(6).all())
    states = (db.session.query(Profile.state, func.count(Profile.id))
              .filter(Profile.state.isnot(None), Profile.state != "")
              .group_by(Profile.state)
              .order_by(func.count(Profile.id).desc()).limit(8).all())

    stats = {
        "users": User.query.count(),
        "farmers": User.query.filter_by(role="farmer").count(),
        "diseases": DiseasePrediction.query.count(),
        "pests": PestPrediction.query.count(),
        "chats": ChatbotHistory.query.count(),
        "schemes": GovernmentScheme.query.count(),
        "prices": MarketPrice.query.count(),
    }
    return render_template(
        "admin/dashboard.html", stats=stats, models=model_status(),
        signups={"labels": [str(s[0]) for s in signups], "values": [s[1] for s in signups]},
        intents={"labels": [i[0] or "unknown" for i in intents],
                 "values": [i[1] for i in intents]},
        diseases={"labels": [d[0] for d in top_diseases],
                  "values": [d[1] for d in top_diseases]},
        states={"labels": [s[0] for s in states], "values": [s[1] for s in states]},
        recent_users=User.query.order_by(User.created_at.desc()).limit(6).all())


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@admin_bp.route("/users")
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    search = clean_text(request.args.get("q"), 80)
    q = User.query
    if search:
        q = q.filter((User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%")))
    items = q.order_by(User.created_at.desc()).paginate(page=page, per_page=15,
                                                        error_out=False)
    return render_template("admin/users.html", items=items, q=search)


@admin_bp.post("/users/<int:uid>/toggle")
@admin_required
def toggle_user(uid):
    user = User.query.get_or_404(uid)
    if user.is_admin:
        flash("Administrator accounts cannot be deactivated here.", "warning")
    else:
        user.is_active_flag = not user.is_active_flag
        db.session.commit()
        flash(f"{user.name} is now {'active' if user.is_active_flag else 'inactive'}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.post("/users/<int:uid>/delete")
@admin_required
def delete_user(uid):
    user = User.query.get_or_404(uid)
    if user.is_admin:
        flash("Administrator accounts cannot be deleted.", "warning")
    else:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.", "success")
    return redirect(url_for("admin.users"))


# ---------------------------------------------------------------------------
# Government schemes
# ---------------------------------------------------------------------------
@admin_bp.route("/schemes", methods=["GET", "POST"])
@admin_required
def schemes():
    if request.method == "POST":
        sid = request.form.get("id", type=int)
        scheme = GovernmentScheme.query.get(sid) if sid else GovernmentScheme()
        scheme.name = clean_text(request.form.get("name"), 200)
        scheme.scheme_type = request.form.get("scheme_type", "central")
        scheme.state = clean_text(request.form.get("state"), 80) or None
        scheme.description = clean_text(request.form.get("description"), 4000)
        scheme.eligibility = clean_text(request.form.get("eligibility"), 4000)
        scheme.benefits = clean_text(request.form.get("benefits"), 4000)
        scheme.documents = clean_text(request.form.get("documents"), 2000)
        scheme.application_process = clean_text(request.form.get("application_process"), 4000)
        scheme.website = clean_text(request.form.get("website"), 255)
        scheme.is_active = bool(request.form.get("is_active"))
        if not sid:
            db.session.add(scheme)
        db.session.commit()
        flash("Scheme saved.", "success")
        return redirect(url_for("admin.schemes"))

    return render_template("admin/schemes.html", states=STATES,
                           items=GovernmentScheme.query.order_by(GovernmentScheme.name).all())


@admin_bp.post("/schemes/<int:sid>/delete")
@admin_required
def delete_scheme(sid):
    db.session.delete(GovernmentScheme.query.get_or_404(sid))
    db.session.commit()
    flash("Scheme deleted.", "success")
    return redirect(url_for("admin.schemes"))


# ---------------------------------------------------------------------------
# Soil information
# ---------------------------------------------------------------------------
@admin_bp.route("/soil", methods=["GET", "POST"])
@admin_required
def soil():
    if request.method == "POST":
        sid = request.form.get("id", type=int)
        row = SoilInformation.query.get(sid) if sid else SoilInformation()
        row.soil_type = clean_text(request.form.get("soil_type"), 60)
        row.description = clean_text(request.form.get("description"), 3000)
        row.nutrients = clean_text(request.form.get("nutrients"), 1500)
        row.advantages = clean_text(request.form.get("advantages"), 1500)
        row.limitations = clean_text(request.form.get("limitations"), 1500)
        row.suitable_crops = clean_text(request.form.get("suitable_crops"), 1000)
        row.fertilizer_recommendation = clean_text(
            request.form.get("fertilizer_recommendation"), 1500)
        row.irrigation_recommendation = clean_text(
            request.form.get("irrigation_recommendation"), 1500)
        row.regions = clean_text(request.form.get("regions"), 1000)
        if not sid:
            db.session.add(row)
        db.session.commit()
        flash("Soil record saved.", "success")
        return redirect(url_for("admin.soil"))

    return render_template("admin/soil.html", soil_types=SOIL_TYPES,
                           items=SoilInformation.query.order_by(
                               SoilInformation.soil_type).all())


# ---------------------------------------------------------------------------
# Crop calendar
# ---------------------------------------------------------------------------
@admin_bp.route("/calendar", methods=["GET", "POST"])
@admin_required
def calendar():
    if request.method == "POST":
        cid = request.form.get("id", type=int)
        row = CropCalendar.query.get(cid) if cid else CropCalendar()
        row.crop = clean_text(request.form.get("crop"), 80)
        row.state = clean_text(request.form.get("state"), 80)
        row.season = clean_text(request.form.get("season"), 40)
        row.sowing_time = clean_text(request.form.get("sowing_time"), 120)
        row.planting_time = clean_text(request.form.get("planting_time"), 120)
        row.irrigation_schedule = clean_text(request.form.get("irrigation_schedule"), 2000)
        row.fertilizer_schedule = clean_text(request.form.get("fertilizer_schedule"), 2000)
        row.harvesting_time = clean_text(request.form.get("harvesting_time"), 120)
        row.duration_days = int(to_float(request.form.get("duration_days"), 120, 20, 500))
        row.notes = clean_text(request.form.get("notes"), 2000)
        if not cid:
            db.session.add(row)
        db.session.commit()
        flash("Calendar entry saved.", "success")
        return redirect(url_for("admin.calendar"))

    return render_template("admin/calendar.html", states=STATES, crops=CROPS,
                           seasons=SEASONS,
                           items=CropCalendar.query.order_by(CropCalendar.state,
                                                             CropCalendar.crop).all())


# ---------------------------------------------------------------------------
# Market prices
# ---------------------------------------------------------------------------
@admin_bp.route("/prices", methods=["GET", "POST"])
@admin_required
def prices():
    if request.method == "POST":
        row = MarketPrice(
            state=clean_text(request.form.get("state"), 80),
            district=clean_text(request.form.get("district"), 80),
            market=clean_text(request.form.get("market"), 120),
            crop=clean_text(request.form.get("crop"), 80),
            variety=clean_text(request.form.get("variety"), 80),
            min_price=to_float(request.form.get("min_price"), 0, 0, 1000000),
            max_price=to_float(request.form.get("max_price"), 0, 0, 1000000),
            modal_price=to_float(request.form.get("modal_price"), 0, 0, 1000000),
            price_date=datetime.strptime(
                request.form.get("price_date") or date.today().isoformat(),
                "%Y-%m-%d").date())
        db.session.add(row)
        db.session.commit()
        flash("Price record added.", "success")
        return redirect(url_for("admin.prices"))

    page = request.args.get("page", 1, type=int)
    items = (MarketPrice.query.order_by(MarketPrice.price_date.desc())
             .paginate(page=page, per_page=20, error_out=False))
    return render_template("admin/prices.html", items=items, states=STATES, crops=CROPS,
                           today=date.today().isoformat())


# ---------------------------------------------------------------------------
# Records & analytics
# ---------------------------------------------------------------------------
@admin_bp.route("/detections")
@admin_required
def detections():
    page = request.args.get("page", 1, type=int)
    items = (DiseasePrediction.query.order_by(DiseasePrediction.created_at.desc())
             .paginate(page=page, per_page=20, error_out=False))
    pests = (PestPrediction.query.order_by(PestPrediction.created_at.desc()).limit(20).all())
    return render_template("admin/detections.html", items=items, pests=pests)


@admin_bp.route("/chat-analytics")
@admin_required
def chat_analytics():
    rows = (db.session.query(ChatbotHistory.intent, func.count(ChatbotHistory.id))
            .group_by(ChatbotHistory.intent)
            .order_by(func.count(ChatbotHistory.id).desc()).all())
    recent = (ChatbotHistory.query.order_by(ChatbotHistory.created_at.desc())
              .limit(30).all())
    return render_template("admin/chat_analytics.html", recent=recent,
                           chart={"labels": [r[0] or "unknown" for r in rows],
                                  "values": [r[1] for r in rows]},
                           total=sum(r[1] for r in rows))

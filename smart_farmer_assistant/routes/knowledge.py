"""Government schemes, soil information and the crop calendar."""
from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from models.models import CropCalendar, GovernmentScheme, SoilInformation
from services.knowledge_base import CROPS, SEASONS, STATES
from utils.validators import clean_text

knowledge_bp = Blueprint("knowledge", __name__)


@knowledge_bp.route("/schemes")
@login_required
def schemes():
    state = clean_text(request.args.get("state"), 80)
    stype = clean_text(request.args.get("type"), 20)
    search = clean_text(request.args.get("q"), 80)

    q = GovernmentScheme.query.filter(GovernmentScheme.is_active.is_(True))
    if stype in ("central", "state"):
        q = q.filter(GovernmentScheme.scheme_type == stype)
    if state:
        q = q.filter((GovernmentScheme.state == state) |
                     (GovernmentScheme.scheme_type == "central"))
    if search:
        q = q.filter(GovernmentScheme.name.ilike(f"%{search}%"))

    items = q.order_by(GovernmentScheme.scheme_type, GovernmentScheme.name).all()
    return render_template("modules/schemes.html", items=items, states=STATES,
                           sel={"state": state, "type": stype, "q": search})


@knowledge_bp.route("/soil")
@login_required
def soil():
    selected = clean_text(request.args.get("soil_type"), 60)
    if not selected and current_user.profile:
        selected = current_user.profile.soil_type
    soils = SoilInformation.query.order_by(SoilInformation.soil_type).all()
    active = next((s for s in soils if s.soil_type == selected), soils[0] if soils else None)
    return render_template("modules/soil.html", soils=soils, active=active)


@knowledge_bp.route("/calendar")
@login_required
def calendar():
    profile = current_user.profile
    state = clean_text(request.args.get("state"), 80) or (profile.state if profile else "Bihar")
    crop = clean_text(request.args.get("crop"), 80)

    q = CropCalendar.query.filter(CropCalendar.state == state)
    if crop:
        q = q.filter(CropCalendar.crop == crop)
    rows = q.order_by(CropCalendar.season, CropCalendar.crop).all()
    return render_template("modules/calendar.html", rows=rows, states=STATES, crops=CROPS,
                           seasons=SEASONS, sel={"state": state, "crop": crop})

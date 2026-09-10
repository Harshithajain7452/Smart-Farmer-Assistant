"""
Versioned REST API (``/api/v1``).

Consumed by the dashboard JavaScript and available for the future mobile app.
All endpoints require an authenticated session; CSRF is exempted for the JSON
endpoints because they are same-origin and session-scoped.
"""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from models.models import GovernmentScheme, MarketPrice, Notification
from services import ml_service
from services.geo_service import nearby_markets
from services.knowledge_base import CROPS, DISTRICTS, SOIL_TYPES, STATES
from services.market_service import price_trend
from services.weather_service import build_weather_alerts, get_weather
from utils.validators import clean_text, to_float

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.get("/meta")
def meta():
    """Dropdown reference data (states, districts, crops, soils)."""
    return jsonify({"states": STATES, "districts": DISTRICTS,
                    "crops": CROPS, "soil_types": SOIL_TYPES})


@api_bp.get("/districts/<state>")
def districts(state):
    return jsonify({"districts": DISTRICTS.get(state, [])})


@api_bp.get("/weather")
@login_required
def weather():
    lat = to_float(request.args.get("lat"), None, -90, 90)
    lon = to_float(request.args.get("lon"), None, -180, 180)
    city = clean_text(request.args.get("city"), 80)
    bundle = get_weather(lat=lat, lon=lon, city=city)
    bundle["alerts"] = [{"severity": s, "title": t, "body": b}
                        for s, t, b in build_weather_alerts(bundle)]
    return jsonify(bundle)


@api_bp.get("/markets/nearby")
@login_required
def markets_nearby():
    lat = to_float(request.args.get("lat"), None, -90, 90)
    lon = to_float(request.args.get("lon"), None, -180, 180)
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400
    radius = to_float(request.args.get("radius"), 250, 5, 1000)
    return jsonify({"markets": nearby_markets(lat, lon, radius)})


@api_bp.get("/prices")
@login_required
def prices():
    q = MarketPrice.query
    for field, column in (("state", MarketPrice.state), ("district", MarketPrice.district),
                          ("crop", MarketPrice.crop)):
        value = clean_text(request.args.get(field), 80)
        if value:
            q = q.filter(column == value)
    rows = q.order_by(MarketPrice.price_date.desc()).limit(100).all()
    return jsonify({"count": len(rows), "prices": [
        {"state": r.state, "district": r.district, "market": r.market, "crop": r.crop,
         "min_price": r.min_price, "max_price": r.max_price, "modal_price": r.modal_price,
         "date": r.price_date.isoformat()} for r in rows]})


@api_bp.get("/prices/trend")
@login_required
def prices_trend():
    crop = clean_text(request.args.get("crop"), 80) or "Rice"
    state = clean_text(request.args.get("state"), 80) or None
    return jsonify(price_trend(crop, state))


@api_bp.get("/schemes")
@login_required
def schemes():
    q = GovernmentScheme.query.filter(GovernmentScheme.is_active.is_(True))
    state = clean_text(request.args.get("state"), 80)
    if state:
        q = q.filter((GovernmentScheme.state == state) |
                     (GovernmentScheme.scheme_type == "central"))
    return jsonify({"schemes": [
        {"id": s.id, "name": s.name, "type": s.scheme_type, "state": s.state,
         "description": s.description, "eligibility": s.eligibility,
         "benefits": s.benefits, "documents": s.documents,
         "process": s.application_process, "website": s.website}
        for s in q.all()]})


@api_bp.post("/predict/crop")
@login_required
def predict_crop():
    d = request.get_json(silent=True) or {}
    return jsonify(ml_service.recommend_crop(
        clean_text(d.get("soil_type"), 60) or "Alluvial",
        to_float(d.get("temperature"), 27, -5, 55),
        to_float(d.get("humidity"), 70, 0, 100),
        to_float(d.get("rainfall"), 150, 0, 5000),
        to_float(d.get("ph"), 6.5, 3, 10)))


@api_bp.post("/predict/fertilizer")
@login_required
def predict_fertilizer():
    d = request.get_json(silent=True) or {}
    return jsonify(ml_service.recommend_fertilizer(
        clean_text(d.get("crop"), 80) or "Wheat",
        clean_text(d.get("soil_type"), 60) or "Alluvial",
        to_float(d.get("nitrogen"), 40, 0, 300),
        to_float(d.get("phosphorus"), 30, 0, 300),
        to_float(d.get("potassium"), 30, 0, 300)))


@api_bp.post("/predict/yield")
@login_required
def predict_yield():
    d = request.get_json(silent=True) or {}
    return jsonify(ml_service.predict_yield(
        clean_text(d.get("crop"), 80) or "Rice",
        to_float(d.get("area"), 1, 0.1, 10000),
        to_float(d.get("rainfall"), 180, 0, 5000),
        to_float(d.get("temperature"), 28, -5, 55),
        to_float(d.get("fertilizer"), 90, 0, 1000)))


@api_bp.get("/notifications")
@login_required
def notifications():
    rows = (Notification.query.filter_by(user_id=current_user.id)
            .order_by(Notification.created_at.desc()).limit(20).all())
    return jsonify({"unread": sum(1 for r in rows if not r.is_read), "items": [
        {"id": r.id, "title": r.title, "body": r.body, "category": r.category,
         "severity": r.severity, "is_read": r.is_read,
         "created_at": r.created_at.isoformat()} for r in rows]})

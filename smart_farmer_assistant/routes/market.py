"""Mandi price system and nearby market finder."""
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from services.geo_service import MARKETS, nearby_markets
from services.knowledge_base import CROPS, DISTRICTS, STATES
from services.market_service import fetch_live_prices, price_trend, query_prices
from utils.validators import clean_text, to_float

market_bp = Blueprint("market", __name__)


@market_bp.route("/market-prices")
@login_required
def prices():
    profile = current_user.profile
    state = clean_text(request.args.get("state"), 80) or (profile.state if profile else "Bihar")
    district = clean_text(request.args.get("district"), 80)
    crop = clean_text(request.args.get("crop"), 80) or "Rice"

    live = fetch_live_prices(state, district, crop)
    rows = query_prices(state, district or None, crop)
    trend = price_trend(crop, state)

    return render_template("modules/prices.html", rows=rows, live=live, trend=trend,
                           states=STATES, districts=DISTRICTS, crops=CROPS,
                           sel={"state": state, "district": district, "crop": crop})


@market_bp.route("/nearby-markets")
@login_required
def nearby():
    return render_template("modules/nearby.html", all_markets=MARKETS)


@market_bp.get("/api/nearby-markets")
@login_required
def nearby_api():
    """Called by the browser Geolocation API from the map page."""
    lat = to_float(request.args.get("lat"), None, -90, 90)
    lon = to_float(request.args.get("lon"), None, -180, 180)
    radius = to_float(request.args.get("radius"), 250, 5, 1000)
    if lat is None or lon is None:
        return jsonify({"success": False, "error": "Latitude and longitude are required."}), 400
    return jsonify({"success": True, "markets": nearby_markets(lat, lon, radius)})

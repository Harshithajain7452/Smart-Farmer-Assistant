"""Live weather forecast module."""
from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from services.weather_service import build_weather_alerts, get_weather
from utils.validators import clean_text, to_float

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/weather")
@login_required
def forecast():
    profile = current_user.profile
    city = clean_text(request.args.get("city"), 80) or (
        profile.district or profile.state if profile else None)
    lat = to_float(request.args.get("lat"), None, -90, 90)
    lon = to_float(request.args.get("lon"), None, -180, 180)
    if request.args.get("city"):
        lat = lon = None
    elif lat is None or lon is None:
        lat = profile.latitude if profile else None
        lon = profile.longitude if profile else None

    bundle = get_weather(lat=lat, lon=lon, city=city)
    return render_template("modules/weather.html", w=bundle,
                           alerts=build_weather_alerts(bundle), city=city)

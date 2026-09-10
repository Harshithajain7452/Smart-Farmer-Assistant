"""
OpenWeatherMap integration.

Provides current conditions, hourly forecast and a 7-day outlook. When no API
key is configured (or the network call fails) the service returns a clearly
flagged deterministic sample so the dashboard and charts still render.
"""
from datetime import datetime, timedelta, timezone

import requests
from flask import current_app

TIMEOUT = 8
IST = timezone(timedelta(hours=5, minutes=30))


def _key() -> str:
    return current_app.config.get("OPENWEATHER_API_KEY", "")


def geocode(city: str):
    """City name -> (lat, lon, display name)."""
    if not _key():
        return None
    url = f"{current_app.config['OPENWEATHER_GEO_URL']}/direct"
    try:
        res = requests.get(url, params={"q": f"{city},IN", "limit": 1, "appid": _key()},
                           timeout=TIMEOUT)
        res.raise_for_status()
        data = res.json()
        if data:
            return data[0]["lat"], data[0]["lon"], data[0]["name"]
    except requests.RequestException as exc:
        current_app.logger.warning("Geocoding failed: %s", exc)
    return None


def get_weather(lat: float = None, lon: float = None, city: str = None) -> dict:
    """
    Return a normalised weather bundle:
    ``{current, hourly[], daily[], location, is_sample}``
    """
    if not _key():
        return _sample_bundle(city or "Your farm")

    if lat is None or lon is None:
        geo = geocode(city or "Patna")
        if not geo:
            return _sample_bundle(city or "Your farm")
        lat, lon, city = geo

    base = current_app.config["OPENWEATHER_BASE_URL"]
    params = {"lat": lat, "lon": lon, "appid": _key(), "units": "metric"}
    try:
        current = requests.get(f"{base}/weather", params=params, timeout=TIMEOUT)
        current.raise_for_status()
        forecast = requests.get(f"{base}/forecast", params=params, timeout=TIMEOUT)
        forecast.raise_for_status()
        return _normalise(current.json(), forecast.json())
    except requests.RequestException as exc:
        current_app.logger.warning("Weather API error: %s", exc)
        return _sample_bundle(city or "Your farm")


def _normalise(cur: dict, fc: dict) -> dict:
    weather = (cur.get("weather") or [{}])[0]
    sys = cur.get("sys", {})
    entries = fc.get("list", [])

    hourly = [
        {
            "time": datetime.fromtimestamp(e["dt"], IST).strftime("%d %b %H:%M"),
            "hour": datetime.fromtimestamp(e["dt"], IST).strftime("%H:%M"),
            "temp": round(e["main"]["temp"], 1),
            "humidity": e["main"]["humidity"],
            "rain_probability": round(e.get("pop", 0) * 100),
            "icon": (e.get("weather") or [{}])[0].get("icon", "01d"),
            "condition": (e.get("weather") or [{}])[0].get("description", "").title(),
        }
        for e in entries[:16]
    ]

    # Aggregate 3-hourly entries into daily min/max for the 7-day outlook.
    buckets = {}
    for e in entries:
        day = datetime.fromtimestamp(e["dt"], IST).strftime("%Y-%m-%d")
        b = buckets.setdefault(day, {"temps": [], "pops": [], "icons": [], "conds": []})
        b["temps"].append(e["main"]["temp"])
        b["pops"].append(e.get("pop", 0))
        b["icons"].append((e.get("weather") or [{}])[0].get("icon", "01d"))
        b["conds"].append((e.get("weather") or [{}])[0].get("main", ""))

    daily = [
        {
            "date": datetime.strptime(day, "%Y-%m-%d").strftime("%a, %d %b"),
            "min": round(min(b["temps"]), 1),
            "max": round(max(b["temps"]), 1),
            "rain_probability": round(max(b["pops"]) * 100),
            "icon": max(set(b["icons"]), key=b["icons"].count),
            "condition": max(set(b["conds"]), key=b["conds"].count),
        }
        for day, b in list(buckets.items())[:7]
    ]

    return {
        "is_sample": False,
        "location": cur.get("name", "Your farm"),
        "current": {
            "temperature": round(cur["main"]["temp"], 1),
            "feels_like": round(cur["main"]["feels_like"], 1),
            "humidity": cur["main"]["humidity"],
            "pressure": cur["main"]["pressure"],
            "wind_speed": round(cur.get("wind", {}).get("speed", 0) * 3.6, 1),  # km/h
            "wind_deg": cur.get("wind", {}).get("deg", 0),
            "clouds": cur.get("clouds", {}).get("all", 0),
            "visibility": round(cur.get("visibility", 0) / 1000, 1),
            "condition": weather.get("description", "").title(),
            "icon": weather.get("icon", "01d"),
            "rain_probability": hourly[0]["rain_probability"] if hourly else 0,
            "sunrise": datetime.fromtimestamp(sys.get("sunrise", 0), IST).strftime("%H:%M"),
            "sunset": datetime.fromtimestamp(sys.get("sunset", 0), IST).strftime("%H:%M"),
        },
        "hourly": hourly,
        "daily": daily,
    }


def _sample_bundle(location: str) -> dict:
    """Offline demo data — flagged with ``is_sample`` so the UI can say so."""
    now = datetime.now(IST)
    hourly = []
    for i in range(16):
        t = now + timedelta(hours=3 * i)
        hourly.append({
            "time": t.strftime("%d %b %H:%M"),
            "hour": t.strftime("%H:%M"),
            "temp": round(28 + 4 * ((i % 8) / 8) - (2 if t.hour < 7 else 0), 1),
            "humidity": 58 + (i * 3) % 30,
            "rain_probability": (i * 13) % 70,
            "icon": "10d" if (i * 13) % 70 > 45 else "01d",
            "condition": "Light Rain" if (i * 13) % 70 > 45 else "Clear Sky",
        })
    daily = []
    for i in range(7):
        d = now + timedelta(days=i)
        daily.append({
            "date": d.strftime("%a, %d %b"),
            "min": round(23 + (i % 3), 1),
            "max": round(32 + (i % 4), 1),
            "rain_probability": (i * 17) % 80,
            "icon": "10d" if (i * 17) % 80 > 45 else "02d",
            "condition": "Rain" if (i * 17) % 80 > 45 else "Clouds",
        })
    return {
        "is_sample": True,
        "location": location,
        "current": {
            "temperature": 29.4, "feels_like": 33.1, "humidity": 71, "pressure": 1004,
            "wind_speed": 11.5, "wind_deg": 120, "clouds": 40, "visibility": 8.0,
            "condition": "Scattered Clouds", "icon": "03d", "rain_probability": 35,
            "sunrise": "05:42", "sunset": "18:21",
        },
        "hourly": hourly,
        "daily": daily,
    }


def build_weather_alerts(bundle: dict) -> list:
    """Derive farmer-facing advisories from the forecast bundle."""
    alerts = []
    cur = bundle["current"]
    if cur["temperature"] >= 40:
        alerts.append(("danger", "Heat wave warning",
                       "Temperature above 40 °C. Irrigate in the early morning or late evening "
                       "and mulch to conserve soil moisture."))
    elif cur["temperature"] >= 36:
        alerts.append(("warning", "High temperature",
                       "Provide light frequent irrigation and avoid mid-day spraying."))
    if cur["temperature"] <= 6:
        alerts.append(("warning", "Cold wave / frost risk",
                       "Irrigate in the evening and use smoke or sprinklers to protect nurseries."))
    heavy = [d for d in bundle["daily"] if d["rain_probability"] >= 70]
    if heavy:
        alerts.append(("warning", "Heavy rain expected",
                       f"High rain probability on {heavy[0]['date']}. Postpone fertiliser "
                       "application and spraying, and clear field drainage channels."))
    if cur["humidity"] >= 85:
        alerts.append(("info", "High humidity — disease risk",
                       "Conditions favour blight and blast. Scout fields and keep a protective "
                       "fungicide ready."))
    if cur["wind_speed"] >= 35:
        alerts.append(("warning", "Strong winds",
                       "Stake tall crops and delay spraying to prevent drift."))
    return alerts

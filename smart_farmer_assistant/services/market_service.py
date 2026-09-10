"""
Mandi (agricultural market) price service.

Primary source: the Government of India open-data mandi price resource
(data.gov.in, resource 9ef84268-d588-465a-a308-a864a43d0070). When no API key
is present the service falls back to the ``market_prices`` table which is
seeded with realistic reference data and maintained from the admin panel.
"""
from datetime import date, timedelta

import requests
from flask import current_app
from sqlalchemy import func

from extensions import db
from models.models import MarketPrice

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
TIMEOUT = 10


def fetch_live_prices(state: str, district: str = None, crop: str = None, limit: int = 40):
    """Query data.gov.in; returns [] when the key is missing or the call fails."""
    api_key = current_app.config.get("DATA_GOV_IN_API_KEY")
    if not api_key:
        return []
    params = {
        "api-key": api_key, "format": "json", "limit": limit,
        "filters[state]": state,
    }
    if district:
        params["filters[district]"] = district
    if crop:
        params["filters[commodity]"] = crop
    try:
        res = requests.get(f"https://api.data.gov.in/resource/{RESOURCE_ID}",
                           params=params, timeout=TIMEOUT)
        res.raise_for_status()
        records = res.json().get("records", [])
    except (requests.RequestException, ValueError) as exc:
        current_app.logger.warning("Mandi price API error: %s", exc)
        return []

    out = []
    for r in records:
        try:
            out.append({
                "state": r.get("state"), "district": r.get("district"),
                "market": r.get("market"), "crop": r.get("commodity"),
                "variety": r.get("variety"),
                "min_price": float(r.get("min_price", 0)),
                "max_price": float(r.get("max_price", 0)),
                "modal_price": float(r.get("modal_price", 0)),
                "price_date": r.get("arrival_date"),
                "source": "data.gov.in",
            })
        except (TypeError, ValueError):
            continue
    return out


def query_prices(state=None, district=None, crop=None, limit=60):
    """Parameterised ORM query (no string SQL — immune to SQL injection)."""
    q = MarketPrice.query
    if state:
        q = q.filter(MarketPrice.state == state)
    if district:
        q = q.filter(MarketPrice.district == district)
    if crop:
        q = q.filter(MarketPrice.crop == crop)
    return q.order_by(MarketPrice.price_date.desc()).limit(limit).all()


def price_trend(crop: str, state: str = None, days: int = 30):
    """Return ``{labels, modal, min, max}`` series for Chart.js."""
    since = date.today() - timedelta(days=days)
    q = (db.session.query(
            MarketPrice.price_date,
            func.avg(MarketPrice.modal_price),
            func.avg(MarketPrice.min_price),
            func.avg(MarketPrice.max_price))
         .filter(MarketPrice.crop == crop, MarketPrice.price_date >= since))
    if state:
        q = q.filter(MarketPrice.state == state)
    rows = q.group_by(MarketPrice.price_date).order_by(MarketPrice.price_date).all()
    return {
        "labels": [r[0].strftime("%d %b") for r in rows],
        "modal": [round(float(r[1]), 2) for r in rows],
        "min": [round(float(r[2]), 2) for r in rows],
        "max": [round(float(r[3]), 2) for r in rows],
    }


def top_movers(limit: int = 5):
    """Crops with the highest average modal price in the last 7 days."""
    since = date.today() - timedelta(days=7)
    rows = (db.session.query(MarketPrice.crop, func.avg(MarketPrice.modal_price).label("p"))
            .filter(MarketPrice.price_date >= since)
            .group_by(MarketPrice.crop).order_by(db.desc("p")).limit(limit).all())
    return [{"crop": r[0], "modal_price": round(float(r[1]), 2)} for r in rows]

"""
Notification engine.

Creates and stores alerts for weather warnings, new government schemes and
market price movements. ``refresh_for_user`` is idempotent for a 12-hour window
so repeated dashboard visits do not spam the farmer.
"""
from datetime import datetime, timedelta

from extensions import db
from models.models import GovernmentScheme, MarketPrice, Notification


def push(user_id: int, title: str, body: str, category: str = "general",
         severity: str = "info", dedupe_hours: int = 12) -> bool:
    """Create a notification unless an identical one exists in the window."""
    if dedupe_hours:
        since = datetime.utcnow() - timedelta(hours=dedupe_hours)
        exists = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.title == title,
            Notification.created_at >= since,
        ).first()
        if exists:
            return False
    db.session.add(Notification(user_id=user_id, title=title, body=body,
                                category=category, severity=severity))
    db.session.commit()
    return True


def refresh_for_user(user, weather_bundle=None) -> int:
    """Generate weather / scheme / price alerts for one farmer. Returns count."""
    from services.weather_service import build_weather_alerts

    created = 0
    if weather_bundle:
        for severity, title, body in build_weather_alerts(weather_bundle):
            created += int(push(user.id, title, body, "weather", severity))

    # New schemes published in the last 7 days (central + farmer's state)
    week_ago = datetime.utcnow() - timedelta(days=7)
    state = user.profile.state if user.profile else None
    q = GovernmentScheme.query.filter(GovernmentScheme.created_at >= week_ago,
                                      GovernmentScheme.is_active.is_(True))
    for scheme in q.limit(5).all():
        if scheme.scheme_type == "state" and state and scheme.state != state:
            continue
        created += int(push(user.id, f"New scheme: {scheme.name}",
                            (scheme.description or "")[:300], "scheme", "info",
                            dedupe_hours=168))

    # Price movement for the crops the farmer grows
    if user.profile and user.profile.crop_list:
        for crop in user.profile.crop_list[:3]:
            change = price_change(crop, state)
            if change and abs(change["pct"]) >= 5:
                direction = "risen" if change["pct"] > 0 else "fallen"
                created += int(push(
                    user.id,
                    f"{crop} price {direction} {abs(change['pct'])}%",
                    f"Modal price moved from ₹{change['old']} to ₹{change['new']} per quintal "
                    f"in the last week. Review your selling plan.",
                    "price", "info" if change["pct"] > 0 else "warning",
                ))
    return created


def price_change(crop: str, state: str = None):
    """Compare the newest modal price with the price a week earlier."""
    q = MarketPrice.query.filter(MarketPrice.crop == crop)
    if state:
        q = q.filter(MarketPrice.state == state)
    rows = q.order_by(MarketPrice.price_date.desc()).limit(60).all()
    if len(rows) < 2:
        return None
    newest = rows[0]
    cutoff = newest.price_date - timedelta(days=7)
    older = next((r for r in rows if r.price_date <= cutoff), rows[-1])
    if not older.modal_price:
        return None
    pct = round((newest.modal_price - older.modal_price) / older.modal_price * 100, 1)
    return {"old": round(older.modal_price), "new": round(newest.modal_price), "pct": pct}


def unread_count(user_id: int) -> int:
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def mark_all_read(user_id: int) -> int:
    updated = Notification.query.filter_by(user_id=user_id, is_read=False).update(
        {"is_read": True}, synchronize_session=False)
    db.session.commit()
    return updated

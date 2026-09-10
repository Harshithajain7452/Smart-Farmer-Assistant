"""Database bootstrap helpers."""
from extensions import db


def init_database(app):
    """Create tables when they do not exist yet (safe on every boot)."""
    with app.app_context():
        db.create_all()


def paginate(query, page: int, per_page: int):
    """Small wrapper so blueprints don't repeat pagination boilerplate."""
    return query.paginate(page=page, per_page=per_page, error_out=False)

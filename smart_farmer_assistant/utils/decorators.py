"""Reusable route decorators."""
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(view):
    """Allow only authenticated admin users."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in as an administrator.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


def profile_required(view):
    """Ensure the farmer completed their profile before using ML modules."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated and current_user.profile is None:
            flash("Complete your farm profile to unlock personalised advice.", "info")
            return redirect(url_for("dashboard.profile"))
        return view(*args, **kwargs)
    return wrapper

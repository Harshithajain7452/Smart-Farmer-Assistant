"""Authentication blueprint: register, login, logout, forgot/reset password."""
import secrets
from datetime import datetime, timedelta

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from models.models import Profile, User
from services.knowledge_base import CROPS, DISTRICTS, SOIL_TYPES, STATES
from utils.validators import (clean_text, is_valid_email, is_valid_name,
                              is_valid_phone, password_issues, to_float)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    form = {}
    if request.method == "POST":
        form = {k: clean_text(v, 200) for k, v in request.form.items() if k != "password"}
        name = clean_text(request.form.get("name"), 120)
        email = clean_text(request.form.get("email"), 160).lower()
        phone = clean_text(request.form.get("phone"), 20)
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        errors = []

        if not is_valid_name(name):
            errors.append("Enter a valid full name.")
        if not is_valid_email(email):
            errors.append("Enter a valid email address.")
        if not is_valid_phone(phone):
            errors.append("Enter a valid 10-digit Indian mobile number.")
        issues = password_issues(password)
        if issues:
            errors.append("Password needs " + ", ".join(issues) + ".")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        if phone and User.query.filter_by(phone=phone).first():
            errors.append("This mobile number is already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            user = User(name=name, email=email, phone=phone)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # obtain user.id before creating the profile

            crops = request.form.getlist("crops_grown")
            profile = Profile(
                user_id=user.id,
                state=clean_text(request.form.get("state"), 80),
                district=clean_text(request.form.get("district"), 80),
                village=clean_text(request.form.get("village"), 120),
                farm_size=to_float(request.form.get("farm_size"), 0, 0, 100000),
                soil_type=clean_text(request.form.get("soil_type"), 60),
                crops_grown=", ".join(clean_text(c, 40) for c in crops),
                preferred_language=request.form.get("preferred_language", "en")[:5],
            )
            db.session.add(profile)
            db.session.commit()

            login_user(user)
            session["lang"] = profile.preferred_language
            flash(f"Welcome aboard, {user.name}. Your farm profile is ready.", "success")
            return redirect(url_for("dashboard.home"))

    return render_template("auth/register.html", form=form, states=STATES,
                           districts=DISTRICTS, crops=CROPS, soils=SOIL_TYPES)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        email = clean_text(request.form.get("email"), 160).lower()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash("This account has been deactivated. Contact the administrator.", "danger")
                return redirect(url_for("auth.login"))
            login_user(user, remember=remember)
            session.permanent = True
            user.last_login = datetime.utcnow()
            db.session.commit()
            if user.profile:
                session["lang"] = user.profile.preferred_language or "en"
            flash(f"Welcome back, {user.name}.", "success")
            nxt = request.args.get("next")
            # Prevent open-redirect attacks
            if nxt and nxt.startswith("/") and not nxt.startswith("//"):
                return redirect(nxt)
            return redirect(url_for("admin.dashboard" if user.is_admin else "dashboard.home"))
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("lang", None)
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Issues a single-use, 1-hour reset token.

    In production wire ``send_reset_email`` to SES/SendGrid; in development the
    link is shown on screen so the flow can be tested without a mail server.
    """
    reset_link = None
    if request.method == "POST":
        email = clean_text(request.form.get("email"), 160).lower()
        user = User.query.filter_by(email=email).first()
        if user:
            user.reset_token = secrets.token_urlsafe(32)
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            reset_link = url_for("auth.reset_password", token=user.reset_token,
                                 _external=True)
            current_app.logger.info("Password reset requested for %s", email)
        # Same message either way — prevents account enumeration.
        flash("If that email is registered, a reset link has been generated.", "info")
    return render_template("auth/forgot_password.html", reset_link=reset_link)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash("This reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        issues = password_issues(password)
        if issues:
            flash("Password needs " + ", ".join(issues) + ".", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            user.set_password(password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            flash("Password updated. Please sign in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)

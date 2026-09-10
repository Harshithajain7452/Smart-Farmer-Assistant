"""Crop disease and pest detection blueprints (CNN powered)."""
import os

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, send_from_directory, url_for, abort)
from flask_login import current_user, login_required

from extensions import db
from models.models import DiseasePrediction, PestPrediction
from services import ml_service
from utils.validators import save_upload

detection_bp = Blueprint("detection", __name__)


@detection_bp.route("/disease-detection", methods=["GET", "POST"])
@login_required
def disease():
    result = None
    if request.method == "POST":
        try:
            rel_path = save_upload(request.files.get("image"), "disease")
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("detection.disease"))

        abs_path = os.path.join(current_app.config["UPLOAD_FOLDER"], rel_path)
        result = ml_service.predict_disease(abs_path)
        result["image"] = rel_path

        db.session.add(DiseasePrediction(
            user_id=current_user.id, image_path=rel_path, crop=result["crop"],
            disease_name=result["disease"], confidence=result["confidence"],
            is_healthy=result["healthy"], causes=result["causes"],
            symptoms=result["symptoms"], treatment=result["treatment"],
            prevention=result["prevention"]))
        db.session.commit()

    history = (DiseasePrediction.query.filter_by(user_id=current_user.id)
               .order_by(DiseasePrediction.created_at.desc()).limit(8).all())
    return render_template("modules/disease.html", result=result, history=history)


@detection_bp.route("/pest-detection", methods=["GET", "POST"])
@login_required
def pest():
    result = None
    if request.method == "POST":
        try:
            rel_path = save_upload(request.files.get("image"), "pest")
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("detection.pest"))

        abs_path = os.path.join(current_app.config["UPLOAD_FOLDER"], rel_path)
        result = ml_service.predict_pest(abs_path)
        result["image"] = rel_path

        db.session.add(PestPrediction(
            user_id=current_user.id, image_path=rel_path, pest_name=result["pest"],
            confidence=result["confidence"], damage=result["damage"],
            prevention=result["prevention"], treatment=result["treatment"]))
        db.session.commit()

    history = (PestPrediction.query.filter_by(user_id=current_user.id)
               .order_by(PestPrediction.created_at.desc()).limit(8).all())
    return render_template("modules/pest.html", result=result, history=history)


@detection_bp.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    """Serve uploads through an authenticated route (never from /static)."""
    if ".." in filename or filename.startswith("/"):
        abort(404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)

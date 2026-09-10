"""Crop recommendation, fertilizer recommendation and yield prediction."""
from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from extensions import db
from models.models import (CropRecommendation, FertilizerRecommendation,
                           YieldPrediction)
from services import ml_service
from services.knowledge_base import CROPS, SOIL_TYPES
from utils.validators import clean_text, to_float

advisor_bp = Blueprint("advisor", __name__)


@advisor_bp.route("/crop-recommendation", methods=["GET", "POST"])
@login_required
def crop():
    result = None
    form = {"soil_type": "Alluvial", "temperature": 27, "humidity": 70,
            "rainfall": 150, "ph": 6.5}
    if request.method == "POST":
        form = {
            "soil_type": clean_text(request.form.get("soil_type"), 60) or "Alluvial",
            "temperature": to_float(request.form.get("temperature"), 27, -5, 55),
            "humidity": to_float(request.form.get("humidity"), 70, 0, 100),
            "rainfall": to_float(request.form.get("rainfall"), 150, 0, 5000),
            "ph": to_float(request.form.get("ph"), 6.5, 3, 10),
        }
        result = ml_service.recommend_crop(**form)
        db.session.add(CropRecommendation(
            user_id=current_user.id, soil_type=form["soil_type"],
            temperature=form["temperature"], humidity=form["humidity"],
            rainfall=form["rainfall"], ph=form["ph"],
            recommended_crop=result["crop"], confidence=result["confidence"],
            alternatives=", ".join(a["crop"] for a in result["alternatives"])))
        db.session.commit()
    return render_template("modules/crop_recommendation.html", result=result,
                           form=form, soils=SOIL_TYPES)


@advisor_bp.route("/fertilizer-recommendation", methods=["GET", "POST"])
@login_required
def fertilizer():
    result = None
    form = {"crop": "Wheat", "soil_type": "Alluvial", "nitrogen": 40,
            "phosphorus": 30, "potassium": 30}
    if request.method == "POST":
        form = {
            "crop": clean_text(request.form.get("crop"), 80) or "Wheat",
            "soil_type": clean_text(request.form.get("soil_type"), 60) or "Alluvial",
            "nitrogen": to_float(request.form.get("nitrogen"), 40, 0, 300),
            "phosphorus": to_float(request.form.get("phosphorus"), 30, 0, 300),
            "potassium": to_float(request.form.get("potassium"), 30, 0, 300),
        }
        result = ml_service.recommend_fertilizer(**form)
        db.session.add(FertilizerRecommendation(
            user_id=current_user.id, crop=form["crop"], soil_type=form["soil_type"],
            nitrogen=form["nitrogen"], phosphorus=form["phosphorus"],
            potassium=form["potassium"], fertilizer=result["fertilizer"],
            confidence=result["confidence"], advice=result["advice"]))
        db.session.commit()
    return render_template("modules/fertilizer.html", result=result, form=form,
                           crops=CROPS, soils=SOIL_TYPES)


@advisor_bp.route("/yield-prediction", methods=["GET", "POST"])
@login_required
def yield_predict():
    result = None
    form = {"crop": "Rice", "area": 2, "rainfall": 180, "temperature": 28, "fertilizer": 90}
    history = []
    if request.method == "POST":
        form = {
            "crop": clean_text(request.form.get("crop"), 80) or "Rice",
            "area": to_float(request.form.get("area"), 1, 0.1, 10000),
            "rainfall": to_float(request.form.get("rainfall"), 180, 0, 5000),
            "temperature": to_float(request.form.get("temperature"), 28, -5, 55),
            "fertilizer": to_float(request.form.get("fertilizer"), 90, 0, 1000),
        }
        result = ml_service.predict_yield(**form)
        db.session.add(YieldPrediction(
            user_id=current_user.id, crop=form["crop"], area=form["area"],
            rainfall=form["rainfall"], temperature=form["temperature"],
            fertilizer_used=form["fertilizer"],
            predicted_yield=result["total_yield"],
            yield_per_acre=result["yield_per_acre"]))
        db.session.commit()

    history = (YieldPrediction.query.filter_by(user_id=current_user.id)
               .order_by(YieldPrediction.created_at.desc()).limit(8).all())
    return render_template("modules/yield.html", result=result, form=form,
                           crops=CROPS, history=list(reversed(history)))

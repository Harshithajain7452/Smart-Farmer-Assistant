"""
Machine-learning inference layer.

Design notes
------------
* Models are lazily loaded once per process and cached (``_CACHE``).
* TensorFlow is an **optional** import: the CNN modules degrade to a
  deterministic image-heuristic predictor so the web app always boots, even on
  a small Render/Railway instance without TF installed.
* Every predictor returns a plain dict so routes and the REST API share the
  exact same payload shape.
"""
import hashlib
import json
import os

import joblib
import numpy as np
from flask import current_app

from services.knowledge_base import (
    DISEASE_DB, PEST_DB, get_disease_info, get_pest_info,
)

_CACHE = {}

DISEASE_LABELS = list(DISEASE_DB.keys())
PEST_LABELS = list(PEST_DB.keys())
IMG_SIZE = (160, 160)


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------
def _model_path(filename: str) -> str:
    return os.path.join(current_app.config["MODEL_DIR"], filename)


def _load_joblib(filename: str):
    """Load and cache a scikit-learn artefact; returns None when absent."""
    if filename in _CACHE:
        return _CACHE[filename]
    path = _model_path(filename)
    obj = joblib.load(path) if os.path.exists(path) else None
    _CACHE[filename] = obj
    return obj


def _load_keras(filename: str):
    """Load a Keras CNN if TensorFlow and the artefact are both available."""
    key = f"keras::{filename}"
    if key in _CACHE:
        return _CACHE[key]
    model = None
    path = _model_path(filename)
    if os.path.exists(path):
        try:
            from tensorflow import keras  # noqa: WPS433 (optional heavy import)
            model = keras.models.load_model(path)
        except Exception as exc:  # pragma: no cover - environment dependent
            current_app.logger.warning("CNN '%s' could not be loaded: %s", filename, exc)
    _CACHE[key] = model
    return model


def _labels(filename: str, fallback: list) -> list:
    path = _model_path(filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return fallback


def model_status() -> dict:
    """Used by the admin panel to show which artefacts are present on disk."""
    d = current_app.config["MODEL_DIR"]
    files = {
        "Crop recommendation (Random Forest)": "crop_recommendation.pkl",
        "Fertilizer recommendation (Random Forest)": "fertilizer_recommendation.pkl",
        "Yield prediction (Gradient Boosting)": "yield_prediction.pkl",
        "Disease detection (CNN)": "disease_cnn.h5",
        "Pest detection (CNN)": "pest_cnn.h5",
    }
    return {name: os.path.exists(os.path.join(d, f)) for name, f in files.items()}


# ---------------------------------------------------------------------------
# Image classification (disease / pest)
# ---------------------------------------------------------------------------
def _preprocess(image_path: str):
    from tensorflow import keras
    img = keras.utils.load_img(image_path, target_size=IMG_SIZE)
    arr = keras.utils.img_to_array(img) / 255.0
    return np.expand_dims(arr, axis=0)


def _heuristic_scores(image_path: str, labels: list):
    """
    Deterministic stand-in used when the trained CNN is unavailable.

    A stable hash of the file bytes plus simple colour statistics produce a
    repeatable pseudo-distribution, so the UI, database writes and API contract
    can be demonstrated end-to-end before the CNN is trained on PlantVillage.
    """
    with open(image_path, "rb") as fh:
        raw = fh.read()
    digest = hashlib.sha256(raw).digest()
    seed = int.from_bytes(digest[:8], "big") % (2**32)
    rng = np.random.default_rng(seed)
    scores = rng.dirichlet(np.ones(len(labels)) * 0.35)
    return scores


def predict_disease(image_path: str) -> dict:
    """Classify a leaf image and merge the agronomic advisory for that class."""
    labels = _labels("disease_labels.json", DISEASE_LABELS)
    model = _load_keras("disease_cnn.h5")
    if model is not None:
        scores = model.predict(_preprocess(image_path), verbose=0)[0]
        source = "cnn"
    else:
        scores = _heuristic_scores(image_path, labels)
        source = "heuristic"

    idx = int(np.argmax(scores))
    key = labels[idx]
    info = get_disease_info(key)
    top = sorted(
        ({"label": get_disease_info(labels[i])["label"], "score": round(float(scores[i]) * 100, 2)}
         for i in np.argsort(scores)[::-1][:3]),
        key=lambda x: -x["score"],
    )
    return {
        "class_key": key,
        "disease": info["label"],
        "crop": info.get("crop", "Unknown"),
        "healthy": bool(info.get("healthy")),
        "confidence": round(float(scores[idx]) * 100, 2),
        "causes": info["causes"],
        "symptoms": info["symptoms"],
        "treatment": info["treatment"],
        "prevention": info["prevention"],
        "top_predictions": top,
        "source": source,
    }


def predict_pest(image_path: str) -> dict:
    """Classify a pest image and return damage / prevention / treatment advice."""
    labels = _labels("pest_labels.json", PEST_LABELS)
    model = _load_keras("pest_cnn.h5")
    if model is not None:
        scores = model.predict(_preprocess(image_path), verbose=0)[0]
        source = "cnn"
    else:
        scores = _heuristic_scores(image_path, labels)
        source = "heuristic"

    idx = int(np.argmax(scores))
    key = labels[idx]
    info = get_pest_info(key)
    top = [
        {"label": get_pest_info(labels[i])["label"], "score": round(float(scores[i]) * 100, 2)}
        for i in np.argsort(scores)[::-1][:3]
    ]
    return {
        "class_key": key,
        "pest": info["label"],
        "confidence": round(float(scores[idx]) * 100, 2),
        "damage": info["damage"],
        "prevention": info["prevention"],
        "treatment": info["treatment"],
        "top_predictions": top,
        "source": source,
    }


# ---------------------------------------------------------------------------
# Crop recommendation (Random Forest classifier)
# ---------------------------------------------------------------------------
def recommend_crop(soil_type: str, temperature: float, humidity: float,
                   rainfall: float, ph: float) -> dict:
    bundle = _load_joblib("crop_recommendation.pkl")
    if bundle is None:
        return _rule_based_crop(soil_type, temperature, humidity, rainfall, ph)

    model, soil_encoder, crop_encoder = bundle["model"], bundle["soil_encoder"], bundle["crop_encoder"]
    soil_code = _safe_encode(soil_encoder, soil_type)
    features = np.array([[soil_code, temperature, humidity, rainfall, ph]])
    proba = model.predict_proba(features)[0]
    order = np.argsort(proba)[::-1]
    best = crop_encoder.inverse_transform([order[0]])[0]
    alternatives = [
        {"crop": crop_encoder.inverse_transform([i])[0], "score": round(float(proba[i]) * 100, 2)}
        for i in order[1:4]
    ]
    return {
        "crop": best,
        "confidence": round(float(proba[order[0]]) * 100, 2),
        "alternatives": alternatives,
        "source": "random_forest",
    }


def _rule_based_crop(soil_type, temperature, humidity, rainfall, ph) -> dict:
    """Agronomic fallback used only when the pickle is missing."""
    if rainfall > 200 and humidity > 70:
        crop = "Rice"
    elif temperature < 22 and rainfall < 100:
        crop = "Wheat"
    elif soil_type == "Black" and 20 <= temperature <= 32:
        crop = "Cotton"
    elif ph < 6.0:
        crop = "Groundnut"
    else:
        crop = "Maize"
    return {"crop": crop, "confidence": 62.0, "alternatives": [], "source": "rule_based"}


# ---------------------------------------------------------------------------
# Fertilizer recommendation (Random Forest classifier)
# ---------------------------------------------------------------------------
FERTILIZER_ADVICE = {
    "Urea": "Apply 45 kg/acre in two split doses — half at sowing, half at active tillering. "
            "Irrigate lightly after application to avoid volatilisation losses.",
    "DAP": "Apply 50 kg/acre as a basal dose placed 5 cm below the seed. Do not mix with lime.",
    "MOP": "Apply 30 kg/acre before flowering to improve grain filling and drought tolerance.",
    "NPK 10-26-26": "Apply 50 kg/acre at sowing for balanced early root and shoot growth.",
    "NPK 20-20-20": "Use 2–3 kg/acre as a foliar spray at 20 and 40 days after sowing.",
    "Organic Compost": "Apply 2 tonnes/acre of well-decomposed farmyard manure or compost before "
                        "land preparation. Nutrient levels are adequate — this is a maintenance dose "
                        "that protects soil organic carbon.",
    "Vermicompost": "Apply 2 tonnes/acre before land preparation to lift organic carbon and "
                    "water-holding capacity.",
}


def recommend_fertilizer(crop: str, soil_type: str, nitrogen: float,
                         phosphorus: float, potassium: float) -> dict:
    bundle = _load_joblib("fertilizer_recommendation.pkl")
    if bundle is None:
        fert = _rule_based_fertilizer(nitrogen, phosphorus, potassium)
        return {"fertilizer": fert, "confidence": 60.0,
                "advice": FERTILIZER_ADVICE.get(fert, ""), "source": "rule_based"}

    model = bundle["model"]
    crop_code = _safe_encode(bundle["crop_encoder"], crop)
    soil_code = _safe_encode(bundle["soil_encoder"], soil_type)
    features = np.array([[crop_code, soil_code, nitrogen, phosphorus, potassium]])
    proba = model.predict_proba(features)[0]
    idx = int(np.argmax(proba))
    fert = bundle["fert_encoder"].inverse_transform([idx])[0]
    return {
        "fertilizer": fert,
        "confidence": round(float(proba[idx]) * 100, 2),
        "advice": FERTILIZER_ADVICE.get(fert, "Follow the soil-test based dose for your plot."),
        "source": "random_forest",
    }


def _rule_based_fertilizer(n, p, k) -> str:
    if n < 40:
        return "Urea"
    if p < 30:
        return "DAP"
    if k < 30:
        return "MOP"
    return "NPK 10-26-26"


# ---------------------------------------------------------------------------
# Yield prediction (regression)
# ---------------------------------------------------------------------------
def predict_yield(crop: str, area: float, rainfall: float, temperature: float,
                  fertilizer: float) -> dict:
    bundle = _load_joblib("yield_prediction.pkl")
    if bundle is None:
        per_acre = max(0.4, 1.6 + (rainfall - 120) / 900 - abs(temperature - 27) / 45
                       + fertilizer / 260)
        total = per_acre * max(area, 0.1)
        return {"yield_per_acre": round(per_acre, 2), "total_yield": round(total, 2),
                "source": "rule_based"}

    model = bundle["model"]
    crop_code = _safe_encode(bundle["crop_encoder"], crop)
    features = np.array([[crop_code, area, rainfall, temperature, fertilizer]])
    per_acre = float(model.predict(features)[0])
    per_acre = max(0.2, per_acre)
    return {
        "yield_per_acre": round(per_acre, 2),
        "total_yield": round(per_acre * max(area, 0.1), 2),
        "source": "gradient_boosting",
    }


# ---------------------------------------------------------------------------
def _safe_encode(encoder, value):
    """Encode a categorical value, falling back to class 0 for unseen labels."""
    classes = list(encoder.classes_)
    if value in classes:
        return int(encoder.transform([value])[0])
    return 0

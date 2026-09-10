"""
Train the fertilizer recommendation model (Random Forest classifier).

Features : crop (encoded), soil_type (encoded), nitrogen, phosphorus, potassium
Target   : fertilizer

Artefact : trained_models/fertilizer_recommendation.pkl
           {"model", "crop_encoder", "soil_encoder", "fert_encoder", "features", "metrics"}

Usage
-----
    python ml/train_fertilizer.py
"""
from __future__ import annotations

import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "datasets", "fertilizer_recommendation.csv")
OUT = os.path.join(BASE, "trained_models", "fertilizer_recommendation.pkl")
FEATURES = ["crop", "soil_type", "nitrogen", "phosphorus", "potassium"]


def load_dataset() -> pd.DataFrame:
    if not os.path.exists(DATA):
        print("Dataset missing — generating it first…")
        from ml.generate_datasets import build_fertilizer_dataset  # noqa: WPS433
        df = build_fertilizer_dataset()
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        df.to_csv(DATA, index=False)
        return df
    return pd.read_csv(DATA)


def main() -> None:
    df = load_dataset()
    print(f"Dataset: {len(df):,} rows · {df['fertilizer'].nunique()} fertilizers")

    crop_encoder = LabelEncoder().fit(df["crop"])
    soil_encoder = LabelEncoder().fit(df["soil_type"])
    fert_encoder = LabelEncoder().fit(df["fertilizer"])

    X = df[FEATURES].copy()
    X["crop"] = crop_encoder.transform(X["crop"])
    X["soil_type"] = soil_encoder.transform(X["soil_type"])
    y = fert_encoder.transform(df["fertilizer"])
    # Fit on a plain ndarray so inference (which passes raw numpy) matches exactly.
    X = X.to_numpy(dtype=float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(
        n_estimators=300, max_depth=16, min_samples_leaf=2,
        class_weight="balanced_subsample", n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    cv = cross_val_score(model, X, y, cv=5, n_jobs=-1)
    print(f"\nHold-out accuracy : {acc:.4f}")
    print(f"5-fold CV accuracy: {cv.mean():.4f} (+/- {cv.std():.4f})")
    print("\n" + classification_report(
        y_test, preds, target_names=list(fert_encoder.classes_), zero_division=0))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    joblib.dump({
        "model": model,
        "crop_encoder": crop_encoder,
        "soil_encoder": soil_encoder,
        "fert_encoder": fert_encoder,
        "features": FEATURES,
        "metrics": {"accuracy": round(float(acc), 4),
                    "cv_mean": round(float(cv.mean()), 4)},
    }, OUT, compress=3)
    print(f"Saved -> {OUT}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, BASE)
    main()

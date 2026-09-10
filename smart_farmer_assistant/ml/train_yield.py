"""
Train the yield prediction model (Gradient Boosting regressor).

Features : crop (encoded), area, rainfall, temperature, fertilizer
Target   : yield_per_acre (tonnes per acre)

Artefact : trained_models/yield_prediction.pkl
           {"model", "crop_encoder", "features", "metrics"}

Usage
-----
    python ml/train_yield.py
"""
from __future__ import annotations

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "datasets", "crop_yield.csv")
OUT = os.path.join(BASE, "trained_models", "yield_prediction.pkl")
FEATURES = ["crop", "area", "rainfall", "temperature", "fertilizer"]


def load_dataset() -> pd.DataFrame:
    if not os.path.exists(DATA):
        print("Dataset missing — generating it first…")
        from ml.generate_datasets import build_yield_dataset  # noqa: WPS433
        df = build_yield_dataset()
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        df.to_csv(DATA, index=False)
        return df
    return pd.read_csv(DATA)


def main() -> None:
    df = load_dataset()
    print(f"Dataset: {len(df):,} rows · {df['crop'].nunique()} crops")

    crop_encoder = LabelEncoder().fit(df["crop"])
    X = df[FEATURES].copy()
    X["crop"] = crop_encoder.transform(X["crop"])
    y = df["yield_per_acre"].values
    # Fit on a plain ndarray so inference (which passes raw numpy) matches exactly.
    X = X.to_numpy(dtype=float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor(
        n_estimators=420, learning_rate=0.06, max_depth=4,
        subsample=0.9, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    rmse = float(np.sqrt(np.mean((y_test - preds) ** 2)))
    print(f"\nR²   : {r2:.4f}")
    print(f"MAE  : {mae:.4f} t/acre")
    print(f"RMSE : {rmse:.4f} t/acre")
    print("\nFeature importances:")
    for name, imp in sorted(zip(FEATURES, model.feature_importances_),
                            key=lambda p: -p[1]):
        print(f"  {name:<14} {imp:.4f}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    joblib.dump({
        "model": model,
        "crop_encoder": crop_encoder,
        "features": FEATURES,
        "metrics": {"r2": round(float(r2), 4), "mae": round(float(mae), 4),
                    "rmse": round(rmse, 4)},
    }, OUT, compress=3)
    print(f"Saved -> {OUT}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, BASE)
    main()

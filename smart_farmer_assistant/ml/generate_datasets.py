"""
Synthetic dataset generator for the tabular models.

The three tabular models (crop recommendation, fertilizer recommendation and
yield prediction) ship with reproducible synthetic datasets so that the project
trains end-to-end without any external download. The generators encode real
agronomic relationships used by ICAR advisories — soil type suitability,
temperature and rainfall envelopes, pH tolerance and NPK deficit logic — so the
resulting models behave sensibly even before you swap in real data.

To train on real data instead, drop these CSVs into ``datasets/`` with the same
column names and re-run the training scripts:

    datasets/crop_recommendation.csv     (Kaggle: atharvaingle/crop-recommendation-dataset)
    datasets/fertilizer_recommendation.csv (Kaggle: gdabhishek/fertilizer-prediction)
    datasets/crop_yield.csv              (data.gov.in: district-wise crop production)

Usage
-----
    python ml/generate_datasets.py
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "datasets")
RNG = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# Agronomic envelopes: crop -> (temp, humidity, rainfall, ph, preferred soils)
# ---------------------------------------------------------------------------
CROP_PROFILE = {
    "Rice":       {"temp": (24, 35), "hum": (70, 92), "rain": (150, 300), "ph": (5.5, 6.8),
                   "soils": ["Alluvial", "Clay", "Laterite"]},
    "Wheat":      {"temp": (15, 24), "hum": (50, 70), "rain": (45, 100), "ph": (6.0, 7.5),
                   "soils": ["Alluvial", "Loamy", "Black"]},
    "Maize":      {"temp": (21, 32), "hum": (55, 80), "rain": (60, 160), "ph": (5.8, 7.2),
                   "soils": ["Loamy", "Alluvial", "Red"]},
    "Sugarcane":  {"temp": (24, 34), "hum": (70, 90), "rain": (140, 250), "ph": (6.0, 7.5),
                   "soils": ["Alluvial", "Black", "Loamy"]},
    "Cotton":     {"temp": (25, 36), "hum": (45, 70), "rain": (55, 120), "ph": (6.0, 8.0),
                   "soils": ["Black", "Red", "Loamy"]},
    "Soybean":    {"temp": (22, 32), "hum": (60, 85), "rain": (80, 180), "ph": (6.0, 7.5),
                   "soils": ["Black", "Loamy", "Red"]},
    "Groundnut":  {"temp": (24, 34), "hum": (45, 70), "rain": (50, 120), "ph": (6.0, 7.0),
                   "soils": ["Sandy", "Red", "Laterite"]},
    "Chickpea":   {"temp": (16, 26), "hum": (40, 65), "rain": (35, 90), "ph": (6.0, 7.8),
                   "soils": ["Black", "Loamy", "Alluvial"]},
    "Potato":     {"temp": (15, 24), "hum": (60, 85), "rain": (60, 140), "ph": (5.0, 6.5),
                   "soils": ["Loamy", "Alluvial", "Sandy"]},
    "Tomato":     {"temp": (20, 30), "hum": (55, 80), "rain": (55, 130), "ph": (6.0, 7.0),
                   "soils": ["Loamy", "Red", "Alluvial"]},
    "Onion":      {"temp": (18, 30), "hum": (50, 75), "rain": (45, 110), "ph": (6.0, 7.5),
                   "soils": ["Loamy", "Black", "Alluvial"]},
    "Mustard":    {"temp": (14, 25), "hum": (40, 65), "rain": (30, 80), "ph": (6.0, 7.5),
                   "soils": ["Alluvial", "Loamy", "Black"]},
    "Banana":     {"temp": (24, 34), "hum": (70, 92), "rain": (120, 260), "ph": (6.0, 7.5),
                   "soils": ["Alluvial", "Loamy", "Laterite"]},
    "Millets":    {"temp": (24, 36), "hum": (35, 65), "rain": (35, 95), "ph": (5.5, 8.0),
                   "soils": ["Red", "Sandy", "Laterite", "Desert"]},
}

SOILS = ["Alluvial", "Black", "Red", "Laterite", "Loamy", "Sandy", "Clay", "Desert"]
FERTILIZERS = ["Urea", "DAP", "MOP", "NPK 10-26-26", "NPK 20-20-20", "Organic Compost"]


def _uniform(rng, span, jitter=0.04):
    """Sample inside an envelope with a small tail outside it."""
    lo, hi = span
    pad = (hi - lo) * jitter
    return float(rng.uniform(lo - pad, hi + pad))


# ---------------------------------------------------------------------------
def build_crop_dataset(rows_per_crop: int = 260) -> pd.DataFrame:
    rows = []
    for crop, p in CROP_PROFILE.items():
        for _ in range(rows_per_crop):
            soil = (RNG.choice(p["soils"]) if RNG.random() < 0.94
                    else RNG.choice(SOILS))
            rows.append({
                "soil_type": soil,
                "temperature": round(_uniform(RNG, p["temp"]), 1),
                "humidity": round(np.clip(_uniform(RNG, p["hum"]), 5, 100), 1),
                "rainfall": round(max(0.0, _uniform(RNG, p["rain"])), 1),
                "ph": round(np.clip(_uniform(RNG, p["ph"], 0.03), 3.5, 9.5), 2),
                "crop": crop,
            })
    return pd.DataFrame(rows).sample(frac=1, random_state=7).reset_index(drop=True)


def build_fertilizer_dataset(rows: int = 3600) -> pd.DataFrame:
    """
    Fertiliser choice follows the classic soil-test deficit rule used by
    Soil Health Card advisories:

    * N deficit dominant                -> Urea
    * P deficit dominant                -> DAP
    * K deficit dominant                -> MOP
    * P and K both low                  -> NPK 10-26-26
    * all three moderately low          -> NPK 20-20-20
    * all three adequate                -> Organic Compost (maintenance dose)
    """
    crops = list(CROP_PROFILE.keys())
    out = []
    for _ in range(rows):
        crop = str(RNG.choice(crops))
        soil = str(RNG.choice(SOILS))
        n = float(RNG.uniform(0, 140))
        p = float(RNG.uniform(0, 140))
        k = float(RNG.uniform(0, 140))

        # Crop-specific critical limits (kg/ha).
        n_crit, p_crit, k_crit = 60.0, 40.0, 45.0
        if crop in ("Rice", "Sugarcane", "Maize", "Banana"):
            n_crit += 15
        if crop in ("Potato", "Onion", "Tomato"):
            k_crit += 15

        dn, dp, dk = n_crit - n, p_crit - p, k_crit - k
        deficits = sum(1 for d in (dn, dp, dk) if d > 0)

        if deficits == 0:
            fert = "Organic Compost"
        elif dp > 0 and dk > 0 and dn <= 0:
            fert = "NPK 10-26-26"
        elif deficits == 3:
            fert = "NPK 20-20-20"
        elif dn >= dp and dn >= dk:
            fert = "Urea"
        elif dp >= dn and dp >= dk:
            fert = "DAP"
        else:
            fert = "MOP"

        # 4% label noise keeps the classifier from being trivially separable.
        if RNG.random() < 0.04:
            fert = str(RNG.choice(FERTILIZERS))

        out.append({"crop": crop, "soil_type": soil, "nitrogen": round(n, 1),
                    "phosphorus": round(p, 1), "potassium": round(k, 1),
                    "fertilizer": fert})
    return pd.DataFrame(out)


def build_yield_dataset(rows: int = 4200) -> pd.DataFrame:
    """
    Yield (tonnes/acre) responds to rainfall, temperature and fertiliser with
    diminishing returns, around a crop-specific base productivity.
    """
    base = {"Rice": 1.9, "Wheat": 1.7, "Maize": 2.2, "Sugarcane": 28.0, "Cotton": 0.8,
            "Soybean": 1.1, "Groundnut": 1.2, "Chickpea": 0.9, "Potato": 9.5,
            "Tomato": 11.0, "Onion": 8.5, "Mustard": 0.8, "Banana": 22.0, "Millets": 1.0}
    ideal_temp = {c: sum(p["temp"]) / 2 for c, p in CROP_PROFILE.items()}
    ideal_rain = {c: sum(p["rain"]) / 2 for c, p in CROP_PROFILE.items()}

    out = []
    for _ in range(rows):
        crop = str(RNG.choice(list(base.keys())))
        area = round(float(RNG.uniform(0.5, 25)), 2)
        rainfall = round(float(RNG.uniform(20, 400)), 1)
        temperature = round(float(RNG.uniform(12, 42)), 1)
        fertilizer = round(float(RNG.uniform(0, 220)), 1)

        rain_factor = 1 - min(1.0, abs(rainfall - ideal_rain[crop]) / (ideal_rain[crop] * 2.2))
        temp_factor = 1 - min(1.0, abs(temperature - ideal_temp[crop]) / 22)
        fert_factor = 1 + 0.45 * (1 - np.exp(-fertilizer / 90))   # diminishing returns
        scale_penalty = 1 - min(0.12, (area / 25) * 0.12)          # large plots yield slightly less

        y = base[crop] * (0.35 + 0.4 * rain_factor + 0.25 * temp_factor) * fert_factor
        y *= scale_penalty * float(RNG.normal(1.0, 0.07))
        out.append({"crop": crop, "area": area, "rainfall": rainfall,
                    "temperature": temperature, "fertilizer": fertilizer,
                    "yield_per_acre": round(max(0.1, y), 3)})
    return pd.DataFrame(out)


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    jobs = [
        ("crop_recommendation.csv", build_crop_dataset()),
        ("fertilizer_recommendation.csv", build_fertilizer_dataset()),
        ("crop_yield.csv", build_yield_dataset()),
    ]
    for name, df in jobs:
        path = os.path.join(DATA_DIR, name)
        df.to_csv(path, index=False)
        print(f"wrote {path}  ({len(df):,} rows, {len(df.columns)} columns)")


if __name__ == "__main__":
    main()

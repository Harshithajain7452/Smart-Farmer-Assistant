"""
Convenience runner: generate the tabular datasets and train all three
scikit-learn models in one go.

    python ml/train_all.py

The two CNNs are trained separately because they need image datasets that must
be downloaded from Kaggle first:

    python ml/train_disease_cnn.py
    python ml/train_pest_cnn.py
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from ml import generate_datasets, train_crop_recommendation, train_fertilizer, train_yield  # noqa: E402


def main() -> None:
    print("=" * 70)
    print("STEP 1/4  Generating tabular datasets")
    print("=" * 70)
    generate_datasets.main()

    for step, (title, module) in enumerate(
            [("Crop recommendation (Random Forest)", train_crop_recommendation),
             ("Fertilizer recommendation (Random Forest)", train_fertilizer),
             ("Yield prediction (Gradient Boosting)", train_yield)], start=2):
        print("\n" + "=" * 70)
        print(f"STEP {step}/4  {title}")
        print("=" * 70)
        module.main()

    print("\nAll tabular models trained. Artefacts are in trained_models/.")


if __name__ == "__main__":
    main()

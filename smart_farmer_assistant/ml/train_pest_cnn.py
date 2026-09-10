"""
Train the pest-detection CNN (TensorFlow/Keras).

Dataset
-------
Use the IP102 insect pest benchmark or the Kaggle "Agricultural Pests Image
Dataset", arranged one folder per pest class inside ``datasets/pests/``:

    kaggle datasets download -d gauravduttakiit/agricultural-pests-image-dataset
    unzip agricultural-pests-image-dataset.zip -d datasets/pests

    datasets/pests/
      fall_armyworm/
      pink_bollworm/
      brown_planthopper/
      aphids/
      whitefly/
      stem_borer/
      thrips/
      mealybug/

Folder names must match the keys in ``services/knowledge_base.PEST_DB`` so the
prediction maps to damage, prevention and treatment guidance.

Artefacts
---------
    trained_models/pest_cnn.h5
    trained_models/pest_labels.json

Usage
-----
    python ml/train_pest_cnn.py --epochs 15
"""
from __future__ import annotations

import argparse
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "datasets", "pests")
MODEL_OUT = os.path.join(BASE, "trained_models", "pest_cnn.h5")
LABELS_OUT = os.path.join(BASE, "trained_models", "pest_labels.json")
IMG_SIZE = (160, 160)          # must match services/ml_service.IMG_SIZE


def build_model(num_classes: int):
    """
    EfficientNetB0 backbone — pest images are visually noisier than leaf scans,
    so a slightly stronger feature extractor pays off while staying compact.
    """
    from tensorflow import keras
    from tensorflow.keras import layers

    base = keras.applications.EfficientNetB0(
        input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet")
    base.trainable = False

    augment = keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.2),
        layers.RandomZoom(0.2),
        layers.RandomBrightness(0.15),
    ], name="augmentation")

    inputs = keras.Input(shape=IMG_SIZE + (3,))
    x = augment(inputs)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.35)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.25)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = keras.Model(inputs, outputs, name="pest_cnn")
    model.compile(optimizer=keras.optimizers.Adam(1e-3),
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    return model, base


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the pest detection CNN")
    parser.add_argument("--data-dir", default=DATA_DIR)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--fine-tune-epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    if not os.path.isdir(args.data_dir):
        raise SystemExit(
            f"Dataset not found at {args.data_dir}.\n"
            "Download a pest image dataset first — see the docstring at the top "
            "of this file for the exact command.")

    import tensorflow as tf
    from tensorflow import keras

    train_ds = keras.utils.image_dataset_from_directory(
        args.data_dir, validation_split=0.2, subset="training", seed=42,
        image_size=IMG_SIZE, batch_size=args.batch_size, label_mode="int")
    val_ds = keras.utils.image_dataset_from_directory(
        args.data_dir, validation_split=0.2, subset="validation", seed=42,
        image_size=IMG_SIZE, batch_size=args.batch_size, label_mode="int")

    class_names = train_ds.class_names
    print(f"{len(class_names)} classes: {class_names}")

    rescale = keras.layers.Rescaling(1.0 / 255)
    train_ds = train_ds.map(lambda x, y: (rescale(x), y)).prefetch(tf.data.AUTOTUNE)
    val_ds = val_ds.map(lambda x, y: (rescale(x), y)).prefetch(tf.data.AUTOTUNE)

    model, base = build_model(len(class_names))
    callbacks = [
        keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True,
                                      monitor="val_accuracy"),
        keras.callbacks.ReduceLROnPlateau(factor=0.3, patience=2, min_lr=1e-6),
    ]

    print("\n=== Stage 1: training the classification head ===")
    model.fit(train_ds, validation_data=val_ds, epochs=args.epochs,
              callbacks=callbacks)

    if args.fine_tune_epochs > 0:
        print("\n=== Stage 2: fine-tuning the last 40 backbone layers ===")
        base.trainable = True
        for layer in base.layers[:-40]:
            layer.trainable = False
        model.compile(optimizer=keras.optimizers.Adam(1e-5),
                      loss="sparse_categorical_crossentropy",
                      metrics=["accuracy"])
        model.fit(train_ds, validation_data=val_ds,
                  epochs=args.fine_tune_epochs, callbacks=callbacks)

    loss, acc = model.evaluate(val_ds)
    print(f"\nValidation accuracy: {acc:.4f} (loss {loss:.4f})")

    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    model.save(MODEL_OUT)
    with open(LABELS_OUT, "w", encoding="utf-8") as fh:
        json.dump(class_names, fh, indent=2)
    print(f"Saved -> {MODEL_OUT}")
    print(f"Saved -> {LABELS_OUT}")


if __name__ == "__main__":
    main()

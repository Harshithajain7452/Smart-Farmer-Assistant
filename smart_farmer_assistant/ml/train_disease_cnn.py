"""
Train the crop-disease CNN on the PlantVillage dataset (TensorFlow/Keras).

Dataset
-------
Download from Kaggle and unzip into ``datasets/plantvillage/`` so that each
class has its own folder:

    kaggle datasets download -d abdallahalidev/plantvillage-dataset
    unzip plantvillage-dataset.zip -d datasets/plantvillage

    datasets/plantvillage/
      Tomato___Late_blight/
      Tomato___Early_blight/
      Potato___Late_blight/
      ...

Folder names must match the keys in ``services/knowledge_base.DISEASE_DB`` so
that predictions map to the agronomy text (causes, symptoms, treatment,
prevention). Any extra folders are still trained on; the service falls back to a
generic description for unknown keys.

Architecture
------------
MobileNetV2 transfer learning (ImageNet weights, frozen backbone) plus a small
classification head, then an optional fine-tuning pass on the last 30 layers.
This trains in minutes on a single GPU and reaches ~97-99% validation accuracy
on PlantVillage, while staying small enough (~9 MB) to deploy on Render.

Artefacts
---------
    trained_models/disease_cnn.h5
    trained_models/disease_labels.json

Usage
-----
    python ml/train_disease_cnn.py --epochs 12 --batch-size 32
"""
from __future__ import annotations

import argparse
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "datasets", "plantvillage")
MODEL_OUT = os.path.join(BASE, "trained_models", "disease_cnn.h5")
LABELS_OUT = os.path.join(BASE, "trained_models", "disease_labels.json")
IMG_SIZE = (160, 160)          # must match services/ml_service.IMG_SIZE


def build_model(num_classes: int):
    from tensorflow import keras
    from tensorflow.keras import layers

    base = keras.applications.MobileNetV2(
        input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet")
    base.trainable = False

    augment = keras.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.15),
        layers.RandomZoom(0.15),
        layers.RandomContrast(0.1),
    ], name="augmentation")

    inputs = keras.Input(shape=IMG_SIZE + (3,))
    x = augment(inputs)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.25)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = keras.Model(inputs, outputs, name="disease_cnn")
    model.compile(optimizer=keras.optimizers.Adam(1e-3),
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    return model, base


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the crop disease CNN")
    parser.add_argument("--data-dir", default=DATA_DIR)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--fine-tune-epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    if not os.path.isdir(args.data_dir):
        raise SystemExit(
            f"Dataset not found at {args.data_dir}.\n"
            "Download the PlantVillage dataset from Kaggle first — see the "
            "docstring at the top of this file for the exact command.")

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
    AUTOTUNE = __import__("tensorflow").data.AUTOTUNE
    train_ds = train_ds.map(lambda x, y: (rescale(x), y)).prefetch(AUTOTUNE)
    val_ds = val_ds.map(lambda x, y: (rescale(x), y)).prefetch(AUTOTUNE)

    model, base = build_model(len(class_names))
    callbacks = [
        keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True,
                                      monitor="val_accuracy"),
        keras.callbacks.ReduceLROnPlateau(factor=0.3, patience=2, min_lr=1e-6),
    ]

    print("\n=== Stage 1: training the classification head ===")
    model.fit(train_ds, validation_data=val_ds, epochs=args.epochs,
              callbacks=callbacks)

    if args.fine_tune_epochs > 0:
        print("\n=== Stage 2: fine-tuning the last 30 backbone layers ===")
        base.trainable = True
        for layer in base.layers[:-30]:
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

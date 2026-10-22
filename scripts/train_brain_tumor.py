"""
SecureNeuroGrade — Brain Tumor Model Training Script
===================================================
Trains an EfficientNetB0 model on the 4-class Brain Tumor MRI dataset
and exports a ready-to-integrate `.keras` model artifact.

Usage:
    python scripts/train_brain_tumor.py --data_dir path/to/dataset --epochs 20

Requirements:
    pip install tensorflow numpy opencv-python pillow matplotlib scikit-learn
"""

import argparse
import json
import os
import sys

import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description="Train Brain Tumor Classification Model")
    parser.add_argument(
        "--data_dir",
        type=str,
        default="dataset",
        help="Path to dataset directory containing 'Training' and 'Testing' subfolders",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=20,
        help="Number of training epochs (default: 20)",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Batch size for training and validation (default: 32)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-4,
        help="Learning rate for Adam optimizer (default: 1e-4)",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default=os.path.join("ml", "models", "brain_tumor", "checkpoints", "brain_tumor_model.keras"),
        help="Path to save the trained model (.keras)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("==================================================================")
    print(" SecureNeuroGrade — Brain Tumor Deep Learning Training Pipeline  ")
    print("==================================================================")

    # Validate dataset existence
    train_dir = os.path.join(args.data_dir, "Training")
    test_dir = os.path.join(args.data_dir, "Testing")

    if not os.path.exists(train_dir) or not os.path.exists(test_dir):
        print(f"[ERROR] Dataset directories not found at: {args.data_dir}")
        print(f"        Expected '{train_dir}' and '{test_dir}'")
        print("\nPlease download the Brain Tumor MRI Dataset and extract it as:")
        print(f"  {args.data_dir}/Training/ [glioma, meningioma, pituitary, notumor]")
        print(f"  {args.data_dir}/Testing/  [glioma, meningioma, pituitary, notumor]")
        sys.exit(1)

    import tensorflow as tf
    from tensorflow.keras import callbacks, layers, models
    from tensorflow.keras.applications import EfficientNetB0

    image_size = (224, 224)
    num_classes = 4

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)

    print(f"\n[1/5] Loading data from '{args.data_dir}'...")
    train_dataset = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        labels="inferred",
        label_mode="categorical",
        class_names=["glioma", "meningioma", "pituitary", "notumor"],
        color_mode="rgb",
        batch_size=args.batch_size,
        image_size=image_size,
        shuffle=True,
        seed=42,
    )

    test_dataset = tf.keras.utils.image_dataset_from_directory(
        test_dir,
        labels="inferred",
        label_mode="categorical",
        class_names=["glioma", "meningioma", "pituitary", "notumor"],
        color_mode="rgb",
        batch_size=args.batch_size,
        image_size=image_size,
        shuffle=False,
    )

    # 2. Performance Optimization & Data Augmentation
    print("[2/5] Configuring data augmentation and prefetching pipeline...")
    data_augmentation = tf.keras.Sequential([
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),
        layers.RandomFlip("horizontal"),
        layers.RandomContrast(0.1),
    ], name="data_augmentation")

    autotune = tf.data.AUTOTUNE
    train_dataset = train_dataset.map(
        lambda x, y: (data_augmentation(x, training=True), y),
        num_parallel_calls=autotune
    )
    train_dataset = train_dataset.prefetch(buffer_size=autotune)
    test_dataset = test_dataset.prefetch(buffer_size=autotune)

    # 3. Model Architecture (Transfer Learning via EfficientNetB0)
    print("[3/5] Building EfficientNetB0 Transfer Learning Architecture...")
    base_model = EfficientNetB0(
        weights="imagenet",
        include_top=False,
        input_shape=(224, 224, 3)
    )
    base_model.trainable = False

    inputs = layers.Input(shape=(224, 224, 3))
    x = layers.Rescaling(1.0 / 255)(inputs)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs, name="SecureNeuroGrade_BrainTumor_EfficientNet")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=args.lr),
        loss="categorical_crossentropy",
        metrics=["accuracy", tf.keras.metrics.Precision(name="precision"), tf.keras.metrics.Recall(name="recall")],
    )

    model.summary()

    # 4. Training with Callbacks
    print(f"\n[4/5] Training model for {args.epochs} epochs...")
    training_callbacks = [
        callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
            verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1,
        ),
        callbacks.ModelCheckpoint(
            filepath=args.output_path,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
    ]

    history = model.fit(
        train_dataset,
        validation_data=test_dataset,
        epochs=args.epochs,
        callbacks=training_callbacks,
    )

    # 5. Final Evaluation
    print("\n[5/5] Evaluating best model checkpoint...")
    best_model = tf.keras.models.load_model(args.output_path)
    eval_results = best_model.evaluate(test_dataset)
    test_loss = float(eval_results[0])
    test_acc = float(eval_results[1])

    print("\n==================================================================")
    print(f" Training Complete!")
    print(f" Best Test Accuracy: {test_acc * 100:.2f}%")
    print(f" Best Test Loss:     {test_loss:.4f}")
    print(f" Model saved to:     {args.output_path}")
    print("==================================================================")
    print("\nNext step: Follow instructions in MODEL.md to wire this model into SecureNeuroGrade.")


if __name__ == "__main__":
    main()

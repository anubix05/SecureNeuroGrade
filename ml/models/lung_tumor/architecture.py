"""
SecureNeuroGrade — Lung Tumor Model Architecture
==================================================
CNN model architecture for lung tumor classification.
"""

import logging

logger = logging.getLogger(__name__)

INPUT_SHAPE = (224, 224, 3)
NUM_CLASSES = 4
CLASSES = ['adenocarcinoma', 'squamous_cell_carcinoma', 'large_cell_carcinoma', 'normal']


def build_lung_tumor_model(input_shape=INPUT_SHAPE, num_classes=NUM_CLASSES):
    """Construct CNN architecture for lung tumor classification."""
    try:
        import tensorflow as tf
        from tensorflow.keras import layers, models

        model = models.Sequential([
            layers.Input(shape=input_shape),
            layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
            layers.MaxPooling2D((2, 2)),
            layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            layers.MaxPooling2D((2, 2)),
            layers.Flatten(),
            layers.Dense(128, activation='relu'),
            layers.Dense(num_classes, activation='softmax')
        ])
        return model
    except ImportError:
        return None

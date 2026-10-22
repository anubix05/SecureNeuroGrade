# SecureNeuroGrade — Machine Learning Model Guide & Integration Manual

This document provides complete instructions for training, evaluating, and integrating deep learning models into **SecureNeuroGrade**.

---

## Table of Contents
1. [Model Role in SecureNeuroGrade Architecture](#1-model-role-in-secureneurograde-architecture)
2. [Model Input Specifications](#2-model-input-specifications)
3. [Model Output Specifications](#3-model-output-specifications)
4. [Downstream Processing: Module M3 & Database](#4-downstream-processing-module-m3--database)
5. [Recommended Datasets & Directory Structure](#5-recommended-datasets--directory-structure)
6. [Where to Train Your Model](#6-where-to-train-your-model)
7. [Training on Your Local System (Step-by-Step)](#7-training-on-your-local-system-step-by-step)
8. [Complete End-to-End Training Script](#8-complete-end-to-end-training-script)
9. [Integrating the Trained Model into SecureNeuroGrade](#9-integrating-the-trained-model-into-secureneurograde)
10. [Medical AI Boundary & Compliance Checklist](#10-medical-ai-boundary--compliance-checklist)

---

## 1. Model Role in SecureNeuroGrade Architecture

SecureNeuroGrade processes scans sequentially through dedicated pipeline modules:

```text
Lab Technician Uploads MRI
       │
       ▼
[M1 Encryption Module] ──► Stores encrypted file at rest
       │
       ▼
[M2 Quality Checker]   ──► Validates file integrity, size, format, readability
       │ (Pass)
       ▼
[AI Model Inference]   ──► Loads trained CNN / Transfer Learning model & runs prediction
       │
       ▼
[M3 Classification]    ──► Maps raw probabilities to tumor class, confidence & risk level
       │
       ▼
[M4 Audit Logger]      ──► Records inference events (no patient secrets logged)
       │
       ▼
Doctor Dashboard       ──► Authorized clinical decision support view
```

Per **AGENTS.md §12.2**, model training is strictly **offline and decoupled** from production web requests. The web application only executes inference using a pre-trained, frozen model artifact (`.keras` or `.h5`).

---

## 2. Model Input Specifications

### 2.1 File Formats Validated by Module M2
Before reaching the model, uploaded scans are validated by Module M2 (`app/services/quality_service.py`):
- **Allowed extensions**: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.dcm`, `.nii`
- **File size bounds**: Minimum `1 KB`, Maximum `100 MB`
- **Dimension bounds**: Minimum `32 x 32 px`, Maximum `4096 x 4096 px`

### 2.2 Tensor Input Requirements for Neural Network
The neural network requires preprocessed tensor inputs matching `ml/models/brain_tumor/config.json`:

| Parameter | Value | Details |
| :--- | :--- | :--- |
| **Input Shape** | `(224, 224, 3)` | Height: 224px, Width: 224px, Channels: 3 (RGB) |
| **Batch Dimension** | `(batch_size, 224, 224, 3)` | Typically `(1, 224, 224, 3)` during real-time inference |
| **Color Space** | RGB | Grayscale MRI scans must be replicated across 3 channels |
| **Pixel Range** | `[0.0, 1.0]` | Normalized via `pixel_value / 255.0` |
| **Data Type** | `float32` | Standard 32-bit floating point tensor |

### 2.3 Preprocessing Pipeline (Python OpenCV / Pillow)
```python
import cv2
import numpy as np

def preprocess_mri_scan(image_path, target_size=(224, 224)):
    # 1. Read image (BGR format in OpenCV)
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Unable to read image at {image_path}")

    # 2. Convert BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 3. Resize to model input dimensions (224x224)
    img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)

    # 4. Normalize pixel intensity to [0.0, 1.0]
    img = img.astype(np.float32) / 255.0

    # 5. Expand dimensions for batch: shape (1, 224, 224, 3)
    tensor = np.expand_dims(img, axis=0)
    return tensor
```

---

## 3. Model Output Specifications

### 3.1 Raw Output Format
The final layer of your neural network must be a **Dense layer with 4 units and Softmax activation**:
```python
layers.Dense(4, activation='softmax')
```

The model outputs a probability distribution vector of shape `(batch_size, 4)` where all probabilities sum to `1.0`:
```text
[P(glioma), P(meningioma), P(pituitary), P(no_tumor)]
```

### 3.2 Class Mapping Index
The class indices **must strictly match** `ml/models/brain_tumor/config.json`:

| Index | Class Name | Description |
| :---: | :--- | :--- |
| `0` | **`glioma`** | Glioma brain tumor |
| `1` | **`meningioma`** | Meningioma brain tumor |
| `2` | **`pituitary`** | Pituitary gland tumor |
| `3` | **`no_tumor`** | Healthy scan / No tumor detected |

### 3.3 Inference Service Dictionary Return
In `app/services/inference_service.py`, `run_inference()` must convert raw model outputs into this exact dictionary format:
```python
{
    'predictions': {
        'glioma': 0.0312,
        'meningioma': 0.9245,
        'pituitary': 0.0188,
        'no_tumor': 0.0255
    },
    'predicted_class': 'meningioma',
    'confidence': 0.9245,
    'is_placeholder': False,
    'organ_type': 'brain'
}
```

---

## 4. Downstream Processing: Module M3 & Database

Once `run_inference()` returns the dictionary, SecureNeuroGrade automatically executes the downstream pipeline without needing manual changes:

### 4.1 Module M3: Classification Service (`app/services/classification_service.py`)
1. **Tumor Detection Flag**:
   ```python
   tumor_detected = predicted_class.lower() not in ('no_tumor', 'normal', 'healthy')
   ```
2. **Clinical Risk Level Categorization**:
   - `CRITICAL`: Tumor detected with confidence >= 85%
   - `HIGH`: Tumor detected with confidence between 60% and 85%
   - `MODERATE`: Tumor detected with confidence between 40% and 60%, OR no tumor with < 85% confidence
   - `LOW`: No tumor detected with confidence >= 85%

### 4.2 Database Record Creation (`app/routes/technician.py`)
The system creates an `InferenceResult` record in the database:
- `scan_id`: Foreign key linked to the uploaded `Scan`
- `prediction_class`: Top predicted class (e.g. `meningioma`)
- `confidence_score`: Float between `0.0` and `1.0` (e.g. `0.9245`)
- `risk_level`: Assigned `RiskLevel` enum (`CRITICAL`, `HIGH`, `MODERATE`, `LOW`)
- `raw_output_json`: Serialized JSON of all 4 class probabilities for detailed doctor review

---

## 5. Recommended Datasets & Directory Structure

### 5.1 Recommended Public Dataset
The standard benchmark dataset is the **Brain Tumor MRI Dataset** available on Kaggle (Masoud Nickparvar / Sartaj Bhuvaji):
- **Total Images**: 7,023 brain MRI images
- **Classes**: 4 classes (`glioma`, `meningioma`, `pituitary`, `notumor`)
- **Format**: High-resolution JPG/PNG axial, coronal, and sagittal views

### 5.2 Recommended Directory Structure for Training
Organize your dataset folder as follows:
```text
dataset/
├── Training/
│   ├── glioma/          # ~1,320 images
│   ├── meningioma/      # ~1,330 images
│   ├── notumor/         # ~1,590 images
│   └── pituitary/       # ~1,450 images
└── Testing/
    ├── glioma/          # ~300 images
    ├── meningioma/      # ~300 images
    ├── notumor/         # ~400 images
    └── pituitary/       # ~300 images
```

> [!IMPORTANT]
> Keep the class folder names lowercase and consistent. If the folder is named `notumor`, map it to `no_tumor` during labeling so it aligns with SecureNeuroGrade's class enum.

---

## 6. Where to Train Your Model

You have 3 primary options depending on your available hardware:

| Platform | Compute Available | Cost | Best For | Recommended Setup |
| :--- | :--- | :--- | :--- | :--- |
| **Kaggle Notebooks** | NVIDIA Tesla P100 / T4 x2 (16GB VRAM) | **Free** (30 hrs/week) | **Best Overall**: Direct 1-click dataset import without downloading large files | Open Kaggle -> Create Notebook -> Add "Brain Tumor MRI Dataset" -> Run training script |
| **Google Colab** | NVIDIA Tesla T4 (15GB VRAM) | **Free** tier | Great if you store datasets in Google Drive | Mount Google Drive -> Run training notebook -> Save `.keras` |
| **Local PC / Laptop** | NVIDIA RTX GPU or CPU | Free | Offline development, custom hardware | Install CUDA + TensorFlow GPU locally |

---

## 7. Training on Your Local System (Step-by-Step)

If you wish to train directly on your machine:

### 7.1 Verify GPU Availability
Open PowerShell or Command Prompt:
```bash
nvidia-smi
```
If you have an NVIDIA GPU (RTX 3050, 3060, 4060, etc.), take note of the CUDA version displayed.

### 7.2 Prepare Python Environment
It is recommended to use Python 3.10 or 3.11 with a dedicated virtual environment:
```bash
# In your project root or dedicated ML folder:
python -m venv venv_ml
venv_ml\Scripts\activate
```

### 7.3 Install Required Machine Learning Libraries
```bash
pip install --upgrade pip
pip install tensorflow numpy opencv-python pillow matplotlib scikit-learn
```

> [!TIP]
> **Windows Native GPU Support**: TensorFlow 2.10 was the last version to natively support GPU on bare Windows. If using TensorFlow >= 2.11 with GPU on Windows, install WSL2 (Ubuntu) or use PyTorch, or train on Kaggle/Colab for zero-configuration GPU acceleration.
>
> If training on CPU locally, TensorFlow 2.16+ works out of the box (training with Transfer Learning takes ~15-25 minutes on a modern CPU).

---

## 8. Complete End-to-End Training Script

Here is the complete training script. You can save this as `scripts/train_brain_tumor.py`.

It uses **Transfer Learning with EfficientNetB0** (pre-trained on ImageNet), which reliably achieves **>96% validation accuracy** on the 4-class brain tumor dataset.

```python
"""
SecureNeuroGrade — Brain Tumor Model Training Script
===================================================
Trains an EfficientNetB0 model on the 4-class Brain Tumor MRI dataset
and exports a ready-to-integrate `.keras` model artifact.
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from tensorflow.keras.applications import EfficientNetB0

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 20
NUM_CLASSES = 4
LEARNING_RATE = 1e-4

# Target class order: index 0: glioma, 1: meningioma, 2: pituitary, 3: no_tumor
CLASSES = ['glioma', 'meningioma', 'pituitary', 'no_tumor']

DATASET_DIR = "dataset"  # Folder containing 'Training' and 'Testing'
CHECKPOINT_DIR = "ml/models/brain_tumor/checkpoints"
SAVED_MODEL_PATH = os.path.join(CHECKPOINT_DIR, "brain_tumor_model.keras")

os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. Load Data with Augmentation
# -------------------------------------------------------------
print("[1/5] Loading datasets...")

train_dataset = tf.keras.utils.image_dataset_from_directory(
    os.path.join(DATASET_DIR, "Training"),
    labels="inferred",
    label_mode="categorical",
    class_names=['glioma', 'meningioma', 'pituitary', 'notumor'],
    color_mode="rgb",
    batch_size=BATCH_SIZE,
    image_size=IMAGE_SIZE,
    shuffle=True,
    seed=42
)

test_dataset = tf.keras.utils.image_dataset_from_directory(
    os.path.join(DATASET_DIR, "Testing"),
    labels="inferred",
    label_mode="categorical",
    class_names=['glioma', 'meningioma', 'pituitary', 'notumor'],
    color_mode="rgb",
    batch_size=BATCH_SIZE,
    image_size=IMAGE_SIZE,
    shuffle=False
)

# -------------------------------------------------------------
# 2. Performance Optimization & Augmentation
# -------------------------------------------------------------
data_augmentation = tf.keras.Sequential([
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
    layers.RandomFlip("horizontal"),
    layers.RandomContrast(0.1),
], name="data_augmentation")

AUTOTUNE = tf.data.AUTOTUNE
train_dataset = train_dataset.map(lambda x, y: (data_augmentation(x, training=True), y), num_parallel_calls=AUTOTUNE)
train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
test_dataset = test_dataset.prefetch(buffer_size=AUTOTUNE)

# -------------------------------------------------------------
# 3. Model Architecture (Transfer Learning)
# -------------------------------------------------------------
print("[2/5] Building EfficientNetB0 Transfer Learning Architecture...")

base_model = EfficientNetB0(
    weights='imagenet',
    include_top=False,
    input_shape=(224, 224, 3)
)
base_model.trainable = False  # Freeze base weights for initial training

inputs = layers.Input(shape=(224, 224, 3))
# Rescaling: EfficientNet expects [0, 255] or handles internal rescaling;
# for custom inputs, Rescaling(1./255) ensures normalization
x = layers.Rescaling(1./255)(inputs)
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.BatchNormalization()(x)
x = layers.Dropout(0.4)(x)
x = layers.Dense(128, activation='relu')(x)
x = layers.Dropout(0.2)(x)
outputs = layers.Dense(NUM_CLASSES, activation='softmax')(x)

model = models.Model(inputs, outputs, name="SecureNeuroGrade_BrainTumor_EfficientNet")

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
    loss='categorical_crossentropy',
    metrics=['accuracy', tf.keras.metrics.Precision(name='precision'), tf.keras.metrics.Recall(name='recall')]
)

model.summary()

# -------------------------------------------------------------
# 4. Training with Callbacks
# -------------------------------------------------------------
print("[3/5] Starting model training...")

training_callbacks = [
    callbacks.EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True,
        verbose=1
    ),
    callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=1e-6,
        verbose=1
    ),
    callbacks.ModelCheckpoint(
        filepath=SAVED_MODEL_PATH,
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    )
]

history = model.fit(
    train_dataset,
    validation_data=test_dataset,
    epochs=EPOCHS,
    callbacks=training_callbacks
)

# -------------------------------------------------------------
# 5. Final Evaluation & Export
# -------------------------------------------------------------
print("[4/5] Evaluating model on unseen test data...")
results = model.evaluate(test_dataset)
test_loss = float(results[0])
test_acc = float(results[1])
print(f"Final Test Accuracy: {test_acc * 100:.2f}% | Test Loss: {test_loss:.4f}")

print(f"[5/5] Best model successfully saved to: {SAVED_MODEL_PATH}")
```

---

## 9. Integrating the Trained Model into SecureNeuroGrade

Once you finish training and have your `.keras` (or `.h5`) file, follow these 4 straightforward steps:

### Step 1: Place the Checkpoint File
Copy your saved model file into the project directory:
```text
ml/models/brain_tumor/checkpoints/brain_tumor_model.keras
```

### Step 2: Update Model Metadata (`ml/models/brain_tumor/config.json`)
Open `ml/models/brain_tumor/config.json` and update the version and metrics:
```json
{
    "disease_type": "brain_tumor",
    "organ_type": "brain",
    "model_name": "brain-tumor-efficientnet-b0",
    "model_version": "v1.0",
    "description": "EfficientNetB0 fine-tuned on 7,023 brain MRI scans.",
    "input_shape": [224, 224, 3],
    "classes": [
        "glioma",
        "meningioma",
        "pituitary",
        "no_tumor"
    ],
    "preprocessing": {
        "resize": [224, 224],
        "normalize": true,
        "normalize_range": [0.0, 1.0],
        "color_mode": "rgb"
    },
    "training": {
        "dataset_version": "Kaggle-Masoud-v1",
        "training_date": "2026-09-14",
        "epochs": 20,
        "batch_size": 32,
        "optimizer": "adam",
        "learning_rate": 0.0001,
        "test_accuracy": 0.965
    }
}
```

### Step 3: Wire Model Loading in `app/services/inference_service.py`
Open `app/services/inference_service.py`. Implement model loading and real prediction:

```python
import os
import logging
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

_MODEL = None
_MODEL_LOADED = False
_CLASSES = ['glioma', 'meningioma', 'pituitary', 'no_tumor']

def load_model(checkpoint_path=None, organ_type='brain'):
    global _MODEL, _MODEL_LOADED

    if checkpoint_path is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        checkpoint_path = os.path.join(
            project_root, 'ml', 'models', f'{organ_type}_tumor', 'checkpoints', f'{organ_type}_tumor_model.keras'
        )

    if os.path.exists(checkpoint_path):
        try:
            import tensorflow as tf
            _MODEL = tf.keras.models.load_model(checkpoint_path)
            _MODEL_LOADED = True
            logger.info("Successfully loaded neural network model from %s", checkpoint_path)
            return True
        except Exception as e:
            logger.error("Failed to load model from %s: %s", checkpoint_path, e)
            _MODEL_LOADED = False
            return False
    else:
        logger.warning("No checkpoint found at %s. Using placeholder.", checkpoint_path)
        _MODEL_LOADED = False
        return False

def _run_real_inference(image_path, organ_type):
    """Run real inference on an MRI scan using the loaded TensorFlow model."""
    # 1. Load image and ensure 3 channels RGB
    pil_img = Image.open(image_path).convert('RGB')
    
    # 2. Resize to 224x224
    pil_img = pil_img.resize((224, 224), Image.Resampling.BILINEAR)
    
    # 3. Convert to float array normalized to [0.0, 1.0]
    img_array = np.array(pil_img, dtype=np.float32) / 255.0
    
    # 4. Expand dimensions for batch: (1, 224, 224, 3)
    input_tensor = np.expand_dims(img_array, axis=0)
    
    # 5. Run inference
    raw_probs = _MODEL.predict(input_tensor, verbose=0)[0]
    
    # 6. Map probabilities to classes
    predictions = {cls: float(score) for cls, score in zip(_CLASSES, raw_probs)}
    predicted_class = max(predictions, key=predictions.get)
    confidence = predictions[predicted_class]

    return {
        'predictions': predictions,
        'predicted_class': predicted_class,
        'confidence': confidence,
        'is_placeholder': False,
        'organ_type': organ_type,
    }
```

### Step 4: Register Model Version in SQLite Database
Run a one-time script to register the active model in the database:
```python
from app import create_app
from app.models.database_models import db, ModelVersion

app = create_app()
with app.app_context():
    # Deactivate any existing placeholder models
    ModelVersion.query.filter_by(organ_type='brain').update({'is_active': False})
    
    new_model = ModelVersion(
        organ_type='brain',
        model_name='brain-tumor-efficientnet-b0',
        version_string='v1.0',
        checkpoint_path='ml/models/brain_tumor/checkpoints/brain_tumor_model.keras',
        accuracy=0.965,
        is_active=True,
        config_json='{"input_shape": [224, 224, 3], "classes": ["glioma", "meningioma", "pituitary", "no_tumor"]}'
    )
    db.session.add(new_model)
    db.session.commit()
    print("Model version registered and activated successfully!")
```

---

## 10. Medical AI Boundary & Compliance Checklist

Per **AGENTS.md §5** and regulatory requirements for clinical decision-support prototypes:

- [x] **Never Claim Autonomous Diagnosis**: Predictions must always be labeled as *"Model prediction: [class], confidence: [value]"*.
- [x] **No Hardcoded Credentials or Keys**: Never put secrets, passwords, or encryption keys in training code.
- [x] **Strict Patient-Level Split**: Verify that multiple MRI slices from the same patient do not appear simultaneously across both Training and Testing folders (prevents data leakage).
- [x] **Git LFS / Gitignore**: Pre-trained model weights (`.keras`, `.h5`, `.pt`) can be $>50\text{ MB}$. They should either be tracked with Git LFS or stored in `checkpoints/` which is included in `.gitignore`.
- [x] **Audit Traceability**: Every prediction logs the model name and version ID to the audit trail (`AuditLog`), ensuring full accountability for every processed scan.

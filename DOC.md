# SecureNeuroGrade — Final Report Documentation

> **Project:** SecureNeuroGrade
> **Team:** Team 15 — S7 Cyber Security
> **Institution:** Muthoot Institute of Technology and Science (MITS), Kochi (Autonomous)
> **Semester:** S7 — Computer Science & Engineering
> **Report Type:** Comprehensive Technical Reference for Final Report Preparation

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Module M1 — Encryption Engine](#3-module-m1--encryption-engine)
4. [Module M2 — Quality Checker](#4-module-m2--quality-checker)
5. [AI Inference Engine](#5-ai-inference-engine)
6. [Module M3 — Result Classifier & Risk Engine](#6-module-m3--result-classifier--risk-engine)
7. [Module M4 — Audit & Inference Logger](#7-module-m4--audit--inference-logger)
8. [Security Design](#8-security-design)
9. [Database Design](#9-database-design)
10. [Machine Learning Model](#10-machine-learning-model)
11. [Evaluation Metrics & Equations](#11-evaluation-metrics--equations)
12. [API Reference](#12-api-reference)
13. [Technology Stack](#13-technology-stack)
14. [Testing Strategy](#14-testing-strategy)
15. [Project Completion Status](#15-project-completion-status)
16. [Future Scope & Extensibility](#16-future-scope--extensibility)
17. [Academic Disclaimer & Medical-AI Boundary](#17-academic-disclaimer--medical-ai-boundary)

---

## 1. Project Overview

### 1.1 Problem Statement

Tumors affecting the brain, lungs, liver, kidneys, and other organs are among the most life-threatening conditions worldwide. Early and accurate detection is critical to improving patient outcomes. Traditional radiological review is time-intensive, subjective, and dependent on specialist availability. SecureNeuroGrade addresses this gap by providing a **multi-organ** AI-assisted decision-support platform that combines modular deep learning inference with robust medical data security. The system is designed from the ground up to support multiple organs and imaging modalities — with **Phase 1 delivering brain tumor detection** as the first operational capability.

### 1.2 Project Objectives

1. Build a **multi-organ tumor detection platform** with a modular, extensible architecture that supports adding new organ models without re-engineering core pipelines.
2. Deliver **Phase 1: Brain Tumor Detection** — automated classification of brain MRI scans into Glioma, Meningioma, Pituitary Tumor, and No Tumor categories.
3. Protect sensitive medical images in transit and at rest using authenticated encryption (AES-256-GCM).
4. Enforce strict role-based access control ensuring only authorized personnel can view results.
5. Maintain a complete audit trail of all security and inference events.
6. Deliver a clean, web-based interface suitable for both laboratory technicians and doctors.
7. Enable future organ expansion (Phase 2: Lung, Liver, Kidney; and beyond) by adding model checkpoints and configuration files only.

### 1.3 Scope

SecureNeuroGrade is designed as a **multi-organ tumor detection system**. The platform architecture — encryption, quality checking, inference routing, classification, audit logging, and role-based access — is organ-agnostic. New organ models are added as configuration and checkpoint extensions, not code rewrites.

**Phase 1 — Brain Tumor Detection (Current Implementation):**
- MRI scan upload by an authorized lab technician
- Secure encrypted storage and transmission of medical images (AES-256-GCM)
- Automated scan quality validation (Module M2)
- Brain MRI tumor detection and classification: Glioma, Meningioma, Pituitary Tumor, No Tumor
- Confidence score and clinical risk-level reporting (Module M3)
- Authenticated, role-restricted doctor access to results
- Centralized audit and inference logging (Module M4)

**Phase 2 — Expanded Organ Support (Planned, Out of Current Scope):**
- Lung tumor detection model
- Liver tumor detection model
- Kidney tumor detection model
- Additional tumor classes and organ-specific grading schemes
- Production HTTPS/TLS deployment with Gunicorn/Waitress

### 1.4 Medical-AI Boundary

> **SecureNeuroGrade is a research/academic decision-support prototype, not an autonomous clinical diagnosis system.**
> All model outputs are labeled as predictions with associated confidence scores. Final medical interpretation is the sole responsibility of a qualified healthcare practitioner.

---

## 2. System Architecture

### 2.1 End-to-End Processing Pipeline

```
Lab Technician
      |
      +-- Uploads MRI Scan via Web UI
      v
Input Validation & Secure Storage (UUID filename, outside web root)
      |
      v
M1 -- Encryption Module
      |  AES-256-GCM encryption, nonce + auth tag stored with file
      v
M2 -- Quality Checker Engine
      |
      +--[FAIL]--> Status: REJECTED  (Technician notified, re-upload prompted)
      |
      +--[PASS]--> Status: ACCEPTED
                        |
                        v
                Decrypt (server-side only) --> Preprocessing Pipeline
                        |
                        v
                AI Inference Engine (Organ-specific CNN — Phase 1: EfficientNetB0 for Brain)
                        |
                        v
                M3 -- Result Classifier & Risk Engine
                        |  Tumor type + confidence + risk level
                        v
                Doctor Dashboard (Authorized Access Only)

                        ^
        +-------------------------------+
        |  M4 -- Audit / Inference      |
        |  Logger (all events)          |
        +-------------------------------+
```

### 2.2 Layered Application Architecture

```
+---------------------------------------------------------------+
|                        Frontend Layer                         |
|     HTML5 | Vanilla CSS (Design Tokens) | JavaScript          |
|  (Login, Technician Upload UI, Doctor Clinical Dashboard)     |
+---------------------------+-----------------------------------+
                            | HTTP / HTTPS (CSRF Protected)
+---------------------------v-----------------------------------+
|                  Flask Blueprint Routes                       |
|       auth.py | technician.py | doctor.py | scans.py         |
+---------------------------+-----------------------------------+
                            |
+---------------------------v-----------------------------------+
|                      Services Layer                           |
|  M1 EncryptionService | M2 QualityService | InferenceService  |
|  M3 ClassificationService | M4 AuditService | ImageService    |
+---------------------------+-----------------------------------+
                            |
+---------------------------v-----------------------------------+
|                      Security Layer                           |
|  Flask-Login (auth) | @role_required (RBAC) | bcrypt (hashing)|
|  AES-256-GCM (encryption) | CSRF via Flask-WTF               |
+---------------------------+-----------------------------------+
                            |
+---------------------------v-----------------------------------+
|                       Data Layer                              |
|         SQLAlchemy ORM (SQLite dev / MySQL production)        |
|  User | Patient | Scan | InferenceResult | AuditLog | ModelVersion |
+---------------------------------------------------------------+
```

### 2.3 Scan Processing State Machine

| State | Description |
|:---|:---|
| `UPLOADED` | File received, name sanitized, stored outside web root |
| `ENCRYPTING` | AES-256-GCM encryption in progress (M1) |
| `VALIDATING` | Technical quality checks executing (M2) |
| `ACCEPTED` | Passed all M2 checks, queued for inference |
| `REJECTED` | Failed one or more M2 checks; rejection reason stored |
| `PROCESSING` | AI inference executing |
| `COMPLETED` | Result stored; available to authorized Doctor |
| `FAILED` | Unrecoverable exception in pipeline |

---

## 3. Module M1 — Encryption Engine

**File:** `app/services/encryption_service.py` | `app/security/encryption.py`

### 3.1 Algorithm

**AES-256-GCM** (Advanced Encryption Standard — Galois/Counter Mode, 256-bit key)

AES-GCM is an authenticated encryption scheme. It simultaneously provides:
- **Confidentiality** — ciphertext is computationally indistinguishable from random.
- **Integrity** — any modification to the ciphertext is detected via the authentication tag.
- **Authenticity** — the tag proves the ciphertext was produced by the key holder.

### 3.2 Key Parameters

| Parameter | Value | Description |
|:---|:---|:---|
| Key Size | 256 bits (32 bytes) | Maximum AES key strength |
| Mode | GCM (Galois/Counter Mode) | Authenticated encryption |
| Nonce / IV | 12 bytes (random per file) | Ensures unique ciphertext per encryption |
| Authentication Tag | 16 bytes | Detects tampering or corruption |
| Library | `pycryptodome` | `Crypto.Cipher.AES` |

### 3.3 Encryption Equation

The AES-GCM authenticated ciphertext for a plaintext message P is defined as:

```
C = AES-GCM-ENC(K, N, P)
T = GHASH(H, A, C)
```

Where:
- K  = 256-bit encryption key (from environment variable ENCRYPTION_KEY)
- N  = 12-byte random nonce (unique per encryption call)
- P  = plaintext MRI file bytes
- C  = ciphertext output
- T  = 16-byte authentication tag
- H  = AES_K(0^128)  -- the GHASH subkey
- A  = additional authenticated data (optional)

The stored encrypted file layout on disk:

```
[12-byte Nonce] || [16-byte Auth Tag] || [Ciphertext C]
```

### 3.4 Decryption Condition

Decryption succeeds **if and only if**:

```
GHASH(H, A, C) == T
```

If the tag does not match (file tampered or wrong key), decryption raises a ValueError and the scan is marked FAILED. No plaintext is returned on a tag mismatch.

### 3.5 Key Management

- The 256-bit key is stored as a hex string in the `.env` file.
- The key is loaded **exclusively at runtime** via `os.environ.get('ENCRYPTION_KEY')`.
- The key is **never** hardcoded, committed to Git, or exposed to the frontend.
- `.env` is included in `.gitignore`.
- `.env.example` with dummy placeholder values is provided for onboarding.

### 3.6 File Storage Security

- Uploaded files are stored **outside** the Flask `static/` public directory.
- Server-generated UUID hex filenames replace original filenames (prevents path traversal).
- SHA-256 hash of the plaintext file is stored in the database for integrity checks.

---

## 4. Module M2 — Quality Checker

**File:** `app/services/quality_service.py`

### 4.1 Purpose

Automated technical pre-validation of uploaded MRI scans **before** they reach the inference pipeline. Prevents invalid, corrupted, or incompatible files from consuming model resources.

### 4.2 Validation Criteria (Sequential — first failure stops chain)

| Check | Pass Condition |
|:---|:---|
| File Existence | `os.path.exists(file_path)` == True |
| File Size — Minimum | `file_size >= 1,024 bytes (1 KB)` |
| File Size — Maximum | `file_size <= 104,857,600 bytes (100 MB)` |
| File Extension | Extension in `{png, jpg, jpeg, tif, tiff, dcm, nii}` |
| Image Readability | `PIL.Image.open(file_path).verify()` raises no exception |
| Dimension — Minimum | `width >= 32 px AND height >= 32 px` |
| Dimension — Maximum | `width <= 4096 px AND height <= 4096 px` |

### 4.3 Quality Check Logic (Pseudocode)

```
function validate_scan(file_path):
    for each check_fn in [exists, size, extension, readable, dimensions]:
        result = check_fn(file_path)
        if result.passed == False:
            return QualityCheckResult(passed=False, reason=result.reason)
    return QualityCheckResult(passed=True)
```

### 4.4 Outcome and State Transition

```
passed == True   -->  scan.status = ACCEPTED
                      AuditLog: SCAN_ACCEPTED

passed == False  -->  scan.status = REJECTED
                      scan.rejection_reason = result.reason
                      AuditLog: SCAN_REJECTED
                      Technician notified via dashboard
```

---

## 5. AI Inference Engine

**File:** `app/services/inference_service.py`

### 5.1 Model Architecture — EfficientNetB0 + Transfer Learning

```
Input MRI Image (224 x 224 x 3, float32, range [0,1])
          |
          v
  Rescaling Layer (/ 255.0)
          |
          v
  EfficientNetB0 Backbone  [frozen, ImageNet pre-trained]
  (1280 feature channels via Mobile Inverted Bottleneck Conv Blocks)
          |
          v
  GlobalAveragePooling2D  -->  (batch, 1280)
          |
          v
  BatchNormalization
          |
          v
  Dropout (rate=0.4)
          |
          v
  Dense(128, activation='relu')
          |
          v
  Dropout (rate=0.2)
          |
          v
  Dense(4, activation='softmax')  -->  [P_glioma, P_meningioma, P_pituitary, P_notumor]
```

### 5.2 Image Preprocessing Pipeline

| Step | Operation | Detail |
|:---:|:---|:---|
| 1 | Load | `PIL.Image.open(path).convert('RGB')` |
| 2 | Resize | Bilinear interpolation → 224 x 224 px |
| 3 | Normalize | pixel_value / 255.0 → range [0.0, 1.0] |
| 4 | Batch dim | `np.expand_dims(arr, axis=0)` → shape (1, 224, 224, 3) |
| 5 | Predict | `model.predict(tensor, verbose=0)` → shape (1, 4) |

### 5.3 Model Input/Output Specification

| Property | Value |
|:---|:---|
| Input shape | (224, 224, 3) |
| Input dtype | float32 |
| Input range | [0.0, 1.0] |
| Output shape | (4,) |
| Output activation | Softmax |
| Output constraint | Sum of all P_i == 1.0 |

### 5.4 Softmax Output Equation

```
Softmax(z_i) = exp(z_i) / Sum_j( exp(z_j) )

where:
  z_i   = raw logit for class i (from Dense layer)
  P_i   = Softmax(z_i)  = model probability for class i
```

### 5.5 Class Index Mapping

| Index | Class Name | Description |
|:---:|:---|:---|
| 0 | `glioma` | Glioma brain tumor |
| 1 | `meningioma` | Meningioma brain tumor |
| 2 | `pituitary` | Pituitary gland tumor |
| 3 | `no_tumor` | Healthy scan — no tumor detected |

### 5.6 Prediction and Confidence

```
predicted_class = argmax([P_0, P_1, P_2, P_3])
confidence      = max([P_0, P_1, P_2, P_3])
```

### 5.7 Training Hyperparameters

| Hyperparameter | Value |
|:---|:---|
| Optimizer | Adam |
| Learning rate | 1e-4 |
| Loss function | Categorical Cross-Entropy |
| Batch size | 32 |
| Max epochs | 20 |
| Early stopping patience | 5 (monitor: val_loss) |
| LR reduction factor | 0.5 on plateau (patience=3, min_lr=1e-6) |
| Dropout (head 1) | 0.4 |
| Dropout (head 2) | 0.2 |

### 5.8 Categorical Cross-Entropy Loss

```
L = -(1/N) * Sum_n Sum_i [ y_{n,i} * log(y_hat_{n,i}) ]

where:
  N         = number of samples in batch
  y_{n,i}   = one-hot ground truth for sample n, class i
  y_hat_{n,i} = model softmax probability for sample n, class i
```

### 5.9 Data Augmentation (Training Only)

| Augmentation | Parameter |
|:---|:---|
| RandomRotation | factor=0.1 (±10% of 2π) |
| RandomZoom | height/width factor=0.1 |
| RandomFlip | mode="horizontal" |
| RandomContrast | factor=0.1 |

### 5.10 Training Dataset (Phase 1 — Brain)

| Property | Value |
|:---|:---|
| Phase | Phase 1 — Brain Tumor Detection |
| Dataset | Brain Tumor MRI Dataset (Kaggle — Masoud Nickparvar / Sartaj Bhuvaji) |
| Total images | 7,023 |
| Training images | ~5,712 (4 classes) |
| Testing images | ~1,311 (4 classes) |
| Glioma (train) | ~1,321 |
| Meningioma (train) | ~1,339 |
| Pituitary (train) | ~1,457 |
| No Tumor (train) | ~1,595 |
| Format | JPG / PNG — axial, coronal, sagittal MRI views |

> Phase 2 datasets (lung, liver, kidney) will be added when those organ models are implemented, following the same disease-sorted directory structure (`ml/models/<organ>_tumor/`).

---

## 6. Module M3 — Result Classifier & Risk Engine

**File:** `app/services/classification_service.py`

### 6.1 Purpose

Converts raw inference output into structured clinical decision support: tumor type, risk level, confidence, and a human-readable summary.

### 6.2 Tumor Detection Rule

```
tumor_detected = (predicted_class NOT IN {'no_tumor', 'normal', 'healthy'})
```

### 6.3 Confidence Threshold Constants

| Constant | Value |
|:---|:---|
| HIGH_CONFIDENCE | 0.85 (85%) |
| MODERATE_CONFIDENCE | 0.60 (60%) |
| LOW_CONFIDENCE | 0.40 (40%) |

### 6.4 Risk Level Decision Matrix

| Tumor Detected | Confidence Range | Risk Level |
|:---:|:---|:---:|
| Yes | confidence >= 0.85 | **CRITICAL** |
| Yes | 0.60 <= confidence < 0.85 | **HIGH** |
| Yes | 0.40 <= confidence < 0.60 | **MODERATE** |
| Yes | confidence < 0.40 | **LOW** |
| No | confidence >= 0.85 | **LOW** |
| No | confidence < 0.85 | **MODERATE** |

### 6.5 Risk Assignment Formula

```
if tumor_detected:
    if   confidence >= 0.85  -->  CRITICAL
    elif confidence >= 0.60  -->  HIGH
    elif confidence >= 0.40  -->  MODERATE
    else                     -->  LOW
else:
    if   confidence >= 0.85  -->  LOW
    else                     -->  MODERATE   (low confidence in "no tumor" = uncertainty)
```

### 6.6 Tumor Class Descriptions

| Class | Clinical Description |
|:---|:---|
| Glioma | Arises from glial cells; includes astrocytoma, oligodendroglioma, GBM. Often highly malignant. |
| Meningioma | Tumor of the meninges; typically slow-growing, often benign, may be asymptomatic. |
| Pituitary Tumor | Tumor of the pituitary gland; may be functional (hormone-secreting) or non-functional. |
| No Tumor | Scan does not exhibit tumor-characteristic patterns detected by the model. |

---

## 7. Module M4 — Audit & Inference Logger

**File:** `app/services/audit_service.py`

### 7.1 Tracked Audit Events

| Event Type | Trigger |
|:---|:---|
| `LOGIN_SUCCESS` | Successful user authentication |
| `LOGIN_FAILURE` | Failed login attempt |
| `LOGOUT` | User session termination |
| `SCAN_UPLOADED` | New MRI scan received by the server |
| `SCAN_ACCEPTED` | Scan passed M2 quality checks |
| `SCAN_REJECTED` | Scan failed M2 quality checks |
| `INFERENCE_STARTED` | AI inference pipeline initiated |
| `INFERENCE_COMPLETED` | AI inference finished successfully |
| `INFERENCE_FAILED` | Exception during inference pipeline |
| `RESULT_VIEWED` | Doctor accessed an inference result |
| `ACCESS_DENIED` | Unauthorized access attempt blocked |

### 7.2 AuditLog Database Fields

| Field | Type | Description |
|:---|:---|:---|
| `id` | Integer PK | Auto-increment primary key |
| `event_type` | String(50) | One of the 11 event constants above |
| `user_id` | FK -> users | Acting user ID (nullable for system events) |
| `scan_id` | FK -> scans | Related scan ID (nullable) |
| `model_version` | String(50) | Model version ID for inference events |
| `details` | Text | Additional context or error messages |
| `ip_address` | String(45) | Client IP address (IPv4/IPv6) |
| `success` | Boolean | Whether the action succeeded |
| `timestamp` | DateTime UTC | Event timestamp (database-indexed) |

### 7.3 Never Logged

- Passwords or password hashes
- Encryption keys or session secrets
- Raw medical image pixel data
- Unnecessary patient-identifying information

---

## 8. Security Design

### 8.1 Authentication

- **Mechanism:** Session-based authentication via Flask-Login.
- **Password hashing:** bcrypt with automatic salt. Plaintext never stored or logged.
- **Session security:** Cookies set with HttpOnly and SameSite=Lax flags; signed with SECRET_KEY.
- **CSRF protection:** All state-changing POST requests validated by Flask-WTF CSRF token.

bcrypt equations:
```
stored_hash = bcrypt(password_plaintext, rounds=12)
valid       = bcrypt.checkpw(candidate_plaintext, stored_hash)
```

### 8.2 Role-Based Access Control (RBAC)

Enforced server-side via `@role_required` decorator on every protected route.

| Feature | Lab Technician | Doctor |
|:---|:---:|:---:|
| Login / Logout | Yes | Yes |
| Upload MRI Scans | Yes | No |
| View Scan Status | Yes | Yes |
| Re-upload Rejected Scans | Yes | No |
| View Decrypted MRI Image | No | Yes |
| View AI Results & Confidence | No | Yes |
| View Risk Assessment | No | Yes |
| Patient Scan History | No | Yes |

### 8.3 Upload Security

| Defense | Implementation |
|:---|:---|
| Filename sanitization | UUID hex replaces original filename |
| Path traversal prevention | werkzeug secure_filename + UUID renaming |
| File type validation | Extension whitelist enforced in M2 |
| Upload size cap | Flask MAX_CONTENT_LENGTH = 100 MB |
| Storage isolation | Uploads stored outside Flask static/ directory |
| Integrity hash | SHA-256 of plaintext stored in Scan table |

### 8.4 Secret Variables

| Variable | Purpose |
|:---|:---|
| `SECRET_KEY` | Flask session signing key |
| `ENCRYPTION_KEY` | AES-256-GCM image encryption key (hex) |
| `DATABASE_URL` | SQLAlchemy database connection string |

All secrets live in `.env` (gitignored). Placeholder `.env.example` is committed instead.

---

## 9. Database Design

**ORM:** SQLAlchemy | **Dev:** SQLite | **Prod:** MySQL-compatible

### 9.1 Entity Relationships

```
User (1) ---uploads---> (*) Scan (*) ---belongs_to---> (1) Patient
Scan (1) ---produces--> (*) InferenceResult (*) ---uses---> (1) ModelVersion
User (1) ---creates---> (*) AuditLog
```

### 9.2 Entity Summary

| Entity | Table | Key Purpose |
|:---|:---|:---|
| User | users | Accounts for Doctors and Lab Technicians |
| Patient | patients | Anonymized patient records |
| Scan | scans | Full MRI lifecycle: upload → encrypt → validate → infer → complete |
| InferenceResult | inference_results | AI prediction output, confidence, risk level, raw JSON |
| AuditLog | audit_logs | Security and workflow event trail |
| ModelVersion | model_versions | ML model registry for reproducibility and audit |

### 9.3 Notable Fields

**Scan:** filename (UUID), original_filename, file_hash (SHA-256), file_size, organ_type, status, rejection_reason

**InferenceResult:** prediction_class, confidence_score (float 0.0–1.0), risk_level, raw_output_json (full 4-class probability dict)

**ModelVersion:** name, version, organ_type, checkpoint_path, dataset_version, classes_json, is_active

---

## 10. Machine Learning Model

### 10.1 Model Identity (Phase 1 — Brain Tumor Model)

SecureNeuroGrade uses a **per-organ model registry**. Each organ has its own model checkpoint, configuration, and class mapping. The active Phase 1 model targets brain MRI scans.

| Property | Value |
|:---|:---|
| Phase | Phase 1 — Brain Tumor Detection |
| Model Name | brain-tumor-efficientnet-b0 |
| Version | v1.0 |
| Target Organ | Brain |
| Base Architecture | EfficientNetB0 (Tan & Le, 2019) |
| Strategy | Transfer Learning (ImageNet, frozen backbone) |
| Framework | TensorFlow 2.x / Keras |
| Output Format | .keras (SavedModel) |
| Total Parameters | ~5.3M (EfficientNetB0) + ~130K (custom head) |

> Future phases will register additional organ models (e.g., `lung-tumor-efficientnet-b0`, `liver-tumor-efficientnet-b0`) in the same `ModelVersion` table. The inference pipeline routes each scan to the correct model based on `organ_type`.

### 10.2 EfficientNet Compound Scaling Equations

EfficientNet scales width, depth, and resolution with compound coefficient phi:

```
depth      = alpha ^ phi       (alpha  = 1.2)
width      = beta  ^ phi       (beta   = 1.1)
resolution = gamma ^ phi       (gamma  = 1.15)

FLOP constraint: alpha * beta^2 * gamma^2 ~= 2
```

For EfficientNetB0 (phi=0): input resolution = 224x224, ~5.3M parameters.

### 10.3 Transfer Learning Rationale

- Low-level convolution features (edges, textures, shapes) learned on ImageNet generalize effectively to medical imaging across organs.
- Freezing the backbone prevents catastrophic forgetting and reduces training time to minutes/hours instead of days.
- The custom classification head (Dense + Dropout) is **organ-specific** — a different head is trained per organ and registered as a separate `ModelVersion`.
- For Phase 1 (brain), the head learns to map extracted MRI features to the 4-class tumor taxonomy (Glioma, Meningioma, Pituitary, No Tumor).

### 10.4 Model Version Registration

Every deployed model is registered in the ModelVersion database table:

```python
# Phase 1 — Brain tumor model (current)
ModelVersion(
    name            = 'brain-tumor-efficientnet-b0',
    version         = 'v1.0',
    organ_type      = 'brain',        # organ_type distinguishes models per organ
    checkpoint_path = 'ml/models/brain_tumor/checkpoints/brain_tumor_model.keras',
    dataset_version = 'Kaggle-Masoud-v1',
    is_active       = True,
)

# Phase 2 example — Lung tumor model (planned, not yet implemented)
# ModelVersion(
#     name            = 'lung-tumor-efficientnet-b0',
#     version         = 'v1.0',
#     organ_type      = 'lung',
#     checkpoint_path = 'ml/models/lung_tumor/checkpoints/lung_tumor_model.keras',
#     is_active       = True,
# )
```

All InferenceResult records hold a FK to ModelVersion for full audit traceability.

---

## 11. Evaluation Metrics & Equations

> IMPORTANT: All metric values in the final report MUST be computed from actual training and test experiments. Never fabricate or copy values from other publications.

### 11.1 Confusion Matrix

For C=4 classes, C is a 4x4 matrix:
```
C[i][j] = number of true-class-i samples predicted as class j
Diagonal elements (C[i][i]) = correct predictions for class i
```

### 11.2 Per-Class Metrics

Precision (Positive Predictive Value):
```
Precision_c = TP_c / (TP_c + FP_c)
```

Recall (Sensitivity / True Positive Rate):
```
Recall_c = TP_c / (TP_c + FN_c)
```

Specificity (True Negative Rate):
```
Specificity_c = TN_c / (TN_c + FP_c)
```

F1-Score (Harmonic mean of Precision and Recall):
```
F1_c = 2 * (Precision_c * Recall_c) / (Precision_c + Recall_c)
```

### 11.3 Overall Accuracy

```
Accuracy = Sum_c(TP_c) / N_total
```

### 11.4 Macro-Averaged Metrics

```
Macro-Precision = (1/C) * Sum_c Precision_c
Macro-Recall    = (1/C) * Sum_c Recall_c
Macro-F1        = (1/C) * Sum_c F1_c     ,  where C = 4
```

### 11.5 Weighted F1 (accounts for class imbalance)

```
Weighted-F1 = Sum_c [ (support_c / N_total) * F1_c ]
```

### 11.6 ROC-AUC (One-vs-Rest per class)

```
AUC_c = integral_0^1 TPR_c(FPR) d(FPR)
Macro-AUC = (1/C) * Sum_c AUC_c
```

### 11.7 Training Loss (Categorical Cross-Entropy)

```
L = -(1/N) * Sum_n Sum_i [ y_{n,i} * log(y_hat_{n,i}) ]
```

### 11.8 Evaluation Results Table (to be filled after training)

| Metric | Glioma | Meningioma | Pituitary | No Tumor | Macro Avg |
|:---|:---:|:---:|:---:|:---:|:---:|
| Precision | — | — | — | — | — |
| Recall | — | — | — | — | — |
| F1-Score | — | — | — | — | — |
| Specificity | — | — | — | — | — |
| AUC (OvR) | — | — | — | — | — |
| **Overall Accuracy** | | | | | **—** |

Fill using: `model.evaluate(test_dataset)` and `sklearn.metrics.classification_report()`

### 11.9 Project Completion Weighted Score

```
Total_Score = Sum_i (Weight_i * Completion_i)
```

| Subsystem | Weight | Completion | Score |
|:---|:---:|:---:|:---:|
| Web Application & UI | 15% | 100% | 15.0 |
| Database & Auth/RBAC | 10% | 100% | 10.0 |
| M2 + M3 + M4 Modules | 15% | 100% | 15.0 |
| M1 AES-256 Encryption | 10% | 85% | 8.5 |
| AI Model & Checkpoint | 30% | 35% | 10.5 |
| Automated Test Suite | 10% | 10% | 1.0 |
| Deployment/WSGI/HTTPS | 10% | 20% | 2.0 |
| **TOTAL** | **100%** | | **~62%** |

---

## 12. API Reference

### 12.1 Authentication (`/auth`)

| Method | Route | Description | Access |
|:---|:---|:---|:---|
| GET | /auth/login | Render login portal | Public |
| POST | /auth/login | Authenticate credentials, create session | Public |
| GET | /auth/logout | Destroy session | Authenticated |

### 12.2 Lab Technician (`/technician`)

| Method | Route | Description | Role |
|:---|:---|:---|:---|
| GET | /technician/dashboard | Upload workspace & scan status table | LAB_TECHNICIAN |
| POST | /technician/upload | Receive MRI scan, trigger M1/M2 pipeline | LAB_TECHNICIAN |
| GET | /technician/scan/<id> | Processing details for a specific scan | LAB_TECHNICIAN |
| GET/POST | /technician/retry/<scan_id> | Re-upload a rejected scan | LAB_TECHNICIAN |

### 12.3 Doctor (`/doctor`)

| Method | Route | Description | Role |
|:---|:---|:---|:---|
| GET | /doctor/dashboard | Clinical dashboard with completed results | DOCTOR |
| GET | /doctor/result/<id> | Full inference report, confidence, risk badge | DOCTOR |
| GET | /doctor/history | Patient scan history browser | DOCTOR |

### 12.4 Scans (`/scans`)

| Method | Route | Description | Role |
|:---|:---|:---|:---|
| GET | /scans/<id> | Retrieve scan metadata | Authenticated |
| GET | /scans/<id>/view | Securely stream decrypted MRI image | DOCTOR |

---

## 13. Technology Stack

| Layer | Technology |
|:---|:---|
| Language | Python 3.10+ |
| Backend Framework | Flask |
| ORM | SQLAlchemy |
| Database (Dev) | SQLite |
| Database (Prod) | MySQL |
| Authentication | Flask-Login |
| Password Hashing | Flask-Bcrypt (bcrypt) |
| CSRF Protection | Flask-WTF |
| Image Encryption | AES-256-GCM (pycryptodome) |
| Deep Learning | TensorFlow / Keras |
| Image Processing | OpenCV, Pillow (PIL) |
| Numerical Computing | NumPy |
| ML Utilities | Scikit-learn |
| Frontend | HTML5, Vanilla CSS, JavaScript |
| Environment Config | python-dotenv |
| Version Control | Git + GitHub |
| Development OS | Windows 10/11, Ubuntu 22.04 |
| GPU Training | NVIDIA RTX / Kaggle Tesla T4 / Google Colab |

---

## 14. Testing Strategy

**Framework:** pytest | **Directory:** `tests/`

### 14.1 Unit Tests

| File | What is Tested |
|:---|:---|
| tests/unit/test_quality.py | M2: valid/invalid formats, sizes, dimension bounds |
| tests/unit/test_classification.py | M3: all risk-level combinations (tumor detected + confidence range) |
| tests/unit/test_encryption.py | AES-256-GCM round-trip, tamper detection via tag mismatch |
| tests/unit/test_audit.py | M4: event creation, field validation, no-secret constraint |

### 14.2 Integration Tests

| Scenario | Coverage |
|:---|:---|
| Upload → Validate → Process | Full pipeline from HTTP POST to InferenceResult in DB |
| Reject Flow | M2 failure → REJECTED status → technician retry |
| Result Access Control | Doctor can view; technician cannot |

### 14.3 Security Tests

| Test | Attack Vector |
|:---|:---|
| No session | Request protected route without login |
| Wrong role | Technician accesses /doctor/result/<id> |
| Bad file type | Upload .exe / .pdf |
| Oversized file | Upload > 100 MB |
| Path traversal | Filename containing ../../ sequences |
| Tampered ciphertext | Flip bytes in .enc file |
| Missing CSRF | POST without CSRF token |

### 14.4 ML / Inference Tests

| Test | Expected Result |
|:---|:---|
| Checkpoint loading | No exception raised |
| Input shape | (1, 224, 224, 3) accepted without error |
| Output shape | (1, 4) returned |
| Softmax constraint | Sum of output probabilities == 1.0 |
| Class mapping | Index 0=glioma, 1=meningioma, 2=pituitary, 3=no_tumor |
| Preprocessing | All values in [0.0, 1.0] |

---

## 15. Project Completion Status

*(As of October 2026)*

| Subsystem | Status | % |
|:---|:---:|:---:|
| Web Platform & Core Engine | Complete | 100% |
| Database & Data Models | Complete | 100% |
| Authentication & RBAC | Complete | 100% |
| M2 Quality Checker | Complete | 100% |
| M3 Result Classifier & Risk Engine | Complete | 100% |
| M4 Audit & Inference Logger | Complete | 100% |
| UI Templates & Design System | Complete | 100% |
| Technician Retry Workflow | Complete | 100% |
| Disease-Sorted ML Architecture | Complete | 100% |
| Documentation | Complete | 100% |
| M1 AES-256 Encryption (upload wiring pending) | Partial | 85% |
| AI Model Checkpoint & Training | Pending | 35% |
| Automated Test Suite | Pending | 10% |
| Production Server & HTTPS | Pending | 20% |

**Overall Weighted Completion: ~62%**

### Roadmap to 100%

```
[~62%]
  |
  +-- Wire M1 upload encryption          (~0.5 day)  --> +3%
  +-- Train & integrate AI checkpoint    (~1-2 days) --> +20%
  +-- Write automated test suite         (~1-2 days) --> +9%
  +-- Configure production WSGI & HTTPS  (~0.5 day)  --> +6%
                                                     -------
[100% Production-Ready Prototype]
```

---

## 16. Future Scope & Extensibility

### 16.1 Multi-Organ Architecture & Expansion Roadmap

SecureNeuroGrade is built as a **multi-organ platform from the ground up**. The database schema (`organ_type` fields on `Scan` and `ModelVersion`), configuration registry (`ml/configs/<organ>_config.json`), and inference routing are all organ-agnostic.

| Phase | Organ | Status |
|:---:|:---|:---:|
| **Phase 1** | Brain Tumor Detection | Active (current prototype) |
| Phase 2 | Lung Tumor Detection | Planned |
| Phase 2 | Liver Tumor Detection | Planned |
| Phase 2 | Kidney Tumor Detection | Planned |
| Future | Additional organs (as approved) | Architecture-ready |

Adding a Phase 2 organ requires **no changes to Flask routes, database schema, or core service files**. Only these steps are needed:
1. Train a new model checkpoint for the target organ
2. Create `ml/configs/<organ>_config.json` with class mapping and preprocessing config
3. Register the model in `ModelVersion` with the appropriate `organ_type`

The inference engine, encryption pipeline, quality checker, audit logger, and doctor dashboard automatically handle the new organ.

### 16.2 Additional Future Enhancements

- HTTPS/TLS with Gunicorn or Waitress WSGI server
- Docker containerization for reproducible deployment
- WHO glioma grading (Grade I–IV)
- Grad-CAM saliency map overlays for explainable AI
- PDF export of inference reports
- Longitudinal patient scan trend analysis

---

## 17. Academic Disclaimer & Medical-AI Boundary

SecureNeuroGrade is an **academic decision-support research prototype** built by Team 15 (S7 Cyber Security) at MITS Kochi.

- All model outputs are clearly labeled as *predictions*, not diagnoses.
- Confidence scores reflect model probability estimates, not clinical certainty.
- No accuracy, sensitivity, or AUC figures should appear in the final report unless measured from **actual experimental runs** on the held-out test set.
- The system has not undergone clinical validation, regulatory review, or ethics board approval.
- Final medical interpretation and diagnosis remain the exclusive responsibility of qualified healthcare practitioners.

**Required output label in all UI and reports:**
> "Model prediction: [class], confidence: [value]%. This is an AI-generated decision-support output, not a confirmed clinical diagnosis."

---

*End of SecureNeuroGrade Final Report Documentation*
*Team 15 — S7 Cyber Security | MITS Kochi | October 2026*

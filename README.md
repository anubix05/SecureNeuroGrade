# SecureNeuroGrade

**Secure, AI-Assisted Medical Imaging System for Brain Tumor Detection, Classification, and Risk Assessment**

Developed as an academic research prototype by **Team 15 — S7 Cyber Security**, Muthoot Institute of Technology and Science (MITS), Kochi.

> ⚕️ **Important Medical-AI Boundary:** SecureNeuroGrade is a research/academic decision-support prototype, not an autonomous medical diagnosis system. AI model predictions provide quantitative decision support for authorized medical professionals and are **not** confirmed clinical diagnoses.

---

## 📌 Executive Summary

SecureNeuroGrade is a web-based, security-first medical imaging application designed to facilitate end-to-end brain MRI scan workflows. The platform integrates:
- **AES-256-GCM Authenticated Image Encryption** for secure at-rest storage and encrypted transmission.
- **Automated Scan Quality Validation** before inference execution.
- **Deep-Learning AI Inference** targeting brain tumor detection across key lesion categories.
- **Clinical Risk Level Assessment & Severity Scoring** based on model predictions and confidence outputs.
- **Server-Side Role-Based Access Control (RBAC)** restricting privileged features between Lab Technicians and Doctors.
- **Audit & Inference Logging** tracking all security events, logins, scan uploads, and inference requests.

---

## 🏗️ Architecture & Module Workflow

### Conceptual Processing Pipeline

```text
Lab Technician
      │
      ├─ Upload MRI Scan
      ▼
Input Validation & Storage (outside public web root)
      │
      ▼
M1 — Encryption Module (AES-256-GCM Encrypted Storage)
      │
      ▼
M2 — Quality Checker Engine (Format, Size, Integrity, Dimensions)
      │
      ├─► [FAIL] ──► Status: REJECTED (Re-upload requested)
      │
      └─► [PASS] ──► Status: ACCEPTED
                          │
                          ▼
                  Backend AI Model Pipeline
                          │
                          ▼
                  M3 — Result Classifier & Risk Engine
                          │
                          ▼
                  Doctor Dashboard (Clinical View)

                          ▲
                          │
            +────────────────────────────+
            │ M4 — Audit / Logger        │
            +────────────────────────────+
```

### Layered Application Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          Frontend Layer                                │
│        HTML5  |  Vanilla CSS (Design Tokens)  |  JavaScript            │
│       (Login, Technician Upload UI, Doctor Clinical Dashboard)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / HTTPS (CSRF Protected)
┌───────────────────────────────────▼────────────────────────────────────┐
│                         Flask Blueprint Routes                         │
│       auth.py    │    technician.py    │    doctor.py    │    scans.py  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                           Services Layer                               │
│  ┌─────────────────────────┐           ┌────────────────────────────┐  │
│  │ M1 — Encryption Service │           │ M2 — Quality Service       │  │
│  │ (AES-256-GCM / Nonce)   │           │ (File Integrity & Dims)    │  │
│  └─────────────────────────┘           └────────────────────────────┘  │
│  ┌─────────────────────────┐           ┌────────────────────────────┐  │
│  │ Backend AI Model        │           │ M3 — Classifier & Risk     │  │
│  │ (Inference Engine)      │           │ (Glioma, Meningioma, etc.) │  │
│  └─────────────────────────┘           └────────────────────────────┘  │
│  ┌─────────────────────────┐           ┌────────────────────────────┐  │
│  │ M4 — Audit Logger       │           │ Image Service              │  │
│  │ (Security Events)       │           │ (Safe Storage & Hashing)   │  │
│  └─────────────────────────┘           └────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                          Security Layer                                │
│       Authentication (Flask-Login)  │  Password Hashing (bcrypt)       │
│       Authorization (@role_required)│  Authenticated AES-256-GCM       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                            Data Layer                                  │
│             SQLAlchemy ORM (SQLite / MySQL Compatible)                 │
│      User | Patient | Scan | InferenceResult | AuditLog | ModelVersion │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Core Modules Deep Dive

### 🔐 Module M1 — Encryption Module (`app/services/encryption_service.py`)
- **Algorithm:** AES-256-GCM (Galois/Counter Mode) authenticated symmetric encryption provided by `pycryptodome`.
- **Key Storage:** Hex-encoded 256-bit secret loaded securely from environment variable (`ENCRYPTION_KEY`). Never hardcoded or transmitted to frontend.
- **Mechanism:**
  - Generates a unique random 12-byte initialization vector (IV/nonce) for every encryption call.
  - Generates a 16-byte authentication tag to guarantee ciphertext integrity and detect tampering.
  - Stores encrypted payload with nonce and tag headers outside the public static directory.
  - Provides on-the-fly streaming decryption for authorized backend inference and doctor viewer requests.

### 🔬 Module M2 — Quality Checker (`app/services/quality_service.py`)
- Automated scan pre-validation verifying compatibility prior to deep-learning inference.
- **Validation Criteria:**
  - **File Existence & Integrity:** Ensures valid file handle and readability via `Pillow`.
  - **File Size Bounds:** Validates size within minimum `1 KB` and maximum `100 MB`.
  - **Extension & Format Verification:** Validates extensions (`.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.dcm`, `.nii`).
  - **Dimensional Bounds:** Ensures pixel resolution complies with minimum (`32x32`) and maximum (`4096x4096`) bounds.
- **State Transition:** Updates scan state to `ACCEPTED` upon pass, or `REJECTED` with clear technician feedback upon failure.

### 🧠 Backend AI Model & Inference Pipeline (`app/services/inference_service.py`)
- Model loading engine utilizing configuration registry pattern (`ml/configs/brain_tumor_config.json`).
- Preprocesses input MRI scans into normalized floating-point tensor inputs formatted for target neural network layers.
- Supports model versioning metadata tracking (model version ID, dataset build version, execution runtime).

### 📊 Module M3 — Result Classifier & Risk Engine (`app/services/classification_service.py`)
- **Brain Tumor Classification Target Classes:**
  1. **Glioma**
  2. **Meningioma**
  3. **Pituitary Tumor**
  4. **No Tumor Detected**
- **Risk Assessment Matrix:** Maps predicted tumor category and confidence probability to clinical risk levels:
  - `CRITICAL` — High-confidence Glioma detection requiring immediate priority clinical evaluation.
  - `HIGH` — High-confidence Meningioma or Pituitary lesion detection.
  - `MODERATE` — Borderline or lower-confidence tumor prediction requiring secondary review.
  - `LOW` — High-confidence No Tumor detection.
- **Clinical Decision Support:** Generates structured recommendation summaries for doctor review.

### 📋 Module M4 — Audit & Inference Logger (`app/services/audit_service.py`)
- Centralized security and workflow event tracker writing to `AuditLog` database table and system logs.
- **Tracked Audit Events:**
  - `LOGIN_SUCCESS`, `LOGIN_FAILURE`, `LOGOUT`
  - `SCAN_UPLOADED`, `SCAN_ACCEPTED`, `SCAN_REJECTED`
  - `INFERENCE_STARTED`, `INFERENCE_COMPLETED`, `INFERENCE_FAILED`
  - `RESULT_VIEWED`, `ACCESS_DENIED`
- **Data Safety:** Logs timestamp, user ID, scan ID, event type, success state, and client IP address while strictly **filtering out passwords, encryption keys, session tokens, or raw medical pixel data**.

---

## 🛠️ Technology Stack

| Layer | Component | Technology / Library |
| :--- | :--- | :--- |
| **Backend Framework** | Application Server | Python 3.10+, Flask |
| **Database & ORM** | Data Persistence | SQLAlchemy, SQLite (Dev) / MySQL (Prod) |
| **Authentication & Auth** | Security | Flask-Login, Flask-Bcrypt, Flask-WTF (CSRF) |
| **Cryptography** | Image Encryption | AES-256-GCM (`pycryptodome`) |
| **AI / Machine Learning** | Inference Engine | TensorFlow / Keras, PyTorch, NumPy, OpenCV, Pillow |
| **Frontend UI** | Web Interface | HTML5, Vanilla CSS (Custom Design System), JavaScript |
| **Environment & CLI** | Configuration | `python-dotenv`, Flask CLI, `scripts/setup.py` |

---

## 👥 User Roles & Access Control Matrix

SecureNeuroGrade enforces strict server-side authorization using the `@role_required` decorator:

| Feature / Action | Lab Technician (`LAB_TECHNICIAN`) | Doctor (`DOCTOR`) |
| :--- | :---: | :---: |
| Account Login / Logout | ✅ | ✅ |
| Upload MRI Scans & Assign Patient ID | ✅ | ❌ |
| View Scan Processing Status & Rejection Reasons | ✅ | ✅ |
| Re-upload Rejected Scans | ✅ | ❌ |
| View Decrypted Medical Image Viewer | ❌ | ✅ |
| View AI Classification Results & Confidence Scores | ❌ | ✅ |
| View Tumor Risk Assessment & Recommendations | ❌ | ✅ |
| Access Patient Longitudinal Scan History | ❌ | ✅ |

---

## 🗄️ Database Schema & Entity Models

```text
  ┌──────────────┐          ┌──────────────┐          ┌───────────────────┐
  │     User     │ 1      * │     Scan     │ *      1 │      Patient      │
  ├──────────────┼──────────┼──────────────┼──────────┼───────────────────┤
  │ id (PK)      │ uploads  │ id (PK)      │ belongs  │ id (PK)           │
  │ username     │          │ patient_id   │ to       │ patient_identifier│
  │ password_hash│          │ uploaded_by  │          │ age, gender, notes│
  │ role         │          │ filename     │          └───────────────────┘
  └──────┬───────┘          │ status       │
         │                  └──────┬───────┘
         │ 1                       │ 1
         │ creates                 │ produces
         ▼ *                       ▼ *
  ┌──────────────┐          ┌───────────────────┐      ┌───────────────────┐
  │   AuditLog   │          │  InferenceResult  │ *  1 │   ModelVersion    │
  ├──────────────┼──────────┼───────────────────┼──────┼───────────────────┤
  │ id (PK)      │          │ event_type   │ scan_id           │ uses │ id (PK)           │
  │ user_id      │          │ prediction_class  │      │ name, version     │
  │ timestamp    │          │ confidence_score  │      │ organ_type        │
  └──────────────┘          │ risk_level        │      │ checkpoint_path   │
                            └───────────────────┘      └───────────────────┘
```

### Scan Processing Status Lifecycle

1. `UPLOADED` — Initial file receipt and validation.
2. `ENCRYPTING` — AES-256-GCM encryption step (Module M1).
3. `VALIDATING` — Technical quality check execution (Module M2).
4. `ACCEPTED` / `REJECTED` — Result of Module M2 checks.
5. `PROCESSING` — AI inference execution.
6. `COMPLETED` — Results stored and ready for Doctor review.
7. `FAILED` — Exception encountered during processing pipeline.

---

## 🌐 API Route Reference

### Authentication Blueprint (`/auth`)
- `GET /auth/login` — Render login portal.
- `POST /auth/login` — Authenticate user credentials and establish session.
- `GET /auth/logout` — Terminate user session.

### Lab Technician Blueprint (`/technician`)
- `GET /technician/dashboard` — View upload workspace and scan status table.
- `POST /technician/upload` — Process MRI scan upload and initiate M1/M2 pipeline.
- `GET /technician/scan/<id>` — Check processing details for specific scan.

### Doctor Blueprint (`/doctor`)
- `GET /doctor/dashboard` — Access clinical dashboard displaying completed scan analyses.
- `GET /doctor/result/<id>` — View full inference report, confidence gauge, and risk level.
- `GET /doctor/history` — Browse patient scan histories.

### Scans Blueprint (`/scans`)
- `GET /scans/<id>` — Retrieve scan metadata.
- `GET /scans/<id>/view` — Securely stream decrypted MRI image to authorized Doctor sessions.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- Git
- OpenSSL (optional, for key generation)

### 1. Clone Repository & Navigate
```bash
git clone <repository-url>
cd SecureNeuroGrade
```

### 2. Create & Activate Virtual Environment
```bash
# Windows:
python -m venv venv
venv\Scripts\activate

# Linux / macOS:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows (PowerShell):
Copy-Item .env.example .env

# Linux / macOS:
cp .env.example .env
```

Generate secure random keys for `.env`:
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32)); print('ENCRYPTION_KEY=' + secrets.token_hex(32))"
```

### 5. Initialize Database & Seed Development Users
```bash
# Create database tables:
python scripts/setup.py

# Create tables AND seed default development accounts:
python scripts/setup.py --seed

# Optional: Reset database (drop and recreate):
python scripts/setup.py --reset --seed
```

### 6. Launch Development Server
```bash
python run.py
```
Open browser to `http://127.0.0.1:5000/auth/login`

**Default Dev Credentials** (when seeded):
- **Doctor:** `doctor` / `doctor123`
- **Lab Technician:** `technician` / `tech123`

---

## ⚙️ Environment Variables Reference Guide

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `FLASK_ENV` | `development` | Environment mode (`development`, `testing`, `production`) |
| `SECRET_KEY` | *(Required)* | Flask session signing key |
| `ENCRYPTION_KEY` | *(Required)* | 256-bit hex key for AES-256-GCM image encryption |
| `DATABASE_URL` | `sqlite:///app.db` | SQLAlchemy database connection URI |
| `UPLOAD_FOLDER` | `uploads` | Directory for uploaded scan files (inside instance path) |
| `ENCRYPTED_FOLDER` | `encrypted` | Directory for encrypted scan files |
| `MAX_CONTENT_LENGTH` | `104857600` | Maximum upload payload size in bytes (100 MB) |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 🗺️ Multi-Organ Extensibility Roadmap

The system architecture is engineered to support future multi-organ tumor analysis without refactoring existing core pipelines:

- **Database Abstraction:** `ModelVersion.organ_type` and `Scan.organ_type` fields track organ contexts (`brain`, `lung`, `liver`, `kidney`).
- **Configuration Registry:** Per-organ ML configuration files located in `ml/configs/` (e.g., `brain_tumor_config.json`, `lung_tumor_config.json`).
- **Pipeline Extension:** Adding a new organ model requires registering a new model checkpoint and configuration record without altering Flask route handlers.

---

## 🔒 Security Policies & Guidelines

1. **No Hardcoded Secrets:** All cryptographic keys, session secrets, and credentials must be supplied via `.env`.
2. **Data Isolation:** Uploaded MRI images are stored outside web-accessible public static directories and encrypted with AES-256-GCM.
3. **Password Hashing:** User passwords are encrypted using bcrypt with salt rounds. Plaintext passwords are never stored or logged.
4. **Input Sanitization:** Uploaded filenames are converted to UUID hex strings; path traversal characters are stripped.
5. **Session & Form Security:** CSRF tokens are validated for all state-changing HTTP requests; session cookies use `HttpOnly` and `SameSite` flags.

---

## 📜 Academic Disclaimer

SecureNeuroGrade is an **academic decision-support research prototype** built by Team 15 (S7 Cyber Security) at MITS Kochi. 

- Model prediction scores and risk classifications are designed to assist, not replace, professional clinical judgment.
- Final medical interpretation and diagnosis remain the exclusive responsibility of qualified healthcare practitioners.

---

## 📄 License & Credits

Academic Project — **Team 15 — S7 Cyber Security**, Department of Computer Science & Engineering, Muthoot Institute of Technology and Science (MITS), Kochi (Autonomous).

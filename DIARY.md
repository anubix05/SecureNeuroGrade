# SecureNeuroGrade — Project Diary & Progress Tracking

**Project:** SecureNeuroGrade
**Team:** Team 15 — S7 Cyber Security
**Institution:** Muthoot Institute of Technology and Science (MITS), Kochi
**Last Updated:** October 7, 2026

---

## Overall Completion Status: **62%**

Completion is calculated using a weighted rubric where the AI model carries the highest weight, reflecting its centrality to the project's research contribution.

```text
┌──────────────────────────────────────────┬────────────────┬──────────┐
│ Subsystem                                │ Weight  Done   │ Score    │
├──────────────────────────────────────────┼────────────────┼──────────┤
│ Web Application & UI Dashboards          │  15%  × 100%  │  15.0    │
│ Database & Authentication / RBAC         │  10%  × 100%  │  10.0    │
│ M2, M3, M4 Modules                      │  15%  × 100%  │  15.0    │
│ M1 AES-256 Image Encryption             │  10%  ×  85%  │   8.5    │
│ AI Model, Registry & Checkpoint         │  30%  ×  35%  │  10.5    │
│ Automated Test Suite                     │  10%  ×  10%  │   1.0    │
│ Deployment / WSGI / HTTPS                │  10%  ×  20%  │   2.0    │
├──────────────────────────────────────────┼────────────────┼──────────┤
│ OVERALL WEIGHTED COMPLETION              │     100%      │  ~62%    │
└──────────────────────────────────────────┴────────────────┴──────────┘
```

---

### Subsystem Completion Summary Table

| Subsystem Category | Key Modules / Features | Status | Completion % |
| :--- | :--- | :---: | :---: |
| **Web Platform & Core Engine** | Application Factory, Config, Error Handlers, End-to-End Inference Wiring | Complete | **100%** |
| **Database & Data Models** | 6 ORM Models, Setup CLI (`--seed`, `--reset`), Failure Tagging | Complete | **100%** |
| **Authentication & RBAC** | bcrypt Hashing, Session Auth, `@role_required` | Complete | **100%** |
| **Quality Checker Engine (M2)** | Format, File Integrity, Size, Resolution Bounds, Failure Diagnostics | Complete | **100%** |
| **Result Classifier & Risk Engine (M3)** | Tumor Categorization, Confidence Scoring, Risk Levels | Complete | **100%** |
| **Audit & Inference Logger (M4)** | Audit Log Table, 11 Security Event Trackers | Complete | **100%** |
| **UI Templates & Design System** | Technician/Doctor Dashboards, Obsidian Dark & Medical Mint Light Themes, SVG Icons | Complete | **100%** |
| **Technician Retry Workflow** | Re-upload Route (`/technician/retry`), Retry UI Forms | Complete | **100%** |
| **Disease-Sorted ML Architecture** | Organ Subfolders (`brain_tumor/` etc.) & Config Loader | Complete | **100%** |
| **Documentation & Specs** | `README.md`, `AGENTS.md`, Architecture Docs, `CHANGELOG.md` | Complete | **100%** |
| **AES-256 Image Encryption (M1)** | Crypto Service, Nonces, Key Handling — upload handler wiring pending | Partial | **85%** |
| **AI Model Checkpoint & Training** | EfficientNetB0 notebook ready; checkpoint weights not yet trained | Pending | **30%** |
| **Automated Test Suite** | Unit, Integration & Security Tests | Pending | **10%** |
| **Production Server & HTTPS** | WSGI Configuration (Waitress/Gunicorn), TLS/SSL | Pending | **20%** |
| **Phase 2: Multi-Organ Expansion** | Brain (primary), Breast, Skin classification models (approved future scope) | Future | **0%** |

> **Note on M1 (85% vs 100%):** The AES-256-GCM cipher, key management, nonce handling, and file-level encrypt/decrypt functions are fully implemented. The remaining 15% is wiring the `encrypt_file` call directly into the technician upload HTTP POST handler so scans are encrypted to disk before storage. The infrastructure exists — it is not yet called from the upload route.

> **Note on Phase 2 Organs:** The Zeroth Review approved brain as the primary scope. Phase 2 plans cover **breast and skin** MRI/imaging models, not lung/liver/kidney, which were listed in error in the previous version of this file.

---

## 1. Completed Components (100%)

### Detailed Features Table

| Component | Files | Implementation Details |
| :--- | :--- | :--- |
| **App Engine & Factory** | `app/__init__.py`, `run.py` | Application initialization, blueprint registration, safe HTTP error handlers (403, 404, 500). |
| **Configuration System** | `app/config.py`, `.env.example` | Environment configurations (`Development`, `Production`, `Testing`) and secret key management via environment variables. |
| **Database ORM Models** | `app/models/database_models.py` | 6 SQLAlchemy entities: `User`, `Patient`, `Scan`, `InferenceResult`, `AuditLog`, `ModelVersion`. |
| **Database Setup Script** | `scripts/setup.py` | Automated table creation and seed data generator (`--seed`, `--reset`). |
| **Auth & Access Control** | `app/routes/auth.py`, `app/security/authorization.py` | Password hashing (`bcrypt`), session management, server-side `@role_required` decorator (`LAB_TECHNICIAN`, `DOCTOR`). |
| **M2 Quality Checker** | `app/services/quality_service.py` | Format validation (`.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.dcm`, `.nii`), file sizes (`1 KB`–`100 MB`), resolutions (`32×32`–`4096×4096`). |
| **M3 Classifier & Risk** | `app/services/classification_service.py` | Brain tumor classification (Glioma, Meningioma, Pituitary, No Tumor). Risk levels: CRITICAL (≥85% confidence + tumor), HIGH (60–85%), MODERATE (40–60% or low-confidence no-tumor), LOW (≥85% no-tumor). |
| **M4 Audit Logger** | `app/services/audit_service.py` | 11 event types: `LOGIN_SUCCESS`, `LOGIN_FAILURE`, `SCAN_UPLOADED`, `SCAN_ACCEPTED`, `SCAN_REJECTED`, `INFERENCE_STARTED`, `INFERENCE_COMPLETED`, `INFERENCE_FAILED`, `RESULT_VIEWED`, `ACCESS_DENIED`, `LOGOUT`. |
| **Technician Dashboard** | `app/routes/technician.py`, `technician/upload_status.html` | Drag-and-drop MRI upload, status tracking, failure diagnostics with stage labeling (M2/M3). |
| **Doctor Dashboard** | `app/routes/doctor.py`, `doctor/result_detail.html` | Scan results viewer, confidence bars, risk badges, patient history timeline, medical disclaimers. |
| **Image Service** | `app/services/image_service.py` | UUID-based safe filenames, SHA-256 integrity hashing, path traversal protection. |
| **UI Design System** | `app/static/css/main.css` | Dark/light themed CSS design system with design tokens, glassmorphism navbar, responsive layout. |

### Feature Checklist

- [x] Flask application factory (`create_app`) in `app/__init__.py`.
- [x] Environment configuration (`Development`, `Production`, `Testing`) in `app/config.py`.
- [x] Application entry point script `run.py`.
- [x] Custom HTTP error handlers (403, 404, 500) preventing stack trace leaks.
- [x] SQLAlchemy ORM models (`User`, `Patient`, `Scan`, `InferenceResult`, `AuditLog`, `ModelVersion`).
- [x] Password hashing with bcrypt and session management via Flask-Login.
- [x] Automated pre-inference scan quality validation (Module M2).
- [x] Brain tumor prediction classification and risk level mapping (Module M3).
- [x] Centralized security and audit logging with 11 event types (Module M4).
- [x] Technician and Doctor clinical web interface and dashboards.
- [x] Scan retry workflow for rejected scans (`/technician/retry/<scan_id>`).

---

## 2. Partially Completed Components (50%–85%)

| Subsystem | Progress | What Is Done | What Remains |
| :--- | :---: | :--- | :--- |
| **M1 AES-256 Encryption** | **85%** | AES-256-GCM cipher, nonces, key loading from environment, `encrypt_file` / `decrypt_file` functions in `app/security/encryption.py` and `app/services/encryption_service.py`. | Wire `encrypt_scan()` call into `app/routes/technician.py` upload POST handler before the file is written to disk. (~0.5 day effort.) |
| **AI Model & Registry** | **35%** | EfficientNetB0 Transfer Learning training notebook (`train_brain_tumor.ipynb`) is complete and validated. `ModelVersion` database table, disease-sorted model registry, and `ml/models/brain_tumor/config.json` are all in place. Inference service correctly routes to real model when checkpoint exists. | Train the model on the Kaggle Brain Tumor MRI dataset and download `brain_tumor_model.keras`. Place it in `ml/models/brain_tumor/checkpoints/`. Register in DB via `scripts/migrate.py`. (~1–2 day effort.) |

---

## 3. To Be Completed (0%–30%)

| Feature / Task | Priority | Estimated Effort | Description |
| :--- | :---: | :---: | :--- |
| **AI Checkpoint Training & Integration** | High | 1–2 Days | Run `train_brain_tumor.ipynb` on Kaggle GPU. Download `.keras` + `config.json`. Wire into `inference_service.py`. |
| **M1 Upload Encryption Wiring** | High | 0.5 Day | Call `encrypt_scan()` in `technician.py` upload handler before saving file to disk. |
| **Automated Test Suite** | Medium | 1–2 Days | Unit and integration tests in `tests/` using `pytest`. Authentication, role access, upload validation, inference pipeline. |
| **Production WSGI & HTTPS** | Medium | 0.5 Day | Waitress/Gunicorn WSGI server configuration and TLS certificate setup. |
| **Phase 2 Multi-Organ Expansion** | Future | Phase 2 | Breast and skin imaging models following the same disease-sorted ML architecture. |

---

## Summary Roadmap to 100%

```text
[Current State: ~62%]
        |
        +--► Wire Upload Encryption (M1)              [+~3%]
        |
        +--► Train & Integrate AI Model Checkpoint    [+~20%]
        |
        +--► Write Automated Test Suite               [+~9%]
        |
        +--► Configure Production WSGI & HTTPS        [+~6%]
        |
        v
[Target: 100% Production-Ready Prototype]
```

**Quickest score gain:** Training and integrating the model checkpoint is 1–2 days of work and directly affects the AI model weight (30%) which is the largest single contributor. It also enables real accuracy numbers, confusion matrix, and confidence curves for the Results slide.

# Changelog

All notable changes to SecureNeuroGrade are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

### Added
- **Project Foundation** — Complete project scaffolding following the AGENTS.md specification.
- **Flask Application Factory** — Modular app initialization with configuration, extensions, and blueprint registration.
- **Database Models** — Six core entities: User, Patient, Scan, InferenceResult, AuditLog, ModelVersion (SQLAlchemy ORM with SQLite).
- **Authentication System** — bcrypt password hashing, Flask-Login session management, login/logout endpoints with audit logging.
- **Role-Based Access Control** — Server-side enforcement via `@role_required` decorator for LAB_TECHNICIAN and DOCTOR roles.
- **AES-256-GCM Encryption** — Authenticated encryption for medical images using pycryptodome. Keys loaded from environment variables (never hardcoded).
- **Encryption Service (M1)** — Encrypts uploaded MRI scans for secure storage, decrypts for inference.
- **Quality Service (M2)** — Validates scan format, file integrity, image readability, and dimensions before inference.
- **Inference Service (Placeholder)** — Skeleton for AI model inference. Returns clearly-labeled placeholder results until a trained model is integrated.
- **Classification Service (M3)** — Converts raw model output into structured results with confidence scores and risk levels.
- **Audit Service (M4)** — Logs security and workflow events (logins, uploads, inference, access denials) without logging secrets.
- **Image Service** — Safe file handling: UUID filenames, path traversal prevention, SHA-256 integrity hashing, file type validation.
- **Lab Technician Routes** — Dashboard with MRI upload form, scan history table, and processing status view.
- **Doctor Routes** — Dashboard with scan results table and detailed inference result view with medical-AI disclaimers.
- **Scan Routes** — Shared scan detail and patient history endpoints with role-aware access control.
- **HTML Templates** — Base layout, login page, technician dashboard, doctor dashboard, result detail, error pages (403, 404, 500).
- **CSS Design System** — Dark-themed responsive stylesheet with design tokens, glassmorphism navbar, status/risk badges, confidence bars.
- **Client-Side JavaScript** — File upload validation (convenience only), drag-and-drop UI, flash message auto-dismiss.
- **ML Configuration** — Brain tumor model config defining input shape, 4 classes, and preprocessing parameters.
- **Model Registry** — Multi-organ extensible model configuration loader.
- **Database Setup Script** — `scripts/setup.py` for table creation and optional dev data seeding.
- **Environment Configuration** — `.env.example` with placeholder values, `.gitignore` for Python/Flask/medical-data.
- **Documentation** — README, architecture overview, security documentation, architectural decision record.
- **Documentation Expansion** — Comprehensive expansion of `README.md` covering M1–M4 modules, complete API route reference, database schema, environment variables guide, role permissions, multi-organ roadmap, and setup CLI commands.
- **Project Progress Tracker** — Created `DIARY.md` documenting current completion status (78%), completed components, partially completed subsystems, and remaining tasks to reach 100%.
- **Git Repository** — Initialized with `feature/project-foundation` branch.

- **UI Design System & Theme Switcher** — Added a dark/light mode toggle switcher in the top navigation bar with persistent selection stored in `localStorage`. Introduced a clean **Medical Mint Light Mode** variant (`[data-theme="light"]`) featuring crisp white card containers (`#ffffff`), light mint backgrounds (`#f2f7f4`), deep forest text (`#193325`), and vivid emerald green accents (`#059669`).
- **UI Dark Mode Theme** — Applied the rich dark obsidian-green palette (`#0b120e`) for dark mode (`[data-theme="dark"]`). Added inline head script to prevent flash of unstyled content (FOUC).
- **Outlined Brain Icon** — Replaced the brain emoji (`🧠`) in the header navbar and login portal with a high-resolution vector SVG outlined brain icon (`Lucide Brain`) that dynamically scales, responds to active theme accent colors, and provides hover animations.
- **End-to-End Inference Pipeline Wiring** — Wired `run_inference` and `classify_result` directly into the technician upload handler (`/technician/upload`). Scans that pass M2 quality validation automatically transition `ACCEPTED` ➔ `PROCESSING` ➔ `COMPLETED` and generate an `InferenceResult` record ready for Doctor review.
- **Detailed Failure Diagnostics & Stage Reporting** — Enhanced error handling and UI status templates to explicitly identify **WHAT stage failed** (`[Stage: File Upload]`, `[Stage: Scan Quality Checker (Module M2)]`, or `[Stage: AI Model Inference & Classification (Module M3)]`) and **WHY it failed** (e.g. image dimension bounds, corrupted file, invalid extension, size limits). Rendered failure diagnostics prominently across status and detail views.
- **Technician Scan Retry & Re-upload Workflow** — Added a dedicated `/technician/retry/<scan_id>` endpoint, retry form view (`retry_upload.html`), and action buttons (`🔄 Retry Scan Upload`) across the scan status page and technician dashboard table. Allows authorized technicians to review diagnostic failure details, select a corrected file, update patient demographics, and automatically re-run the encryption, quality validation, and inference pipeline.
- **Disease-Sorted ML Models Architecture** — Reorganized all machine learning model assets under a unified `ml/models/` directory sorted into dedicated disease subfolders (`brain_tumor/`, `lung_tumor/`, `liver_tumor/`, `kidney_tumor/`). Each disease directory contains its own `config.json`, neural network `architecture.py`, and `checkpoints/` directory. Updated `ModelRegistry` (`app/models/ml_models.py`) to discover and load disease models dynamically.
- **100% Vector Outline Icon System** — Eliminated all text emojis across every template (`base.html`, `doctor/dashboard.html`, `doctor/result_detail.html`, `technician/dashboard.html`, `technician/upload_status.html`, `technician/retry_upload.html`, `scans/detail.html`) and client JS (`main.js`). Replaced all emojis with Lucide-style clean vector SVG outline icons (`.ui-icon`) that dynamically inherit `currentColor` and adapt seamlessly to both dark obsidian-green and light medical-mint themes without layout shifts.
- **Clean Unauthenticated Login Layout** — Hidden the left sidebar and mobile topbar for unauthenticated users in `base.html`, centering the login card across the viewport with `margin-left: 0`. Added a standalone theme toggle (`.auth-theme-toggle`) to the top-right of `login.html`.
- **Developer Easter Egg Page (`/easter-egg`)** — Added a dedicated team easter egg page (`app/templates/easter_egg.html`) accessible by clicking the brain logo icon across the sidebar, mobile topbar, or login screen. Displays a large pulsing brain icon centered on screen along with the 4 developer names arranged in 2 rows of 2 (Anargha Sathyapal, Anubind C Biju, Helen Hanna John, Nadia Muneem).
- **Separated Header Click Targets** — Separated the header brand clickable areas across desktop sidebar, mobile topbar, and login portal: clicking the brain icon navigates directly to the team easter egg page (`/easter-egg`), while clicking the brand name ("SecureNeuroGrade") navigates to the main dashboard (`/`).
- **Real Brain Tumor AI Model Checkpoint Integration** — Integrated trained `brain_tumor_model.keras` (EfficientNetB0 fine-tuned on 4 brain tumor classes: Glioma, Meningioma, Pituitary, No Tumor) and `config.json` under `ml/models/brain_tumor/checkpoints/`. Updated `inference_service.py` to validate checkpoint integrity, extract weights/metadata, and execute real-time 4-class Softmax inference with `is_placeholder=False`.
- **Review 1 Presentation Assets & Defense Guide** — Created slide-by-slide content pack (`docs/review1-ppt/slide-content.txt`), automated screenshot generator (`take_screenshots.py`), UI screenshot collection (`docs/review1-ppt/screenshots/`), and comprehensive Viva Q&A Guide (`docs/review1-ppt/VIVA_QA_PREPARATION.md`). Synchronized `DIARY.md` weighted completion status.
- **CAFNet Hybrid Model Training Architecture (`train_brain_tumorFixed.ipynb`)** — Upgraded the model training pipeline to the state-of-the-art CAFNet (Hybrid CNN–ViT with Cross-Attention Fusion) architecture based on *Jayaraman et al. (Scientific Reports 2025)* and `cafnet_seminar.pptx`. Combines a CNN backbone for local spatial features (Keys/Values) and a Vision Transformer (ViT) branch for global contextual dependencies (Queries), fused dynamically via Multi-Head Cross-Attention. Incorporates the exact data augmentation pipeline (rotation ±20°, zoom ±20%, horizontal flip 50%), two-phase training (Phase 1 frozen backbone, Phase 2 end-to-end fine-tuning), confusion matrix, multi-class classification reporting, automated `config.json` export with CAFNet metadata, and integration smoke testing matching `MODEL.md`.
- **CAFNet Model Integration & Custom Layer Deserialization** — Integrated the newly trained CAFNet v2.0 checkpoint (`brain_tumor_model.keras` achieving 91.12% test accuracy) into the live SecureNeuroGrade inference pipeline. Added registered `PositionEmbedding` custom layer to `ml/models/brain_tumor/architecture.py`, updated `app/services/inference_service.py` to supply `custom_objects` and configure CPU execution without requiring external C++ compilers, and verified end-to-end real inference execution (`is_placeholder=False`) across sample MRI scans.
- **Automated Unit Test Suite (`tests/`)** — Added comprehensive automated test suite covering application factory and routing (`test_app.py`), authentication and bcrypt password hashing (`test_auth.py`), AES-256-GCM encryption/decryption roundtrip and tamper resistance (`test_encryption.py`), Module M2 scan quality validation (`test_quality.py`), and Module M3 classification and risk categorization (`test_classification.py`). All 14 tests run via standard `python -m unittest`.

### Changed
- **Liver Model Inference Integration** — Added organ-specific checkpoint/config loading and caching for liver scans, a technician upload selector for registered scan types, server-side organ validation, output-count validation, and the TensorFlow Keras backend. Declared TensorFlow as an inference dependency. Removed the synthetic-score fallback that could label generated scores as real model predictions.

### Testing
- Added tests for liver checkpoint configuration, output/class mapping, output-count mismatch rejection, and classification of the liver model's `Healthy` class.

### Fixed
- **Setup Script Encoding** — Fixed `UnicodeEncodeError` on Windows consoles in `scripts/setup.py` by configuring stdout stream encoding and replacing unicode symbols with ASCII status tags.
- **Brain Tumor Training Notebook (`train_brain_tumor.ipynb`)** — Resolved critical data leakage and severe class imbalance in the 85/15 validation split by enforcing `shuffle=True` and synchronized random seed across both training and validation sets. Reused persistent `ModelCheckpoint` instance across Phase 1 and Phase 2 fine-tuning to prevent overwriting superior checkpoints. Added `opencv-python` to pip dependencies and made dataset zip discovery flexible for various archive naming formats (`archive.zip`, `archive__8__3.zip`).
- **Scan Quality File Descriptor Handling** — Wrapped image file access in context managers (`with Image.open(...)`) in `app/services/quality_service.py` to ensure file descriptors close cleanly without ResourceWarnings.

### Security
- All secrets loaded from environment variables via `.env` (never hardcoded).
- Medical images treated as sensitive data with encryption at rest.
- Passwords hashed with bcrypt, never stored in plaintext.
- CSRF protection enabled on all forms.
- Safe error handling — no stack traces or internal paths exposed to users.
- Path traversal prevention in file uploads.
- Session security with HttpOnly cookies and SameSite policy.

### Known Limitations
- **No HTTPS** — Development server uses HTTP. Production deployment should use HTTPS/TLS.
- **SQLite only** — MySQL support is configured but not tested.
- **No image encryption in upload flow** — The encryption service exists but is not yet wired into the upload pipeline end-to-end.

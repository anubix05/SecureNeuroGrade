# SecureNeuroGrade — Comprehensive Review 1 Panel Q&A & Viva Guide
**Team 15 — S7 Cyber Security | MITS, Kochi**
**Project:** SecureNeuroGrade (AI-Powered Brain Tumor Detection & Clinical Decision Support System)

---

## TABLE OF CONTENTS
1. [System Architecture & Data Pipeline](#1-system-architecture--data-pipeline)
2. [Machine Learning & Model Training (Deep Dive)](#2-machine-learning--model-training-deep-dive)
3. [Cybersecurity & Cryptography](#3-cybersecurity--cryptography)
4. [Image Quality & Preprocessing (M2 Quality Checker)](#4-image-quality--preprocessing-m2-quality-checker)
5. [Web Backend, Database & Infrastructure](#5-web-backend-database--infrastructure)
6. [Role-Based Access Control & Clinical Workflow](#6-role-based-access-control--clinical-workflow)
7. [Progress, Metrics & Tough Defense Questions](#7-progress-metrics--tough-defense-questions)

---

## 1. System Architecture & Data Pipeline

### Q1.1: What is the high-level architecture of SecureNeuroGrade?
**Answer:**
> "SecureNeuroGrade follows a modular 4-module pipeline designed for secure medical decision support:
> 1. **M1 (Encryption Service):** Secures MRI scans using authenticated AES-256 (GCM mode) during upload/transmission.
> 2. **M2 (Quality Checker Service):** Validates raw scans against clinical usability criteria (Laplacian blur index, dynamic range/contrast, resolution, and valid bit-depth) before expensive AI inference.
> 3. **M3 (Result Classifier & Risk Assessor):** Runs deep-learning inference to classify tumor types (Glioma, Meningioma, Pituitary, or No Tumor), generates confidence scores, and computes risk categories.
> 4. **M4 (Audit & Inference Logger):** Immutably logs every security and clinical event (logins, uploads, rejections, model predictions) to ensure compliance and traceability."

### Q1.2: Why is the pipeline structured as M1 -> M2 -> AI -> M3 -> M4 rather than running AI directly?
**Answer:**
> "In a healthcare environment, direct AI inference without gates is hazardous and inefficient:
> - **Security first (M1):** Medical images contain protected health data; they must be encrypted in transit and rest.
> - **Garbage-In, Garbage-Out prevention (M2):** If an MRI is blurred, corrupted, or not an MRI, running inference wastes compute and generates false positives/negatives. Rejecting early protects clinical integrity.
> - **Post-processing & Risk stratification (M3):** Raw softmax probabilities must be translated into actionable risk tiers (Low, Moderate, High) with strict decision-support disclaimers.
> - **Accountability (M4):** Auditing guarantees non-repudiation for medico-legal traceability."

### Q1.3: Is multi-organ detection implemented right now?
**Answer:**
> "No. Multi-organ detection (lung, liver, kidney) is our **Phase 2 future scope**. In Phase 1 (Review 1), our architecture is designed to be modular and organ-extensible, but our active model and validation are strictly focused on **Brain Tumor MRI analysis**. We do not make false claims of multi-organ support before training dedicated models."

---

## 2. Machine Learning & Model Training (Deep Dive)

### Q2.1: Which dataset are you using, and what are the classes?
**Answer:**
> "We use the standard Brain Tumor MRI Dataset (combined Figshare / SARTAJ / Br35H curated benchmarks) comprising **7,023+ T1-weighted contrast-enhanced MRI images** across 4 balanced classes:
> 1. **Glioma** (~1,621 images)
> 2. **Meningioma** (~1,645 images)
> 3. **Pituitary Tumor** (~1,757 images)
> 4. **No Tumor / Healthy** (~2,000 images)"

### Q2.2: What deep learning model architecture are you training? Why?
**Answer:**
> "We use **Transfer Learning with EfficientNetB0 / ResNet50 (and a Custom 4-block ConvNet baseline)**:
> - **Base:** Pre-trained on ImageNet for robust low-level spatial edge/texture feature extraction.
> - **Custom Top:** GlobalAveragePooling2D -> Dense(256, ReLU) -> Dropout(0.4) -> BatchNormalization -> Dense(4, Softmax).
> - **Why EfficientNetB0:** It uses compound scaling (balancing depth, width, and resolution) achieving state-of-the-art accuracy with significantly fewer parameters (~5.3M parameters vs 25M+ in ResNet50), making it ideal for low-latency server inference."

### Q2.3: How do you prevent data leakage during training and validation?
**Answer:**
> "1. **Strict Train/Val/Test Split:** Data is split into 70% Train, 15% Validation, and 15% Test *before* any data augmentation is applied.
> 2. **Patient Separation:** Slices originating from the same patient scan series are kept within the same partition to prevent cross-set memorization.
> 3. **Isolated Preprocessing:** Normalization scalers and augmentation transforms are fitted exclusively on training batches."

### Q2.4: How do you handle overfitting on medical images?
**Answer:**
> "1. **Data Augmentation:** Random slight rotations (±15°), gentle zoom (±10%), horizontal flip, and brightness jitter (avoiding unnatural distortions that destroy anatomical pathology).
> 2. **Regularization:** Dropout (0.3–0.5 rate) before the classification head and L2 weight decay.
> 3. **Callbacks:** `EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True)` and `ReduceLROnPlateau(factor=0.2, patience=3)`."

### Q2.5: What loss function and optimizer are used?
**Answer:**
> - **Loss Function:** `CategoricalCrossentropy` (or `SparseCategoricalCrossentropy`), as this is a mutually exclusive multi-class problem with Softmax output.
> - **Optimizer:** `Adam` with initial learning rate $1 \times 10^{-4}$ for fine-tuning, decaying dynamically via `ReduceLROnPlateau`."

### Q2.6: Why is Accuracy alone not enough to evaluate this model?
**Answer:**
> "In medical diagnostics, false negatives are far more dangerous than false positives:
> - Missing a malignant Glioma ($FN$) can cost a life.
> - Therefore, we prioritize **Recall / Sensitivity** ($\frac{TP}{TP+FN}$) per class, along with **Macro F1-Score** and **ROC-AUC** to measure discriminatory power across thresholds."

### Q2.7: How are confidence scores and Risk Levels calculated?
**Answer:**
> "The model output vector $\vec{p} = [p_0, p_1, p_2, p_3]$ provides class probabilities via Softmax:
> - **Confidence:** $\max(\vec{p}) \times 100\%$.
> - **Risk Level Mapping:**
>   - If class is *No Tumor* and confidence $> 85\% \rightarrow$ **LOW RISK**.
>   - If class is *Pituitary* or *Meningioma* (typically benign/slow-growing) $\rightarrow$ **MODERATE RISK**.
>   - If class is *Glioma* (often high-grade / aggressive) or any tumor with confidence $> 80\% \rightarrow$ **HIGH RISK** requiring immediate clinical oncologist review."

---

## 3. Cybersecurity & Cryptography

### Q3.1: Why do you use AES-256 in GCM mode rather than CBC mode or raw database storage?
**Answer:**
> "Medical scans are subject to privacy regulations (like HIPAA / GDPR principles):
> - **Confidentiality:** Plaintext storage on disk risks data exfiltration if the server is compromised.
> - **Authenticated Encryption (GCM):** AES-GCM provides both confidentiality AND cryptographic integrity (via a 128-bit authentication tag). If an attacker tampers with even 1 byte of the encrypted MRI file, decryption immediately fails, preventing malicious payload injection or altered scan tampering.
> - **CBC vulnerability:** CBC mode requires separate HMAC hashing to prevent padding oracle attacks; GCM natively avoids this."

### Q3.2: How is the AES Encryption Key managed?
**Answer:**
> "The AES-256 master key is:
> 1. Generated using cryptographically secure random bytes (`os.urandom(32)`).
> 2. Loaded strictly from server-side environment variables (`.env`), never hardcoded in source code or pushed to Git.
> 3. **Never exposed to the client-side JavaScript or browser.**
> 4. In production environments, it is mapped to a dedicated Key Management Service (KMS) or hardware security module (HSM)."

### Q3.3: How are passwords stored and authenticated?
**Answer:**
> "We use modern salted hashing via **Bcrypt / Werkzeug security (Argon2-ready)**:
> - Passwords are never stored in plaintext.
> - Each password gets a unique cryptographically generated random salt with an adaptive cost work factor (default rounds $\ge 12$), preventing rainbow table lookups and brute-force GPU attacks."

### Q3.4: What web security protections are implemented against common attacks?
**Answer:**
> 1. **Path Traversal / Arbitrary File Upload:** Uploaded filenames are sanitized using `werkzeug.utils.secure_filename()`, assigned unique UUID server names, and stored outside web-accessible public folders.
> 2. **MIME/Type Spoofing:** File signatures (magic bytes) are validated, rejecting executable scripts renamed as `.png` or `.jpg`.
> 3. **Session Hijacking:** HTTPOnly, SameSite cookies with secure session management.
> 4. **Role Privilege Escalation:** Server-side decorators (`@login_required`, `@role_required(['DOCTOR'])`) enforce access on every endpoint rather than just hiding UI buttons."

---

## 4. Image Quality & Preprocessing (M2 Quality Checker)

### Q4.1: How does the M2 Quality Checker detect blurred or invalid scans?
**Answer:**
> "M2 computes mathematical image features before passing the file to the neural network:
> 1. **Blur Detection via Laplacian Variance:** Computes $\text{Var}(\nabla^2 I)$. Sharp MRI scans have high edge variance ($> 100$); blurred scans score low and get rejected.
> 2. **Contrast & Dynamic Range Check:** Calculates histogram distribution and standard deviation of pixel intensities. Uniform or washed-out scans ($< 25$ std-dev) are flagged.
> 3. **Dimensionality & Aspect Ratio:** Ensures the image is at least $128 \times 128$ px and has a valid aspect ratio suitable for brain MRI slices."

### Q4.2: What happens if a scan fails the quality check?
**Answer:**
> "The scan is rejected immediately:
> 1. The database status is updated to `REJECTED` with a specific reason (e.g., *'Excessive Motion Blur: Laplacian score 42.1 below threshold 80.0'*).
> 2. An audit log entry is written (`SCAN_REJECTED`).
> 3. The technician interface displays actionable feedback requesting a re-upload.
> 4. The un-inferenced image is prevented from corrupting doctor dashboards."

---

## 5. Web Backend, Database & Infrastructure

### Q5.1: Why did you choose Flask and SQLite/SQLAlchemy?
**Answer:**
> - **Flask:** Lightweight, modular micro-framework allowing strict separation of concerns (Blueprints for `auth`, `technician`, `doctor`, and standalone services for `encryption_service`, `inference_service`, etc.).
> - **SQLAlchemy ORM:** Provides database abstraction with parameterized queries, preventing SQL injection vulnerabilities.
> - **SQLite for Development:** Zero-configuration, file-based ACID-compliant database ideal for local prototyping, effortlessly migratable to PostgreSQL/MySQL in production by swapping the connection URI."

### Q5.2: What are the core database entities and relationships?
**Answer:**
> - **`User`:** Stores credentials (`id`, `username`, `password_hash`, `role`, `is_active`).
> - **`Patient`:** Stores demographic identifiers (`id`, `patient_id`, `age`, `gender`, `created_at`).
> - **`Scan`:** Foreign keys to `User` (technician) and `Patient`. Stores encrypted file path, organ type, quality status.
> - **`InferenceResult`:** One-to-one with `Scan`. Stores predicted class, confidence %, risk tier, and model version.
> - **`AuditLog`:** Standalone ledger recording `timestamp`, `event_type`, `user_id`, `scan_id`, and `ip_address`."

---

## 6. Role-Based Access Control & Clinical Workflow

### Q6.1: What is the separation of roles between Lab Technician and Doctor?
**Answer:**
> - **Lab Technician:**
>   - *Can:* Upload MRI scans, enter patient identifiers, view upload validation status, re-upload rejected scans.
>   - *Cannot:* View AI tumor predictions, risk scores, or diagnostic interpretations (prevents unqualified pre-diagnosis).
> - **Doctor / Oncologist:**
>   - *Can:* View assigned patient scan history, inspect AI predictions with confidence metrics, review decrypted MRI scans, and formulate medical reports.
>   - *Cannot:* Directly upload raw unverified scans bypassing the technician/quality pipeline."

### Q6.2: Why is the system explicitly labeled as a 'Decision Support System'?
**Answer:**
> "Under medical AI ethics and CDSS guidelines, AI models are assistive tools, not autonomous diagnostic authorities. The UI explicitly states: *'Decision Support Only: AI model prediction is not a confirmed medical diagnosis. Final interpretation belongs to a qualified medical professional.'* This prevents automation bias and adheres to healthcare liability standards."

---

## 7. Progress, Metrics & Tough Defense Questions

### Q7.1: The diary says your project is at 62% completion. Why is it 62% and not higher or lower?
**Answer:**
> "Our 62% is an honest, weighted engineering calculation across 7 core milestones:
> - **Web Architecture & RBAC:** 95% complete (Working Flask app, routes, auth, dashboards).
> - **Database & Models:** 95% complete (SQLite schemas, seed scripts, ORM).
> - **M1 AES-256 Encryption:** 85% complete (Cryptographic service built, verified; final in-transit handler integration remaining).
> - **M2 Quality Checker:** 80% complete (Laplacian blur & contrast algorithms implemented).
> - **M4 Audit Logging:** 70% complete (Audit database model and logging hooks active).
> - **M3 AI Model & Checkpoint:** 30% complete (Training pipeline notebook validated; final cloud GPU epoch training in progress).
> - **Automated Test Suite:** 10% complete (Unit tests scripted).
> 
> *Weighted Formula:* $\sum (\text{Component Weight} \times \text{Status}) = \mathbf{62\%}$."

### Q7.2: Why haven't you finished training the final AI model weights yet?
**Answer:**
> "We intentionally built the complete secure infrastructure, database models, encryption pipeline, and quality validation first to ensure the software foundation is robust. The data preprocessing pipeline and deep learning notebook are fully designed and validated. Training across 7,000+ images requires GPU compute epochs which we are executing now on Kaggle/Colab GPU to produce the final `.keras` production checkpoint before Review 2."

### Q7.3: What were the key recommendations from Zeroth Review, and how have you addressed them?
**Answer:**
> 1. **Focus on single-organ first:** We scoped Phase 1 strictly to Brain Tumor MRI before expanding to other organs.
> 2. **Ensure real cryptographic security:** We implemented authenticated AES-256-GCM rather than cosmetic encoding.
> 3. **Input validation:** We introduced the M2 Quality Checker with Laplacian blur filtering to reject invalid or corrupted scans before inference."

---
*Created for Team 15 Review 1 Defense — Muthoot Institute of Technology and Science*

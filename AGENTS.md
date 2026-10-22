# AGENTS.md --- SecureNeuroGrade

## 1. Purpose of This File

This file is the authoritative instruction set for AI coding agents
working on the **SecureNeuroGrade** project in VS Code, Antigravity, or
other AI-assisted development environments.

AI agents MUST read and follow this file before making any code,
configuration, documentation, database, model, security, or
infrastructure change.

If a repository-level instruction conflicts with a higher-priority
instruction from the human developer, the human developer's explicit
instruction takes precedence.

------------------------------------------------------------------------

# 2. Project Identity

**Project:** SecureNeuroGrade\
**Team:** Team 15 --- S7 Cyber Security\
**Institution:** Muthoot Institute of Technology and Science, Kochi
(Autonomous)

SecureNeuroGrade is a secure, web-based medical imaging system intended
to assist with **brain tumor detection, tumor classification, and tumor
risk assessment from MRI scans**.

The system combines:

-   Medical image processing
-   Deep-learning-based inference
-   Secure/encrypted image transmission
-   Scan-quality validation
-   Result classification
-   Risk-level assessment
-   Doctor authentication and role-based access
-   Patient/scan history
-   Audit and inference logging
-   A web-based workflow for laboratory technicians and doctors

The current project focus is **brain tumor detection**.

The architecture should be designed so that **multi-organ tumor
detection can be added in future phases**, but agents MUST NOT claim
that multi-organ detection is already implemented unless it actually
exists in the codebase.

The project presentation explicitly describes multi-organ support as a
future extension rather than a current prototype capability.

------------------------------------------------------------------------

# 3. Core Product Workflow

The intended high-level pipeline is:

``` text
Lab Technician
      |
      | MRI scan upload
      v
Input
      |
      v
M1 — Encryption Module
      |
      | encrypted transmission
      v
M2 — Quality Checker
      |
      | valid scan
      v
Backend AI Model
      |
      | inference
      v
M3 — Result Classifier
      |
      | tumor type + risk/confidence
      v
Doctor Dashboard

                    +----------------------+
                    | M4 — Audit /         |
                    | Inference Logger     |
                    +----------------------+
                              ^
                              |
                         inference logs
```

The intended processing sequence is:

``` text
scan
  -> encrypt
  -> transmit
  -> decrypt at server
  -> validate
  -> infer
  -> classify
  -> assess risk
  -> log
  -> display to authorized doctor
```

If a scan fails quality validation:

``` text
Input
  -> Quality Checker
  -> reject
  -> re-upload
```

Agents should preserve this conceptual workflow unless the human
developer explicitly changes the architecture.

------------------------------------------------------------------------

# 4. Functional Scope

## 4.1 Current / Primary Scope

The implementation should support, as applicable to the current
development phase:

1.  MRI scan upload by an authorized lab technician.
2.  Secure transmission of medical images.
3.  Server-side decryption only where required for inference.
4.  MRI image quality validation.
5.  Brain tumor detection.
6.  Tumor-type classification.
7.  Tumor risk/severity estimation.
8.  Confidence-score reporting.
9.  Authenticated doctor access.
10. Role-based/privilege-restricted access.
11. Patient and scan history.
12. Audit/inference logging.
13. A centralized web interface.

## 4.2 Future Scope

The architecture should make it possible to add:

-   Lung tumor detection
-   Liver tumor detection
-   Kidney tumor detection
-   Other organ-specific models
-   Additional datasets
-   Additional tumor classes
-   Additional risk/grading schemes

Future capabilities MUST be implemented as extensions rather than by
unnecessarily rewriting the existing system.

------------------------------------------------------------------------

# 5. Important Medical-AI Boundary

SecureNeuroGrade is a **research/academic decision-support prototype**,
not an autonomous medical diagnosis system.

Agents MUST:

-   Clearly distinguish model predictions from confirmed medical
    diagnoses.
-   Avoid UI wording that implies the AI is infallible.
-   Avoid claiming clinical validation unless documented by the project
    team.
-   Avoid inventing accuracy, sensitivity, specificity, F1-score, AUC,
    Dice scores, or other metrics.
-   Preserve confidence values produced by the actual model.
-   Display appropriate disclaimers where appropriate.
-   Avoid fabricating patient information or medical results.

Do not present an AI prediction as:

> "The patient definitely has cancer."

Prefer language such as:

> "Model prediction: \[class\], confidence: \[value\]."

The final medical interpretation belongs to a qualified medical
professional.

------------------------------------------------------------------------

# 6. Technology Direction

The project presentation specifies the following technology environment:

### Operating Systems

-   Windows 10/11
-   Ubuntu 22.04

### Programming / AI

-   Python 3.10+
-   TensorFlow / Keras
-   PyTorch
-   OpenCV
-   NumPy
-   Pandas
-   Scikit-learn

### Backend

-   Flask

### Frontend

-   HTML
-   CSS
-   JavaScript

### Database

-   SQLite for lightweight/local development
-   MySQL where a larger/deployed database is required

### Security

-   AES encryption for medical-image protection
-   HTTPS/TLS for network communication
-   Authentication
-   Role-based access control

### Development

-   Visual Studio Code
-   Git
-   GitHub

### Compute

Training may use an NVIDIA RTX-class GPU.

Cloud GPU infrastructure may be used where required.

------------------------------------------------------------------------

# 7. Recommended Repository Structure

Unless the existing repository already has an established structure that
should be preserved, use a structure similar to:

``` text
SecureNeuroGrade/
│
├── AGENTS.md
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── requirements.txt
│
├── app/
│   ├── __init__.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── technician.py
│   │   ├── doctor.py
│   │   └── scans.py
│   │
│   ├── services/
│   │   ├── encryption_service.py
│   │   ├── image_service.py
│   │   ├── quality_service.py
│   │   ├── inference_service.py
│   │   ├── classification_service.py
│   │   └── audit_service.py
│   │
│   ├── models/
│   │   ├── database_models.py
│   │   └── ml_models.py
│   │
│   ├── security/
│   │   ├── authentication.py
│   │   ├── authorization.py
│   │   └── encryption.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── technician/
│   │   └── doctor/
│   │
│   └── static/
│       ├── css/
│       ├── js/
│       └── images/
│
├── ml/
│   ├── datasets/
│   ├── preprocessing/
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   ├── checkpoints/
│   └── configs/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── ml/
│
├── scripts/
│   ├── setup.py
│   ├── train.py
│   ├── evaluate.py
│   └── migrate.py
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── security/
│   ├── model/
│   └── decisions/
│
└── release-notes/
    └── CHANGELOG.md
```

### Structure Rules

Do not create unnecessary files or directories.

Do not reorganize the repository merely for aesthetic reasons.

If the repository already contains a working structure, understand it
first and modify it incrementally.

Before introducing a new module, check whether an equivalent module
already exists.

------------------------------------------------------------------------

# 8. Separation of Responsibilities

Agents MUST maintain clear separation between:

### Frontend

Responsible for:

-   UI
-   Forms
-   Upload controls
-   Dashboard presentation
-   Client-side validation
-   User interaction

The frontend MUST NOT contain encryption keys, database credentials,
model secrets, or privileged server logic.

### Backend

Responsible for:

-   Authentication
-   Authorization
-   Request validation
-   File handling
-   Encryption/decryption orchestration
-   Quality-check orchestration
-   Model invocation
-   Result processing
-   Database access
-   Audit logging

### ML Layer

Responsible for:

-   Dataset preprocessing
-   Training
-   Model loading
-   Inference
-   Evaluation
-   Metrics
-   Model versioning

### Security Layer

Responsible for:

-   Authentication
-   Password handling
-   Authorization
-   Encryption
-   Secure file handling
-   Session security
-   Audit events

------------------------------------------------------------------------

# 9. Security Rules

Security is a first-class requirement of SecureNeuroGrade.

## 9.1 Never Commit Secrets

NEVER commit:

-   Passwords
-   API keys
-   Encryption keys
-   JWT secrets
-   Database passwords
-   Cloud credentials
-   Certificates/private keys
-   `.env` files containing secrets
-   Patient-identifiable information

Use:

``` text
.env
```

locally and provide:

``` text
.env.example
```

with placeholder values.

Example:

``` env
SECRET_KEY=change-me
DATABASE_URL=...
ENCRYPTION_KEY=...
```

Never put real values in `.env.example`.

------------------------------------------------------------------------

## 9.2 Medical Images

Medical images must be treated as sensitive data.

Agents MUST:

-   Avoid committing real patient MRI scans.
-   Avoid committing identifiable patient metadata.
-   Use synthetic, anonymized, or approved sample data for development.
-   Validate uploaded file types.
-   Restrict upload size.
-   Avoid path traversal vulnerabilities.
-   Store uploads outside public/static directories where possible.
-   Generate safe server-side filenames.
-   Delete temporary files when no longer needed.
-   Avoid exposing raw storage paths to clients.

------------------------------------------------------------------------

## 9.3 Encryption

The intended architecture includes AES encryption for medical-image
protection.

Agents MUST NOT:

-   Hardcode encryption keys.
-   Store encryption keys in frontend JavaScript.
-   expose keys through API responses.
-   invent custom cryptographic algorithms.
-   use encryption merely as cosmetic encoding.

Use established cryptographic libraries and authenticated encryption
where practical.

If an existing cryptographic design is changed, document the reason.

------------------------------------------------------------------------

## 9.4 HTTPS

Production communication should use HTTPS/TLS.

Never assume HTTP is secure simply because authentication is enabled.

Do not disable certificate verification merely to make development work
unless explicitly required for a controlled local environment, and
document any such exception.

------------------------------------------------------------------------

# 10. Authentication and Authorization

The system has at least two important user roles:

``` text
LAB_TECHNICIAN
DOCTOR
```

Additional roles may be introduced only when necessary.

### Lab Technician

Can:

-   Log in
-   Upload MRI scans
-   View upload/processing status
-   Correct rejected uploads

Must NOT:

-   Access privileged doctor-only results unless explicitly authorized
-   Access administrative secrets
-   Modify model configuration

### Doctor

Can:

-   Log in
-   Access authorized patient records
-   View scans and AI results
-   View tumor classification
-   View risk assessment
-   View confidence information
-   Review scan history

Access MUST be enforced on the server.

Do not rely solely on hiding frontend buttons.

------------------------------------------------------------------------

# 11. Database Rules

Use the database for structured application data, not as a dumping
ground for arbitrary objects.

Potential entities include:

``` text
User
Patient
Scan
InferenceResult
AuditLog
ModelVersion
```

Suggested relationships:

``` text
User
  |
  +---- uploads ----> Scan
                         |
                         +---- belongs to ----> Patient
                         |
                         +---- produces ----> InferenceResult
                                                 |
                                                 +---- ModelVersion

User / System
  |
  +---- creates ----> AuditLog
```

Never store plaintext passwords.

Use a modern password-hashing mechanism such as Argon2 or bcrypt.

------------------------------------------------------------------------

# 12. ML Development Rules

## 12.1 Dataset Integrity

Never silently alter a dataset.

Any preprocessing must be:

-   Reproducible
-   Documented
-   Versioned where practical
-   Applied consistently between training and inference

Avoid data leakage.

Patient-level separation must be maintained where appropriate so that
scans from the same patient do not improperly appear across training and
test sets.

------------------------------------------------------------------------

## 12.2 Training

Training code must be separate from production inference code.

Do not train a model during every web request.

Production application code should load a trained model/checkpoint.

Bad:

``` python
@app.route("/predict")
def predict():
    model.fit(...)
```

Good:

``` text
training -> model artifact
                  |
                  v
             inference
```

------------------------------------------------------------------------

## 12.3 Model Versioning

Every production model should have an identifiable version.

Example:

``` text
brain-tumor-cnn-v1
brain-tumor-cnn-v2
```

Where possible, record:

-   Model name
-   Version
-   Training date
-   Dataset version
-   Relevant metrics
-   Configuration
-   Checkpoint location

Inference logs should identify which model version generated the result.

------------------------------------------------------------------------

# 13. Model Evaluation

Never claim that a model is "accurate" without evidence.

Where applicable, evaluate using appropriate metrics such as:

-   Accuracy
-   Precision
-   Recall
-   F1-score
-   Confusion matrix
-   ROC-AUC
-   Sensitivity
-   Specificity

For segmentation tasks, use suitable metrics such as Dice coefficient.

Metrics must be calculated from actual experiments.

Do not fabricate benchmark results.

If a paper or existing system reports a metric, label it as a
reported/reference result rather than claiming it is SecureNeuroGrade's
result.

------------------------------------------------------------------------

# 14. Image Processing Rules

MRI processing should be implemented as a clear pipeline.

A typical structure is:

``` text
Upload
  |
Validation
  |
Decode
  |
Preprocessing
  |
Normalization / resizing as required by model
  |
Model inference
  |
Post-processing
  |
Classification / risk assessment
```

Do not silently change preprocessing parameters because they "look
better."

Any change that can affect model output should be documented and tested.

------------------------------------------------------------------------

# 15. API Rules

If REST endpoints are used:

-   Use clear endpoint names.
-   Validate all request data.
-   Validate file uploads.
-   Return appropriate HTTP status codes.
-   Never expose stack traces to production users.
-   Do not expose internal filesystem paths.
-   Do not expose database credentials.
-   Do not return sensitive data unnecessarily.
-   Enforce authorization server-side.
-   Log security-relevant events without logging secrets.

Example conceptual endpoints:

``` text
POST /auth/login
POST /scans/upload
GET  /scans/<id>
GET  /patients/<id>/scans
GET  /results/<id>
GET  /doctor/dashboard
```

These are examples, not requirements to create all endpoints
immediately.

------------------------------------------------------------------------

# 16. Error Handling

Errors must be:

-   Predictable
-   Logged appropriately
-   Safe for users
-   Useful to developers

Do not expose:

``` text
Traceback...
/home/user/project/database/password...
SECRET_KEY=...
```

to users.

Instead:

``` text
The scan could not be processed. Please try again.
```

Detailed technical information should go into controlled logs.

------------------------------------------------------------------------

# 17. Logging and Audit

The project includes an **Audit / Inference Logger (M4)**.

Audit logs should capture security- and workflow-relevant events such
as:

``` text
LOGIN_SUCCESS
LOGIN_FAILURE
SCAN_UPLOADED
SCAN_REJECTED
SCAN_ACCEPTED
INFERENCE_STARTED
INFERENCE_COMPLETED
INFERENCE_FAILED
RESULT_VIEWED
ACCESS_DENIED
```

Logs should include useful metadata such as:

-   Timestamp
-   Event type
-   User/system actor
-   Scan identifier
-   Model version where applicable
-   Success/failure state

Never log:

-   Passwords
-   Encryption keys
-   Session secrets
-   Full sensitive medical images
-   Unnecessary patient-identifying information

------------------------------------------------------------------------

# 18. Testing Requirements

Every meaningful change should be tested.

At minimum, consider:

### Unit Tests

Test individual functions and services.

### Integration Tests

Test:

``` text
upload -> validation -> processing -> inference -> result
```

### Security Tests

Test:

-   Unauthorized access
-   Wrong role access
-   Invalid file uploads
-   Oversized uploads
-   Path traversal attempts
-   Invalid authentication
-   Session handling
-   Missing/invalid tokens where applicable

### ML Tests

Test:

-   Model loading
-   Input shape
-   Preprocessing
-   Inference output format
-   Class mapping
-   Confidence-score generation

A code change is not considered complete merely because the application
starts.

------------------------------------------------------------------------

# 19. Git and Branching Policy --- STRICT

This section is mandatory.

## 19.1 NEVER Commit to `main`

AI agents MUST NEVER:

-   Commit directly to `main`
-   Push directly to `main`
-   Merge directly into `main`
-   Force-push `main`
-   Rewrite `main` history

The `main` branch is controlled by the human/user.

Only the human/user may make the final commit or merge into `main`.

If the current branch is `main`, stop before making a commit.

------------------------------------------------------------------------

# 20. One Change = One Branch

Every change must have its own branch.

Examples:

``` text
feature/mri-upload
feature/doctor-dashboard
feature/model-inference
feature/aes-encryption
fix/login-validation
fix/upload-security
refactor/inference-service
docs/api-documentation
test/authentication
```

Before starting work:

``` bash
git status
git branch
git switch main
git pull
git switch -c feature/<short-description>
```

Do not reuse an old completed branch for unrelated work.

------------------------------------------------------------------------

# 21. Branch Lifecycle

The expected lifecycle is:

``` text
main
  |
  +---- create branch
          |
          v
       develop
          |
          v
       test
          |
          v
      review
          |
          v
      human merges
          |
          v
         main
          |
          v
   branch is closed/deleted
```

After the work is completed and merged by the human:

``` bash
git branch -d <branch-name>
git push origin --delete <branch-name>
```

The AI agent MUST NOT delete the branch unless the human explicitly asks
it to.

"Branch is closed" means the completed feature branch should not
continue to be used for unrelated work.

------------------------------------------------------------------------

# 22. AI Agent Commit Policy

By default, AI agents should **not create commits**.

The preferred workflow is:

``` text
AI:
    create branch
    modify files
    run tests
    inspect diff
    prepare release notes
    report changes
    STOP

Human:
    review diff
    review release notes
    commit
    push
    merge to main
    close/delete branch
```

If repository tooling requires an AI-generated commit, the human must
explicitly authorize the commit first.

Even with permission:

-   Never commit to `main`.
-   Never push to `main`.
-   Never merge into `main`.

------------------------------------------------------------------------

# 23. Commit Message Convention

Every commit must describe one logical change.

Recommended format:

``` text
<type>(<scope>): <description>
```

Examples:

``` text
feat(upload): add MRI scan upload validation
feat(auth): implement doctor role authorization
feat(ml): add brain tumor inference service
fix(security): prevent unsafe upload paths
fix(api): handle invalid scan requests
test(auth): add role authorization tests
docs(api): document scan endpoints
refactor(ml): separate inference from training
```

Do not use meaningless messages such as:

``` text
update
changes
final
fixed stuff
latest
test
done
```

------------------------------------------------------------------------

# 24. Release Notes --- REQUIRED FOR EVERY COMMIT

**Every commit MUST have corresponding release notes.**

No commit should be considered complete without documenting what
changed.

Release notes should be stored in:

``` text
release-notes/CHANGELOG.md
```

or, if the project later adopts per-release files:

``` text
release-notes/
    v0.x.x.md
```

The release note should explain:

``` text
## [Unreleased]

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Security
- ...

### Testing
- ...
```

Only include sections that are relevant.

For every commit, the release note should make clear:

1.  What changed
2.  Why it changed
3.  Any important implementation details
4.  Any security implications
5.  Tests performed
6.  Any known limitations

Do not write vague release notes.

Bad:

``` text
- Fixed backend.
```

Good:

``` text
- Added server-side validation for MRI upload type and size.
- Rejected unsupported files before they reach the inference pipeline.
- Added tests for invalid extensions and oversized uploads.
```

------------------------------------------------------------------------

# 25. Do Not Mix Unrelated Changes

One branch and commit should have one logical purpose.

Do not combine:

``` text
MRI upload feature
+
login redesign
+
database migration
+
unrelated CSS cleanup
```

into one change.

If unrelated work is discovered, create a separate branch.

------------------------------------------------------------------------

# 26. Before Editing Code

AI agents MUST first inspect:

``` bash
git status
git branch --show-current
```

Then inspect relevant files.

Before modifying an existing implementation:

1.  Read the relevant file.
2.  Understand its callers.
3.  Understand its dependencies.
4.  Search for related functionality.
5.  Check existing tests.
6.  Check project documentation.
7.  Check whether another branch/change already addresses the issue.

Do not blindly rewrite files.

------------------------------------------------------------------------

# 27. Minimal-Change Principle

Prefer the smallest change that correctly solves the problem.

Do not:

-   Rewrite working modules unnecessarily.
-   Rename unrelated files.
-   Reformat the entire repository.
-   Upgrade dependencies without a reason.
-   Change architecture merely because another architecture is
    preferred.
-   Delete code that may be used elsewhere without checking references.

Avoid "drive-by refactoring."

------------------------------------------------------------------------

# 28. Dependency Management

Before adding a dependency:

1.  Check whether the functionality already exists.
2.  Check whether an existing dependency can provide it.
3.  Consider security and maintenance.
4.  Add the dependency to the appropriate dependency file.
5.  Document why it is needed.

Do not install random packages during development without documenting
them.

Avoid unnecessary dependency upgrades.

For security-sensitive dependencies, prefer maintained and
well-established libraries.

------------------------------------------------------------------------

# 29. Configuration

Configuration should be environment-driven.

Prefer:

``` text
environment variables
configuration files
```

over hardcoded values.

Do not hardcode:

-   Database credentials
-   Secret keys
-   Encryption keys
-   Production URLs
-   Cloud credentials
-   Deployment-specific paths

Use:

``` text
.env
.env.example
```

appropriately.

------------------------------------------------------------------------

# 30. Frontend Rules

Keep frontend code:

-   Simple
-   Accessible
-   Responsive
-   Consistent
-   Security-conscious

Never trust client-side validation as the only validation.

For example:

``` javascript
if (file.size > MAX_SIZE) {
    // helpful UI message
}
```

is useful, but the backend MUST independently enforce the same
restriction.

Do not expose:

-   Secrets
-   Internal API keys
-   Encryption keys
-   Database credentials
-   Administrative functionality

through frontend source code.

------------------------------------------------------------------------

# 31. Doctor Dashboard

The doctor dashboard should prioritize clinical readability.

Potential information:

``` text
Patient
Scan date
Scan status
Tumor detected
Tumor classification
Risk level
Confidence score
Model version
Relevant scan/result
```

Do not clutter the interface with unnecessary technical information.

The dashboard should make clear that AI output is decision support.

------------------------------------------------------------------------

# 32. Lab Technician Workflow

The technician interface should make the workflow obvious:

``` text
Login
  |
Upload MRI
  |
Upload validation
  |
Encryption
  |
Quality check
  |
Accepted / Rejected
  |
Processing status
```

If a scan is rejected, provide a useful reason where safe.

Example:

``` text
Scan rejected: unsupported image format.
Please upload an approved MRI image.
```

Do not reveal internal exception details.

------------------------------------------------------------------------

# 33. Scan Quality Checker

M2 exists to validate scan quality before inference.

Quality validation may include checks such as:

-   Supported format
-   File integrity
-   Image readability
-   Expected dimensions
-   Expected channel/volume structure
-   Basic preprocessing compatibility

The exact criteria should be based on the actual model and dataset.

Do not invent medical quality thresholds without documentation or
evidence.

------------------------------------------------------------------------

# 34. Result Classification

M3 is responsible for converting model output into a usable result.

Keep the following concepts separate:

``` text
raw model output
        |
        v
classification
        |
        v
confidence
        |
        v
risk assessment
        |
        v
doctor-facing result
```

Do not confuse confidence with probability of clinical truth.

If the model's output semantics are not established, document the
uncertainty rather than inventing an interpretation.

------------------------------------------------------------------------

# 35. Multi-Organ Extensibility

The architecture should avoid hardcoding everything around one organ.

Prefer a model registry/configuration approach where practical:

``` text
organ
  |
  +-- brain
  |     +-- model
  |     +-- classes
  |     +-- preprocessing
  |
  +-- lung
  |     +-- future model
  |
  +-- liver
        +-- future model
```

However, do not over-engineer future functionality before the current
brain-tumor prototype works.

The rule is:

> Design for extension, implement only what the current scope requires.

------------------------------------------------------------------------

# 36. Documentation Rules

Significant architectural decisions should be documented.

Useful documentation includes:

``` text
docs/architecture/
docs/security/
docs/model/
docs/api/
docs/decisions/
```

If an architectural decision changes security, model behavior, database
design, or API contracts, update the appropriate documentation.

------------------------------------------------------------------------

# 37. README Requirements

The root `README.md` should eventually explain:

-   Project purpose
-   Architecture
-   Features
-   Technology stack
-   Setup
-   Environment configuration
-   Running the backend
-   Running the frontend
-   Running tests
-   Training the model
-   Running inference
-   Database setup
-   Security considerations
-   Git workflow
-   Team contribution workflow

Do not document functionality that does not exist.

------------------------------------------------------------------------

# 38. Testing Before Hand-Off

Before telling the human that a change is complete, run the appropriate
checks.

At minimum:

``` bash
git status
git diff
```

and relevant test commands.

Depending on the project state, examples may include:

``` bash
python -m pytest
```

or:

``` bash
python -m unittest
```

Also verify that:

-   The application starts.
-   Imports work.
-   No obvious secrets were added.
-   No real patient data was added.
-   Changed endpoints work.
-   Changed UI flows work.
-   Relevant tests pass.

If a test cannot be run, explicitly tell the human why.

Never claim a test passed if it was not actually run.

------------------------------------------------------------------------

# 39. Final AI Handoff Format

When a task is complete, the AI agent should report:

``` text
Branch:
    feature/<name>

Implemented:
    - ...
    - ...

Files changed:
    - ...
    - ...

Tests:
    - ...
    - ...

Release notes:
    - Updated release-notes/CHANGELOG.md

Security considerations:
    - ...

Known limitations:
    - ...

Human action required:
    - Review diff
    - Commit
    - Push branch
    - Merge into main
    - Close/delete branch
```

The AI MUST NOT state that the work is "merged" unless the human
actually merged it.

------------------------------------------------------------------------

# 40. Stop Conditions

The AI agent should stop and ask the human instead of guessing when:

-   Requirements conflict.
-   A destructive database migration is required.
-   Production infrastructure must be changed.
-   Real patient data is involved.
-   Encryption architecture must be changed substantially.
-   A model's medical interpretation is unclear.
-   A dependency introduces significant security risk.
-   The task requires credentials.
-   A change would require committing to `main`.
-   The requested behavior conflicts with documented project scope.
-   The repository's existing architecture contradicts the assumed
    architecture.
-   A significant architectural decision is required.

Do not make high-impact decisions silently.

------------------------------------------------------------------------

# 41. Group Project Collaboration Rules

This is a team project. Code must remain understandable to other team
members.

## Rules

1.  Do not overwrite another person's work without checking it first.
2.  Pull/rebase from the latest shared development state before
    beginning substantial work when appropriate.
3.  Keep branches focused.
4.  Keep commits focused.
5.  Write meaningful commit messages.
6.  Add release notes for every commit.
7.  Test before handing work over.
8.  Do not commit generated junk.
9.  Do not commit secrets.
10. Do not commit real patient data.
11. Do not change APIs without considering existing callers.
12. Document breaking changes.
13. Do not silently remove features.
14. Communicate architectural changes.
15. Resolve merge conflicts carefully.
16. Do not force-push shared branches without explicit human approval.
17. Do not rewrite another developer's commits without permission.
18. Keep code formatting consistent with the existing project.
19. Prefer readable code over clever code.
20. Leave the repository in a clean, understandable state.

------------------------------------------------------------------------

# 42. What AI Agents Must Never Do

The following actions are prohibited unless explicitly authorized by the
human:

``` text
COMMIT DIRECTLY TO MAIN
PUSH DIRECTLY TO MAIN
MERGE INTO MAIN
FORCE-PUSH MAIN
DELETE MAIN
DELETE SOMEONE ELSE'S WORK
COMMIT SECRETS
COMMIT PATIENT DATA
FABRICATE MODEL RESULTS
FABRICATE TEST RESULTS
FABRICATE CLINICAL VALIDATION
DISABLE SECURITY TO "MAKE IT WORK"
HARDCODE CREDENTIALS
INVENT MEDICAL THRESHOLDS
SILENTLY CHANGE ARCHITECTURE
SILENTLY CHANGE PUBLIC API CONTRACTS
```

------------------------------------------------------------------------

# 43. Git Safety Checklist

Before any commit-related operation:

``` text
[ ] Am I on a feature/fix/docs/test branch?
[ ] Is the branch NOT main?
[ ] Is the working tree understood?
[ ] Is the change logically scoped?
[ ] Have relevant tests been run?
[ ] Did I inspect git diff?
[ ] Did I check for secrets?
[ ] Did I check for patient data?
[ ] Did I update release notes?
[ ] Has the human authorized the commit?
```

If any required answer is "No", do not commit.

------------------------------------------------------------------------

# 44. Definition of Done

A development task is considered complete only when:

``` text
[ ] Requirement implemented
[ ] Existing functionality preserved
[ ] Code is readable
[ ] Security implications considered
[ ] Relevant tests added/updated
[ ] Tests executed
[ ] Documentation updated where needed
[ ] Release notes updated
[ ] git diff reviewed
[ ] No secrets/patient data introduced
[ ] Work remains on its dedicated branch
[ ] Human is informed that review/commit/merge is required
```

------------------------------------------------------------------------

# 45. Source-of-Truth Rules

When making implementation decisions, use this priority:

``` text
1. Explicit human instruction
2. Existing working code and repository architecture
3. This AGENTS.md
4. Project documentation
5. Tests and established interfaces
6. Reasonable engineering judgment
```

Do not replace project-specific decisions with generic "best practices"
without checking the existing project first.

When uncertain, ask the human rather than silently inventing
requirements.

------------------------------------------------------------------------

# 46. Project Scope Reference

The project presentation describes SecureNeuroGrade as a secure
web-based system for automated brain tumor detection using deep
learning. The workflow includes MRI upload, encrypted transmission,
server-side decryption for inference, model-based
detection/classification/risk assessment, and authenticated doctor
review.

The presentation also identifies the following proposed advantages:

-   Multi-organ scalable architecture
-   Brain tumor detection and classification
-   Tumor risk assessment
-   Enhanced AI training
-   Encrypted MRI image transmission
-   Secure doctor authentication
-   AI-assisted diagnosis with confidence score
-   Centralized web platform
-   Patient scan-history management
-   Future support for additional tumor detection

The presentation explicitly notes that **multi-organ support and full
clinical deployment are future phases**, while the current focus is
brain tumor detection.

------------------------------------------------------------------------

# 47. Final Principle

The goal is not merely to make the code run.

The goal is to build a:

> **secure, maintainable, testable, collaborative, and academically
> defensible medical-AI prototype.**

AI agents should optimize for:

``` text
Correctness
+
Security
+
Maintainability
+
Reproducibility
+
Traceability
+
Team collaboration
```

Above all:

> **AI assists the team. The human controls the repository, commits,
> merges, releases, and final engineering decisions.**

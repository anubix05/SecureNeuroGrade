# Architecture Overview

## System Architecture

SecureNeuroGrade follows a layered architecture with clear separation of concerns.

```
┌─────────────────────────────────────────────────────┐
│                    Frontend Layer                     │
│          HTML Templates  |  CSS  |  JavaScript        │
│     (Login, Technician Dashboard, Doctor Dashboard)   │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP Requests
┌───────────────────────▼─────────────────────────────┐
│                    Flask Routes                       │
│         auth.py | technician.py | doctor.py | scans.py│
│              (Blueprints with RBAC)                   │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                   Services Layer                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ M1       │ │ M2       │ │ Inference│ │ M3      │ │
│  │ Encrypt  │ │ Quality  │ │ Service  │ │ Classify│ │
│  └──────────┘ └──────────┘ └──────────┘ └─────────┘ │
│  ┌──────────┐ ┌──────────┐                           │
│  │ M4 Audit │ │ Image    │                           │
│  │ Logger   │ │ Service  │                           │
│  └──────────┘ └──────────┘                           │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                  Security Layer                       │
│     Authentication | Authorization | Encryption       │
│         (bcrypt, RBAC, AES-256-GCM)                  │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                   Data Layer                          │
│         SQLAlchemy ORM | SQLite/MySQL                 │
│   User | Patient | Scan | InferenceResult |           │
│   AuditLog | ModelVersion                             │
└─────────────────────────────────────────────────────┘
```

## Data Flow

### Scan Upload Pipeline

```
Technician uploads MRI scan
    │
    ▼
Image Service: validate file type, size, generate safe filename
    │
    ▼
Save to disk (upload folder, outside public/static)
    │
    ▼
Create Scan record (status: UPLOADED)
    │
    ▼
M1 Encryption Service: AES-256-GCM encrypt for storage
    │
    ▼
M2 Quality Service: validate format, integrity, dimensions
    │
    ├── PASS → status: ACCEPTED
    │
    └── FAIL → status: REJECTED (with reason)
```

### Inference Pipeline (to be fully wired)

```
Accepted scan
    │
    ▼
M1 Encryption Service: decrypt for inference
    │
    ▼
Inference Service: load model, preprocess, predict
    │
    ▼
M3 Classification Service: classify, assess risk
    │
    ▼
Create InferenceResult record
    │
    ▼
M4 Audit Service: log inference event
    │
    ▼
Scan status → COMPLETED
    │
    ▼
Available on Doctor Dashboard
```

## Multi-Organ Extensibility

The architecture supports future organ types through:

- **ModelVersion.organ_type** — Database column identifying the organ
- **Scan.organ_type** — Tracks which organ a scan targets
- **ML Config files** — Per-organ configuration in `ml/configs/`
- **ModelRegistry** — Loads config by organ type dynamically

Adding a new organ requires:
1. A trained model checkpoint
2. A config file (e.g., `ml/configs/lung_tumor_config.json`)
3. A ModelVersion database record
4. No core code changes needed

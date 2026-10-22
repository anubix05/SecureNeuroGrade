# ADR-001: Initial Architecture Decisions

**Date:** 2026-09-07
**Status:** Accepted
**Authors:** Team 15

## Context

SecureNeuroGrade needs a foundation architecture for a secure, web-based brain tumor detection system. Key requirements include secure medical image handling, role-based access control, AI inference pipeline, and audit logging.

## Decisions

### 1. Flask as Backend Framework
- **Decision:** Use Flask (not Django or FastAPI)
- **Rationale:** Specified in AGENTS.md tech stack. Flask's lightweight nature suits the modular service architecture. Blueprints provide clean route separation.

### 2. SQLite for Development
- **Decision:** SQLite for local dev, MySQL for production
- **Rationale:** SQLite requires no external setup and is sufficient for development and testing. SQLAlchemy ORM provides database portability.

### 3. bcrypt for Password Hashing
- **Decision:** Use bcrypt via Flask-Bcrypt
- **Rationale:** AGENTS.md allows bcrypt or Argon2. bcrypt has better Flask ecosystem integration and is well-established.

### 4. AES-256-GCM for Image Encryption
- **Decision:** Use AES-256-GCM from pycryptodome
- **Rationale:** Provides authenticated encryption (confidentiality + integrity). AGENTS.md requires AES and prohibits custom crypto.

### 5. Flask-Login for Session Management
- **Decision:** Use session-based authentication (not JWT)
- **Rationale:** Simpler for a server-rendered web application. Appropriate for the current scope where the frontend and backend are on the same origin.

### 6. App Factory Pattern
- **Decision:** Use Flask app factory pattern with extensions
- **Rationale:** Supports testing with different configurations, avoids circular imports, and follows Flask best practices.

### 7. Service Layer Pattern
- **Decision:** Separate services from routes
- **Rationale:** Routes handle HTTP concerns; services contain business logic. Follows AGENTS.md separation of responsibilities (§8). Services map to the M1–M4 modules.

### 8. Multi-Organ Extensibility
- **Decision:** Use organ_type fields and config-driven model registry
- **Rationale:** AGENTS.md §35 requires extensibility for future organs without hardcoding around brain-only. The registry pattern allows new organ models to be added via config files and database records.

## Consequences

- The project starts with a working web application skeleton
- All core entities and relationships are modeled
- Security is built-in from the start (not bolted on later)
- The inference pipeline has a clear placeholder for the real ML model
- The architecture can grow without major rewrites

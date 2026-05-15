# LearnCRM Sync API

**RESTful API microservice for automated data synchronization between a corporate CRM system and an internal Academic Progress Tracking System.**

Built with Python, FastAPI, SQLAlchemy, and PostgreSQL.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [API Documentation](#api-documentation)
- [API Endpoints Reference](#api-endpoints-reference)
- [Example Requests](#example-requests)
- [Business Logic Flow](#business-logic-flow)
- [Security Best Practices](#security-best-practices)
- [Testing](#testing)
- [Deployment](#deployment)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Project Overview

An offline educational center operates two independent systems:

| System | Purpose |
|--------|---------|
| **CRM** | Sales, student contracts, payments |
| **Academic / LMS** | Attendance tracking, grades, academic progress |

Data between these systems was previously transferred manually or through file exports, causing delays, duplications, and errors.

**LearnCRM Sync API** is a middleware microservice that sits between the two systems, providing a standard REST interface for:

- Automatic **student onboarding** from CRM into the Academic system
- **Payment validation** — when a payment is marked *Paid* in CRM, academic modules are unlocked automatically
- **Academic progress reporting** — attendance and grades flow back from the Academic system into CRM
- **Centralized audit logging** of every synchronization event

---

## Features

- **JWT + API Key authentication** — dual-layer auth for service-to-service communication
- **Student synchronization** (CRM → Academic) — upsert student profiles
- **Payment synchronization** (CRM → Academic) — process payments and auto-unlock modules
- **Academic progress sync** (Academic → CRM) — push grades and attendance back
- **Strict data validation** — Pydantic v2 models with phone format, email, and range validation
- **Centralized sync logging** — every request is recorded with payload, status, and error details
- **Rate limiting** — per-endpoint configurable limits via SlowAPI
- **CORS support** — configurable allowed origins
- **Auto-generated Swagger UI** — interactive API documentation at `/docs`
- **ReDoc** — alternative documentation at `/redoc`
- **Docker-ready** — full `docker-compose.yml` with PostgreSQL
- **Alembic migrations** — version-controlled database schema
- **Comprehensive test suite** — pytest with in-memory SQLite

---

## System Architecture

```
┌──────────────┐         ┌─────────────────────────┐         ┌──────────────────┐
│              │         │                         │         │                  │
│  CRM System  │───────▶│   LearnCRM Sync API     │◀───────│  Academic / LMS  │
│              │  HTTP   │       (FastAPI)          │  HTTP   │     System       │
│  - Students  │         │                         │         │  - Attendance    │
│  - Payments  │         │  ┌───────────────────┐  │         │  - Grades        │
│  - Contracts │         │  │   PostgreSQL DB    │  │         │  - Progress      │
│              │         │  │  ┌─────────────┐  │  │         │                  │
└──────────────┘         │  │  │  students   │  │  │         └──────────────────┘
                         │  │  │  payments   │  │  │
                         │  │  │  academic_  │  │  │
                         │  │  │   records   │  │  │
                         │  │  │  sync_logs  │  │  │
                         │  │  │  api_users  │  │  │
                         │  │  └─────────────┘  │  │
                         │  └───────────────────┘  │
                         └─────────────────────────┘
```

### Data Flow

```
CRM → Academic (Outbound from CRM):
  1. CRM calls POST /api/v1/crm/students/sync       → Student created/updated
  2. CRM calls POST /api/v1/crm/payments/sync        → Payment processed, modules unlocked

Academic → CRM (Outbound from Academic):
  3. Academic calls POST /api/v1/academic/records     → Progress record created
  4. CRM calls GET /api/v1/academic/progress/{id}/crm-payload → Fetches formatted report
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Framework | FastAPI 0.115 |
| Validation | Pydantic v2 |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 16 (prod) / SQLite (dev) |
| Migrations | Alembic |
| Authentication | JWT (python-jose) + API Key |
| Rate Limiting | SlowAPI |
| Server | Uvicorn |
| Containerization | Docker & Docker Compose |
| Testing | pytest + httpx |

---

## Project Structure

```
FastAPI-LearnCRM-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Settings via pydantic-settings
│   ├── database.py              # SQLAlchemy engine, session, Base
│   ├── dependencies.py          # Auth dependencies (JWT, API Key)
│   ├── models/
│   │   ├── __init__.py          # Model re-exports
│   │   ├── student.py           # Student ORM model
│   │   ├── payment.py           # Payment ORM model
│   │   ├── academic.py          # AcademicRecord ORM model
│   │   ├── sync_log.py          # SyncLog ORM model (audit trail)
│   │   └── user.py              # APIUser ORM model (service accounts)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── student.py           # Student Pydantic schemas
│   │   ├── payment.py           # Payment Pydantic schemas
│   │   ├── academic.py          # Academic record schemas
│   │   ├── sync_log.py          # Sync log response schema
│   │   └── auth.py              # Token / register schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py            # Health check endpoints
│   │   ├── auth.py              # Register + login endpoints
│   │   ├── crm_sync.py          # CRM → Academic sync routes
│   │   └── academic_sync.py     # Academic → CRM sync routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── student_service.py   # Student business logic
│   │   ├── payment_service.py   # Payment business logic
│   │   ├── academic_service.py  # Academic record logic
│   │   └── sync_service.py      # Sync log queries
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── rate_limiter.py      # SlowAPI limiter instance
│   └── utils/
│       ├── __init__.py
│       ├── security.py          # Password hashing, JWT creation
│       └── logger.py            # Sync event logging utility
├── alembic/
│   ├── env.py                   # Alembic environment config
│   ├── script.py.mako           # Migration template
│   └── versions/                # Auto-generated migrations
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures (in-memory DB)
│   ├── test_crm_sync.py         # CRM sync endpoint tests
│   ├── test_academic_sync.py    # Academic sync endpoint tests
│   └── test_auth.py             # Auth endpoint tests
├── .env.example                 # Template for environment variables
├── .gitignore
├── alembic.ini                  # Alembic CLI config
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Container image definition
├── pyproject.toml               # Project metadata + tool config
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## Database Schema

### Entity Relationship

```
api_users
├── id (PK, UUID)
├── username (UNIQUE)
├── hashed_password
├── service_name
├── is_active
└── created_at

students
├── id (PK, UUID)
├── crm_student_id (UNIQUE, indexed)
├── first_name, last_name
├── email (UNIQUE)
├── phone, date_of_birth
├── enrollment_date, course_name
├── group_id, is_active, notes
├── created_at, updated_at
│
├──< payments (1:N)
│   ├── id (PK, UUID)
│   ├── crm_payment_id (UNIQUE)
│   ├── student_id (FK → students.id)
│   ├── amount, currency
│   ├── payment_status (Paid | Pending | Failed | Refunded)
│   ├── payment_date, invoice_number
│   ├── modules_unlocked (CSV)
│   ├── created_at, updated_at
│
└──< academic_records (1:N)
    ├── id (PK, UUID)
    ├── student_id (FK → students.id)
    ├── course_code, module_name
    ├── attendance_pct, grade, score
    ├── total_classes, attended_classes
    ├── status (in_progress | completed | failed | withdrawn)
    ├── instructor_notes
    ├── recorded_at, updated_at

sync_logs (audit trail)
├── id (PK, UUID)
├── direction (crm_to_academic | academic_to_crm)
├── entity_type (student | payment | academic_record)
├── entity_id
├── action (create | update | sync | error)
├── status (success | failure)
├── http_status_code
├── request_payload (JSON text)
├── response_payload (JSON text)
├── error_message
└── created_at
```

### Key Design Decisions

- **`crm_student_id`** is the natural key used to link a CRM record to the local student. All endpoints accept CRM IDs, not internal UUIDs.
- **`sync_logs`** captures every API call regardless of outcome, enabling full auditability.
- **`modules_unlocked`** is stored as a comma-separated string for simplicity; in a high-scale deployment this could be a join table.

---

## Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 14+ (or use SQLite for development)
- Git
- Docker & Docker Compose (optional, for containerized deployment)

### Clone the repository

```bash
git clone https://github.com/<your-username>/FastAPI-LearnCRM-backend.git
cd FastAPI-LearnCRM-backend
```

### Create a virtual environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Copy the example file and edit it:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Service display name | `LearnCRM Sync API` |
| `APP_VERSION` | Semantic version | `1.0.0` |
| `DEBUG` | Enable debug mode | `false` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./learncrm.db` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | *(must change)* |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL | `60` |
| `API_KEY` | Static API key for registration | *(must change)* |
| `RATE_LIMIT` | Default rate limit | `100/minute` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:3000,...` |
| `LOG_LEVEL` | Python log level | `INFO` |

> **Security note:** Always generate a strong random `SECRET_KEY` and `API_KEY` for production. Use `python -c "import secrets; print(secrets.token_urlsafe(48))"` to generate one.

---

## Running Locally

### Option A: SQLite (zero setup)

```bash
# The default DATABASE_URL uses SQLite — no database server needed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option B: PostgreSQL via Docker Compose

```bash
# Start PostgreSQL + the API
docker compose up --build
```

### Option C: PostgreSQL (manual)

```bash
# 1. Create the database
createdb learncrm_db

# 2. Set DATABASE_URL in .env
#    DATABASE_URL=postgresql://user:pass@localhost:5432/learncrm_db

# 3. Run migrations
alembic upgrade head

# 4. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running, open:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## API Documentation

FastAPI auto-generates interactive documentation from the code and Pydantic schemas.

### Authentication Flow

```
1. Admin registers a service account:
   POST /auth/register  (requires X-API-Key header)

2. The service obtains a JWT:
   POST /auth/token  →  { "access_token": "eyJ..." }

3. All subsequent requests include the JWT:
   Authorization: Bearer eyJ...
```

### Swagger UI Screenshot Reference

Open `/docs` in your browser after starting the server. You will see grouped endpoints:

- **Health** — `GET /`, `GET /health`
- **Authentication** — `POST /auth/register`, `POST /auth/token`
- **CRM Sync** — Student and payment sync, sync logs
- **Academic Sync** — Academic records and CRM payload generation

---

## API Endpoints Reference

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Root — service info |
| `GET` | `/health` | Health check |

### Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | API Key | Create a service account |
| `POST` | `/auth/token` | None | Get a JWT token |

### CRM → Academic Sync

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/crm/students/sync` | JWT | Upsert student |
| `PATCH` | `/api/v1/crm/students/{crm_student_id}` | JWT | Partial update |
| `GET` | `/api/v1/crm/students` | JWT | List students |
| `GET` | `/api/v1/crm/students/{crm_student_id}` | JWT | Get one student |
| `POST` | `/api/v1/crm/payments/sync` | JWT | Process payment |
| `GET` | `/api/v1/crm/payments` | JWT | List payments |
| `GET` | `/api/v1/crm/sync-logs` | JWT | Query sync logs |

### Academic → CRM Sync

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/academic/records` | JWT | Create academic record |
| `PATCH` | `/api/v1/academic/records/{record_id}` | JWT | Update record |
| `GET` | `/api/v1/academic/records/{crm_student_id}` | JWT | Get student records |
| `GET` | `/api/v1/academic/progress/{crm_student_id}/crm-payload` | JWT | CRM export payload |

---

## Example Requests

### 1. Register a service account

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "username": "crm_service",
    "password": "StrongP@ssw0rd!",
    "service_name": "CRM System"
  }'
```

**Response** `201 Created`:
```json
{
  "id": "a1b2c3d4-...",
  "username": "crm_service",
  "service_name": "CRM System",
  "message": "Service account created successfully"
}
```

### 2. Obtain a JWT token

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "crm_service",
    "password": "StrongP@ssw0rd!"
  }'
```

**Response** `200 OK`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in_minutes": 60
}
```

### 3. Sync a student from CRM

```bash
curl -X POST http://localhost:8000/api/v1/crm/students/sync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "crm_student_id": "CRM-STU-10045",
    "first_name": "Aisha",
    "last_name": "Karimova",
    "email": "aisha.karimova@example.com",
    "phone": "+998901234567",
    "date_of_birth": "2005-03-15",
    "enrollment_date": "2025-09-01",
    "course_name": "Python Backend Development",
    "group_id": "GRP-2025-PY-03"
  }'
```

**Response** `200 OK`:
```json
{
  "id": "b2c3d4e5-...",
  "crm_student_id": "CRM-STU-10045",
  "first_name": "Aisha",
  "last_name": "Karimova",
  "email": "aisha.karimova@example.com",
  "phone": "+998901234567",
  "date_of_birth": "2005-03-15",
  "enrollment_date": "2025-09-01",
  "course_name": "Python Backend Development",
  "group_id": "GRP-2025-PY-03",
  "is_active": true,
  "created_at": "2025-09-01T10:00:00Z",
  "updated_at": "2025-09-01T10:00:00Z"
}
```

### 4. Sync a payment (auto-unlock modules)

```bash
curl -X POST http://localhost:8000/api/v1/crm/payments/sync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "crm_payment_id": "PAY-20250901-001",
    "crm_student_id": "CRM-STU-10045",
    "amount": 350.00,
    "currency": "USD",
    "payment_status": "Paid",
    "payment_date": "2025-09-01",
    "invoice_number": "INV-10045",
    "modules_to_unlock": ["MOD-PY-101", "MOD-PY-102"]
  }'
```

**Response** `200 OK`:
```json
{
  "payment_id": "c3d4e5f6-...",
  "student_id": "b2c3d4e5-...",
  "status": "Paid",
  "modules_unlocked": ["MOD-PY-101", "MOD-PY-102"],
  "message": "Payment created. 2 module(s) unlocked."
}
```

### 5. Record academic progress

```bash
curl -X POST http://localhost:8000/api/v1/academic/records \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "crm_student_id": "CRM-STU-10045",
    "course_code": "PY-BACKEND-2025",
    "module_name": "Django REST Framework",
    "attendance_pct": 92.5,
    "grade": "A",
    "score": 95.0,
    "total_classes": 24,
    "attended_classes": 22,
    "status": "in_progress",
    "instructor_notes": "Excellent participation"
  }'
```

**Response** `201 Created`:
```json
{
  "id": "d4e5f6g7-...",
  "student_id": "b2c3d4e5-...",
  "course_code": "PY-BACKEND-2025",
  "module_name": "Django REST Framework",
  "attendance_pct": 92.5,
  "grade": "A",
  "score": 95.0,
  "total_classes": 24,
  "attended_classes": 22,
  "status": "in_progress",
  "instructor_notes": "Excellent participation",
  "recorded_at": "2025-09-15T14:30:00Z",
  "updated_at": "2025-09-15T14:30:00Z"
}
```

### 6. Get CRM payload for academic progress

```bash
curl http://localhost:8000/api/v1/academic/progress/CRM-STU-10045/crm-payload \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Response** `200 OK`:
```json
[
  {
    "crm_student_id": "CRM-STU-10045",
    "student_name": "Aisha Karimova",
    "course_code": "PY-BACKEND-2025",
    "module_name": "Django REST Framework",
    "attendance_pct": 92.5,
    "grade": "A",
    "score": 95.0,
    "status": "in_progress",
    "synced_at": "2025-09-15T14:35:00Z"
  }
]
```

### 7. Query sync logs

```bash
curl "http://localhost:8000/api/v1/crm/sync-logs?direction=crm_to_academic&status=failure" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## Business Logic Flow

### CRM → Academic System

```
┌─────────┐    POST /students/sync     ┌──────────────────┐
│   CRM   │ ─────────────────────────▶ │  Student Service  │
│  System │                            │                   │
│         │    POST /payments/sync     │  crm_student_id   │
│         │ ─────────────────────────▶ │  exists?          │
└─────────┘                            │   YES → UPDATE    │
                                       │   NO  → CREATE    │
                                       └────────┬─────────┘
                                                │
                                       ┌────────▼─────────┐
                                       │  Payment Service  │
                                       │                   │
                                       │  status == Paid?  │
                                       │   YES → unlock    │
                                       │         modules   │
                                       │   NO  → record    │
                                       │         only      │
                                       └────────┬─────────┘
                                                │
                                       ┌────────▼─────────┐
                                       │    Sync Logger    │
                                       │  (success/fail)   │
                                       └──────────────────┘
```

### Academic System → CRM

```
┌──────────┐   POST /academic/records   ┌──────────────────┐
│ Academic │ ──────────────────────────▶│ Academic Service  │
│  System  │                            │                   │
│          │   GET /progress/.../       │  Validate student │
│          │       crm-payload          │  Store record     │
│          │◀──────────────────────────│  Build CRM payload│
└──────────┘                            └────────┬─────────┘
                                                 │
                                        ┌────────▼─────────┐
                                        │    Sync Logger    │
                                        │  (audit entry)    │
                                        └──────────────────┘
```

### Payment Unlock Logic

1. CRM sends a payment event with `payment_status` and optional `modules_to_unlock`.
2. The API resolves the student by `crm_student_id` (returns 404 if not found).
3. Payment is upserted (created or updated based on `crm_payment_id`).
4. If `payment_status == "Paid"` **and** `modules_to_unlock` is non-empty:
   - The modules are recorded in the `modules_unlocked` field.
   - In a production integration, an outbound call to the Academic/LMS API would enable those modules.
5. A sync log entry is written regardless of outcome.

---

## Security Best Practices

| Practice | Implementation |
|----------|---------------|
| **JWT authentication** | All sync endpoints require a valid Bearer token. Tokens expire after a configurable TTL. |
| **API Key gating** | Service account registration requires a pre-shared API key (`X-API-Key` header). |
| **Password hashing** | Passwords are stored with bcrypt via `passlib`. |
| **Rate limiting** | Per-endpoint limits via SlowAPI to prevent abuse (default: 100 req/min). |
| **Input validation** | Pydantic v2 enforces types, ranges, email format, phone regex, date patterns. |
| **CORS** | Only explicitly listed origins are allowed. |
| **SQL injection prevention** | SQLAlchemy ORM parameterizes all queries. |
| **Secret management** | All secrets are loaded from environment variables, never hardcoded. |
| **Audit trail** | Every sync operation is logged to `sync_logs` with full request/response payloads. |
| **Dependency pinning** | `requirements.txt` pins exact versions to prevent supply-chain issues. |

### Production Hardening Checklist

- [ ] Generate a cryptographically strong `SECRET_KEY` and `API_KEY`
- [ ] Use HTTPS (terminate TLS at a reverse proxy like Nginx or Traefik)
- [ ] Set `DEBUG=false`
- [ ] Restrict `ALLOWED_ORIGINS` to actual frontend/system origins
- [ ] Enable PostgreSQL SSL connections
- [ ] Run the container as a non-root user
- [ ] Set up log rotation and monitoring (ELK, Grafana, Sentry)
- [ ] Enable database connection pooling (PgBouncer)

---

## Testing

Run the full test suite:

```bash
pytest -v
```

Run with coverage:

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

The test suite uses an **in-memory SQLite database** and overrides the authentication dependency so tests do not require a running PostgreSQL instance or valid tokens.

### Test Files

| File | Coverage |
|------|----------|
| `tests/test_crm_sync.py` | Student CRUD, payment sync, validation errors |
| `tests/test_academic_sync.py` | Academic records, CRM payload generation |
| `tests/test_auth.py` | Registration, login, health endpoints |

---

## Deployment

### Docker Compose (recommended)

```bash
# 1. Set secrets
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
export API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. Build and start
docker compose up --build -d

# 3. Verify
curl http://localhost:8000/health
```

### Manual Deployment

```bash
# 1. Provision a PostgreSQL database

# 2. Set environment variables (or use .env)
export DATABASE_URL=postgresql://user:pass@host:5432/learncrm_db
export SECRET_KEY=<strong-random-value>
export API_KEY=<strong-random-value>

# 3. Run migrations
alembic upgrade head

# 4. Start with production settings
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 443 ssl;
    server_name api.learncrm.example.com;

    ssl_certificate     /etc/ssl/certs/learncrm.pem;
    ssl_certificate_key /etc/ssl/private/learncrm.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Future Improvements

| Category | Improvement | Description |
|----------|-------------|-------------|
| **Message Queue** | RabbitMQ / Kafka | Decouple synchronization via async events. The API publishes events; workers consume them. |
| **Task Queue** | Celery + Redis | Offload long-running sync jobs (batch imports, retries) to background workers. |
| **Webhooks** | Outbound webhooks | Push real-time notifications to CRM/Academic systems instead of polling. |
| **Retry Logic** | Exponential backoff | Automatically retry failed sync operations with configurable retry policies. |
| **Batch Sync** | Bulk endpoints | Accept arrays of students/payments in a single request for initial data migration. |
| **Caching** | Redis cache | Cache frequently read student profiles to reduce database load. |
| **Monitoring** | Prometheus + Grafana | Export metrics (sync latency, failure rate, throughput) for operational dashboards. |
| **Tracing** | OpenTelemetry | Distributed tracing across CRM → API → Academic for debugging. |
| **API Versioning** | `/api/v2/` | Introduce versioned schemas for backward-compatible evolution. |
| **Multi-tenancy** | Org-scoped data | Support multiple educational centers with tenant isolation. |
| **CI/CD** | GitHub Actions | Automated testing, linting, building, and deployment on every push. |
| **Schema Registry** | JSON Schema / Avro | Formalize contract between CRM and Academic systems. |

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

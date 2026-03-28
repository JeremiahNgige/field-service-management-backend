# Field Service Management — Backend

A RESTful Django backend for a **Field Service Management (FSM)** application. It handles user authentication, job lifecycle management, file uploads via MinIO (S3-compatible storage), and push notifications through Firebase Cloud Messaging (FCM) — all orchestrated via Docker Compose.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Getting Started (Docker)](#getting-started-docker)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [Seeding Mock Data](#seeding-mock-data)
- [Known Limitations & Incomplete Features](#known-limitations--incomplete-features)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 + Django REST Framework |
| Database | PostgreSQL 15 |
| Auth | JWT via `djangorestframework-simplejwt` |
| Task Queue | Celery + Redis |
| Object Storage | MinIO (S3-compatible) |
| Push Notifications | Firebase Admin SDK (FCM) |
| Server | Gunicorn |
| Containerisation | Docker + Docker Compose |

---

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  Django/    │────▶│ PostgreSQL  │
│  (Flutter)  │     │  Gunicorn   │     │     DB      │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Celery  │ │  Redis   │ │  MinIO   │
        │  Worker  │ │ (Broker) │ │ (S3)     │
        └────┬─────┘ └──────────┘ └──────────┘
             │
             ▼
        ┌──────────┐
        │ Firebase │
        │   FCM    │
        └──────────┘
```

- **Django** serves the REST API on port `8000`.
- **Celery** processes background tasks (FCM notifications) using **Redis** as a broker.
- **MinIO** provides S3-compatible object storage for photos and signatures — presigned URLs are generated server-side for direct client uploads and downloads.
- A **signal** fires when a job transitions from `unassigned → assigned`, triggering a Celery task that sends an FCM push notification to the assigned technician.

---

## Prerequisites

You only need the following installed on a fresh machine:

- [Docker](https://docs.docker.com/get-docker/) (v24+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2+)

> No Python, PostgreSQL, or Redis installation is required on the host machine.

---

## Getting Started (Docker)

### 1. Clone the repository

```bash
git clone <repository-url>
cd "field service management backend"
```

### 2. Configure environment variables

Copy the example below into a `.env` file in the project root. Adjust values as needed:

```env
# Django
SECRET_KEY="django-insecure-change-me-in-production"
DEBUG=True
ALLOWED_HOSTS="*"

# PostgreSQL
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=db
DB_PORT=5432

# MinIO (S3-compatible storage)
USE_S3=True
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=fsm-bucket
AWS_S3_ENDPOINT_URL=http://minio:9000
AWS_S3_USE_SSL=False

# Celery / Redis
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Firebase (FCM)
GOOGLE_APPLICATION_CREDENTIALS=/app/firebase-credentials.json
```

> **Note:** `DB_HOST` must be `db` (the Docker service name) when running inside Docker.

### 3. Add Firebase credentials

Place your Firebase service account JSON file in the project root and name it exactly:

```
firebase-credentials.json
```

If you do not have Firebase credentials yet, the server will still start — FCM notifications will be gracefully skipped.

### 4. Create the MinIO bucket

The MinIO bucket must exist before uploads work. After services are running, create it via the MinIO web console:

1. Open [http://localhost:9001](http://localhost:9001) in your browser.
2. Log in with `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (default: `minioadmin` / `minioadmin`).
3. Create a bucket named `fsm-bucket` (or whatever you set in `AWS_STORAGE_BUCKET_NAME`).
4. Set the bucket's **Access Policy** to `public` (required for presigned URL generation).

### 5. Build and start all services

```bash
docker compose up --build
```

This single command will:

- Build the Django application image
- Start PostgreSQL, Redis, and MinIO
- Run all database migrations (`migrate.sh`)
- Seed **150 mock unassigned jobs** (`jobs_generator.py`)
- Start the Django/Gunicorn API server on port `8000`
- Start the Celery worker

### 6. Verify the services are running

| Service | URL | Purpose |
|---|---|---|
| Django API | http://localhost:8000 | Main REST API |
| MinIO Console | http://localhost:9001 | Object storage UI |
| MinIO API | http://localhost:9000 | S3-compatible endpoint |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Celery broker |

### Starting the services

If you have already built the images and just want to start the existing containers in the background (detached mode):

```bash
docker compose up -d
```

If you previously stopped the containers (without removing them) and just want to wake them up again:

```bash
docker compose start
```

### Stopping the services

```bash
docker compose stop
```

To entirely tear down the containers and network:

```bash
docker compose down
```

To also remove all persistent data volumes:

```bash
docker compose down -v
```

### Restarting specific services

If you make code changes or just need to bounce a specific container without bringing down the whole stack, you can restart individual services:

```bash
# Restart the Django API server
docker compose restart web

# Restart the Celery background worker
docker compose restart celery

# Restart PostgreSQL database
docker compose restart db

# Restart Redis broker
docker compose restart redis

# Restart MinIO object storage
docker compose restart minio
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Django secret key |
| `DEBUG` | ✅ | `False` | Enable debug mode |
| `ALLOWED_HOSTS` | ✅ | `*` | Comma-separated list of allowed hosts |
| `DB_NAME` | ✅ | `postgres` | PostgreSQL database name |
| `DB_USER` | ✅ | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | ✅ | — | PostgreSQL password |
| `DB_HOST` | ✅ | `127.0.0.1` | DB host (`db` inside Docker) |
| `DB_PORT` | ✅ | `5432` | PostgreSQL port |
| `USE_S3` | ✅ | `False` | Enable MinIO/S3 storage |
| `AWS_ACCESS_KEY_ID` | ✅ (if S3) | `minioadmin` | MinIO/S3 access key |
| `AWS_SECRET_ACCESS_KEY` | ✅ (if S3) | `minioadmin` | MinIO/S3 secret key |
| `AWS_STORAGE_BUCKET_NAME` | ✅ (if S3) | `fsm-bucket` | Bucket name |
| `AWS_S3_ENDPOINT_URL` | ✅ (if S3) | `http://localhost:9000` | MinIO endpoint |
| `AWS_S3_USE_SSL` | ❌ | `False` | Enable SSL for MinIO |
| `CELERY_BROKER_URL` | ✅ | `redis://localhost:6379/1` | Redis broker URL |
| `CELERY_RESULT_BACKEND` | ✅ | `redis://localhost:6379/1` | Redis result backend |
| `GOOGLE_APPLICATION_CREDENTIALS` | ❌ | — | Path to Firebase credentials JSON |

---

## API Reference

All endpoints are prefixed with their app path. Authentication uses **Bearer JWT tokens**.

> Obtain tokens via `POST /user/login/`. Pass the token as `Authorization: Bearer <access_token>`.

### Authentication & User Endpoints — `/user/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/user/register/` | ❌ Public | Register a new user |
| `POST` | `/user/login/` | ❌ Public | Login and receive JWT tokens |
| `PUT` | `/user/update/` | ✅ JWT | Update authenticated user's profile |
| `POST` | `/user/logout/` | ✅ JWT | Logout (invalidates refresh token) |
| `GET` | `/user/profile/` | ✅ JWT | Fetch authenticated user's profile |
| `GET` | `/user/fetch-assigned-jobs/` | ✅ JWT | List all jobs assigned to the authenticated user |
| `PUT` | `/user/update-fcm-token/` | ✅ JWT | Update the user's FCM push notification token |

### Job Endpoints — `/jobs/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/jobs/create/` | ✅ JWT | Create a new job |
| `GET` | `/jobs/list/` | ✅ JWT | List all jobs (admin) or assigned jobs (technician) |
| `PUT` | `/jobs/update/<uuid:job_id>/` | ✅ JWT | Update a job (status, assignment, fields) |
| `DELETE` | `/jobs/delete/<uuid:job_id>/` | ✅ JWT | Delete a job |
| `GET` | `/jobs/detail/<uuid:job_id>/` | ✅ JWT | Retrieve a single job's details |
| `POST` | `/jobs/upload-urls/` | ✅ JWT | Generate presigned S3 upload URLs for photos/signature |
| `POST` | `/jobs/download-urls/` | ✅ JWT | Generate presigned S3 download URLs for a job's media |

#### JWT Token Refresh

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/token/refresh/` | Refresh an expired access token |

### JWT Details

| Setting | Value |
|---|---|
| Access Token Lifetime | 15 minutes |
| Refresh Token Lifetime | 7 days |
| Token Algorithm | HS256 |
| Header | `Authorization: Bearer <token>` |

---

## Running Tests

Tests are written using Django's built-in `TestCase` and run against a temporary in-memory test database — **no running Docker services required**.

### Run all tests (inside Docker)

```bash
docker compose exec web python manage.py test
```

### Run all tests (locally, with a virtual environment)

```bash
# Activate your virtual environment first
source .venv/bin/activate

# Run all tests
python manage.py test
```

### Run tests for a specific app

```bash
# Jobs app only
python manage.py test jobs

# User app only
python manage.py test user
```

### Run a specific test class or method

```bash
python manage.py test jobs.tests.JobTests
python manage.py test jobs.tests.JobTests.test_job_creation
```
### Run API Integration Tests

```bash
# Run all integration tests across both apps
python manage.py test user.tests_integration jobs.tests_integration
```

### Test coverage summary

| App | Test Class | Cases Covered |
|---|---|---|
| `jobs` | `JobTests` | Creation, update, delete, detail, list, invalid data |
| `user` | `UserTests` | Creation, update, delete, detail, list, invalid data |
| `user` | `AuthProfileIntegrationTests` | End-to-end API testing of registration, JWT token generation, profile fetching, and profile updating |
| `jobs` | `JobLifecycleIntegrationTests` | End-to-end API testing of job creation, technician assignment, status progression, and signature uploads |
| `jobs` | `TechnicianWorkFlowIntegrationTests` | End-to-end API testing of fetching assigned jobs securely and syncing FCM tokens |

---

## Seeding Mock Data

The migration script (`migrate.sh`) automatically seeds **150 unassigned mock jobs** on startup via `jobs_generator.py`. All seeded jobs have:

- Status: `unassigned`
- Start/end times: between 1 and 30 days from the current date (never overdue)
- Realistic addresses with latitude/longitude coordinates
- Varied priorities (`low`, `medium`, `high`) and service types

To re-seed the database manually:

```bash
# Inside Docker
docker compose exec web python jobs_generator.py

# Locally
python jobs_generator.py
```

> ⚠️ The seed script **clears all existing jobs** before inserting new ones.

---

## Known Limitations & Incomplete Features

### 🔒 Authentication & Authorisation
- **Role-based access control (RBAC) is partially enforced.** The `user_type` field (`admin`, `technician`, `driver`, `inspectors`) is stored on the user model, but not all view-level permission checks strictly enforce role boundaries — some endpoints that should be admin-only may be accessible to any authenticated user.

### 📁 File Storage
- **The MinIO bucket must be created manually** before file upload/download endpoints will function. There is no automated bucket provisioning on startup.
- **Presigned URLs expire** after the default S3 timeout. Long-running clients may receive expired URLs and will need to request new ones.

### 🔔 Push Notifications
- **FCM notifications are best-effort.** If a user has no FCM token stored, or if Firebase initialisation fails (e.g., missing `firebase-credentials.json`), the notification is silently skipped — the job assignment still succeeds.
- **No notification retry mechanism.** If the Celery task fails after the job is assigned, the push notification is lost and not retried.

### 🧪 Tests
- **The `test_job_creation_with_invalid_data` test in `JobTests`** creates a duplicate job without a unique constraint, meaning it may not reliably raise a `ValidationError` in all database states.

### ⚙️ General
- **`DEBUG=True` is set by default.** This must be changed to `False` and `SECRET_KEY` must be rotated before any production deployment.
- **`ALLOWED_HOSTS="*"` is set by default**, which should be restricted to specific domains in production.
- **No API versioning.** All endpoints are unversioned (`/user/`, `/jobs/`), making future breaking changes harder to manage.
- **No rate limiting or throttling** is configured on any endpoint.
- **`migrate.sh` runs `makemigrations` on startup**, which is not suitable for production. Migration files should be committed to version control and only `migrate` should run in deployment pipelines.

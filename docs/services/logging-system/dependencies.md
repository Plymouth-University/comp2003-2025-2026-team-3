# Logging System Dependencies

## Purpose

This document lists the code, database, configuration, and runtime dependencies needed for the current logging system.

The durable logging system depends on a dedicated PostgreSQL database and async SQLAlchemy. Console and AI file logging still have their own smaller dependencies.

## Internal Code Dependencies

### Durable log models

File:

- `backend/app/models/logs.py`

Provides:

- SQLAlchemy models for all logging tables
- relationships from `request_trace` to each log family
- indexes for query-friendly fields such as request ID, tenant ID, profile ID, endpoint, action, severity, and occurred time

Depends on:

- `backend/app/log_database.py`
- SQLAlchemy
- PostgreSQL JSONB and UUID types

### Logging database connection

File:

- `backend/app/log_database.py`

Provides:

- `log_engine`
- `LogSessionLocal`
- `LogBase`
- `get_log_db()`
- `init_log_db()`
- `close_log_db()`

Depends on:

- `settings.LOG_DATABASE_URL`
- SQLAlchemy async engine
- `asyncpg`

Current runtime use:

- `LogWriter` uses `LogSessionLocal`
- app shutdown calls `close_log_db()`
- migrations are the preferred schema setup path

### Central writer service

File:

- `backend/app/services/log_writer.py`

Provides:

- `LogContext`
- `LogWriter`
- durable writes for application, performance, error, request trace, and UI interaction logs

Depends on:

- `LogSessionLocal`
- `ApplicationLog`
- `PerformanceLog`
- `ErrorLog`
- `RequestTrace`
- `UIClickAnalyticsLog`
- FastAPI `Request`
- `jsonable_encoder`
- PostgreSQL insert/upsert support

### Backend request middleware

File:

- `backend/app/main.py`

Depends on:

- `LogWriter`
- `LogContext`
- session cookie settings
- `decode_session_token`
- standard library timing and memory helpers

Used for:

- server-generated request IDs
- request start/completion logs
- request-level performance logs
- unhandled exception logs
- request payload and response payload size metadata
- process RSS memory measurement

### Durable UI log ingestion

Files:

- `backend/app/routers/logs.py`
- `backend/app/schemas/logs.py`
- `frontend/src/shared/api/uiLogs.ts`

Depends on:

- authenticated backend session cookie
- `POST /api/v1/logs/ui-clicks`
- frontend `fetch`
- `API_BASE_URL`

Used for:

- frontend view/edit/close/reassign/override interaction logs

### Business event call sites

Files:

- `backend/app/routers/auth.py`
- `backend/app/routers/ai_state.py`
- `backend/app/routers/profiles.py`

Depend on:

- `LogWriter`
- `LogContext`
- existing route session/context data

Used for:

- auth lifecycle logs
- AI ticket state logs
- profile/specialism management logs
- domain-level error logs

## Database Dependencies

### Local compose service

File:

- `backend/compose.yml`

Defines:

- service: `postgres_logs`
- container: `secops-postgres-logs`
- database: `logsdb`
- port: `5435`
- user: `postgres`
- password: `password`

### Configuration

File:

- `backend/app/config.py`

Relevant setting:

```text
LOG_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5435/logsdb
```

This URL is used by:

- `backend/app/log_database.py`
- `backend/alembic_logs/env.py`
- `backend/scripts/migrate_all_databases.py`

### Migrations

Files:

- `backend/alembic_logs.ini`
- `backend/alembic_logs/env.py`
- `backend/alembic_logs/versions/5bccb4e25b7a_create_logging_tables.py`

Preferred setup command from the backend directory:

```bash
python scripts/migrate_all_databases.py
```

This runs both the core database migrations and the logs database migrations.

## Python Package Dependencies

From `backend/requirements.txt`:

- `sqlalchemy[asyncio]>=2.0.0`
- `asyncpg>=0.29.0`
- `alembic>=1.13.0`
- `fastapi`
- `pydantic-settings`

Optional runtime behavior:

- `psutil` is used for process RSS memory measurement if installed.
- If `psutil` is not installed, the app falls back to standard-library/platform memory helpers.

Important note:

- missing `asyncpg` prevents the backend from importing because async database engines are created at import time.

## Frontend Dependencies

The frontend logging helper depends only on browser APIs already used by the app:

- `fetch`
- `JSON.stringify`
- `Date`
- `window.location.pathname`

The helper sends credentials with the request:

```ts
credentials: "include"
```

That means UI log ingestion requires the same backend session cookie as the rest of the authenticated app.

## Existing Supporting Logging Dependencies

### Python standard logging

Still used by:

- `backend/app/main.py`
- `backend/app/database.py`
- `backend/app/log_database.py`
- `backend/app/providers/fake_autotask.py`
- AI service modules

Purpose:

- local terminal feedback
- fallback logging if durable logging fails

### AI rotating file logging

File:

- `backend/app/services/ai/logging_config.py`

Depends on:

- `logging`
- `logging.handlers`
- filesystem write access to `backend/logs/ai_services/`

This remains separate from durable database logging.

## Operational Assumptions

The durable logging system assumes:

- `postgres_logs` or another configured logs database is reachable
- logs migrations have been applied
- `LOG_DATABASE_URL` points at the intended logs database
- route handlers do not rely on log writes succeeding
- logged JSON details do not include secrets
- frontend UI logging is best-effort and may silently fail from the user's point of view

## Current Dependency Gaps

Verified gaps:

- no log query UI
- no retention or archival job
- no OpenTelemetry dependency
- no SQLAlchemy timing collector for `db_latency_ms`
- no explicit external/provider timing collector for `external_api_latency_ms`
- no mandatory `psutil` dependency for memory measurement

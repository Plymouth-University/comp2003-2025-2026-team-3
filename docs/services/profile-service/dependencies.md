# Profile Service Dependencies

## Purpose

This document lists the dependencies the profile service relies on at runtime and explains how they are used.

Source of truth:

- `backend/app/services/profile_service.py`
- `backend/app/repositories/profile_repository.py`
- `backend/app/models/profile.py`
- `backend/app/database.py`
- `backend/app/config.py`
- `backend/requirements.txt`

## Internal Code Dependencies

### Database session management

Files:

- `backend/app/database.py`

Used for:

- providing `AsyncSession` instances through `get_db()`
- creating the SQLAlchemy async engine and session factory

Why it matters:

- every profile service route depends on a live database session
- transaction and commit behavior is split between repository methods and `get_db()`

### ORM models

Files:

- `backend/app/models/profile.py`

Used for:

- tenant, profile, display, identity, avatar, and specialism persistence

Why it matters:

- repository queries and updates are tightly coupled to these ORM models and their relationships

### Pydantic schemas

Files:

- `backend/app/schemas/profile.py`

Used for:

- validating request payloads
- shaping HTTP responses

Why it matters:

- schema constraints define accepted values such as profile status and avatar source

### Auth integration

Files:

- `backend/app/routers/auth.py`
- `backend/app/auth.py`

Used for:

- obtaining validated Entra identity claims
- triggering `resolve_entra_profile(...)`

Why it matters:

- the profile service is part of the login path, not just admin-style CRUD

### Application settings

Files:

- `backend/app/config.py`

Used for:

- `ENTRA_INTERNAL_TENANT_NAME`
- `ENTRA_IDP_NAME`

Why it matters:

- these settings control how Entra users are mapped into the local profile domain

### AI category dependency for authenticated specialism replacement

Files:

- `backend/app/services/profile_service.py`
- `backend/app/services/ai/__init__.py`

Used for:

- validating authenticated specialism keys against configured AI category keys
- creating tenant specialisms from AI category labels when missing

Why it matters:

- profile specialism replacement for authenticated users is now coupled to the currently configured AI category set

## Third-Party Dependencies

### FastAPI

Declared in:

- `backend/requirements.txt`

Used for:

- request routing
- dependency injection
- HTTP error handling
- validation integration with Pydantic

Profile-service touchpoints:

- `backend/app/routers/profiles.py`
- `backend/app/routers/auth.py`

### SQLAlchemy asyncio

Declared in:

- `backend/requirements.txt`

Used for:

- ORM model mapping
- async queries and updates
- relationship loading

Profile-service touchpoints:

- all repository classes
- `backend/app/database.py`

### asyncpg

Declared in:

- `backend/requirements.txt`

Used for:

- PostgreSQL driver for `postgresql+asyncpg://...`

Why it matters:

- the service will not run against PostgreSQL without a working asyncpg installation and matching `DATABASE_URL`

### PostgreSQL

Referenced by:

- `backend/app/config.py`
- `backend/compose.yml`

Used for:

- persistent storage of tenant/profile domain data

Why it matters:

- this is the profile service's primary state store

### Pydantic and pydantic-settings

Declared in:

- `backend/requirements.txt`

Used for:

- schema validation
- environment-driven settings

## Data Dependencies

### Required database state

The service can create some dependencies on demand:

- internal Entra tenant row can be auto-created
- identity provider row can be auto-created

But many flows still require pre-existing data:

- profile creation requires an existing tenant
- direct identity linking requires valid referenced IDs
- specialism assignment assumes valid profile and specialism IDs

### Required configuration

Relevant settings:

- `DATABASE_URL`
- `ENTRA_INTERNAL_TENANT_NAME`
- `ENTRA_IDP_NAME`
- plus broader auth settings used by `/auth/callback`

If auth flows are used, these also matter indirectly:

- `ENTRA_TENANT_ID`
- `ENTRA_CLIENT_ID`
- `ENTRA_CLIENT_SECRET`
- `ENTRA_REDIRECT_URI`
- `SECRET_KEY`

## Dependency Boundaries

### What the profile service does not depend on

Verified by code separation:

- no dependency on AI ticket categorization modules
- no dependency on the fake ticket provider
- no dependency on frontend code at runtime

### What depends on the profile service

- profile management routes in `backend/app/routers/profiles.py`
- auth callback flow in `backend/app/routers/auth.py`
- `/api/v1/auth/me` indirectly, because it reloads the current profile after session validation

## Operational Assumptions

- PostgreSQL is reachable at the configured `DATABASE_URL`
- migrations/schema setup match the ORM model expectations
- auth configuration is valid if Entra login is exercised
- the backend process can commit writes from repository methods

## Dependency Risks

- repository methods committing internally can make future multi-step transactional operations harder to reason about
- generic exception handling in some service methods can hide which dependency actually failed
- if Entra configuration is wrong, the auth flow will fail before or during profile resolution even when the profile service code itself is healthy

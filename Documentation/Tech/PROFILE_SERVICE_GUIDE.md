# Multi-Tenant Profile Service Implementation Guide

## Overview

This guide provides a comprehensive overview of the multi-tenant profile management system. It allows the application to support multiple organizations (tenants) with isolated user profiles, integration with Microsoft Entra ID, and skill-based specialisms.

## Architecture

The profile service follows a standard three-tier architecture:

```
┌─────────────────────────────────────┐
│  API Endpoints (FastAPI)            │
│  /api/v1/profiles                   │
│  /api/v1/tenants                    │
│  /api/v1/specialisms                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Service Layer                      │
│  - ProfileService (Business Logic)  │
│  - TenantService                    │
│  - SpecialismService                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Repository Layer (Data Access)     │
│  - ProfileRepository                │
│  - TenantRepository                 │
│  - IdentityRepository               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Database (PostgreSQL)              │
└─────────────────────────────────────┘
```

-   **API Endpoints:** Defined in `app/routers/profiles.py`.
-   **Service Layer:** Business logic in `app/services/profile_service.py`.
-   **Repository Layer:** Data access logic in `app/repositories/profile_repository.py`.
-   **Database Models:** SQLAlchemy models in `app/models/profile.py`.
-   **Validation Schemas:** Pydantic schemas in `app/schemas/profile.py`.

## Quick Start

### 1. Environment Setup

Create a `.env` file in the `backend` directory with the following variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mydb

# Application
ENVIRONMENT=development
DEBUG=True

# Security
SECRET_KEY=a-secure-secret-key-for-development
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SESSION_COOKIE_NAME=secops_session
SESSION_MAX_AGE_SECONDS=28800

# Microsoft Entra ID
ENTRA_TENANT_ID=your-entra-tenant-id
ENTRA_CLIENT_ID=your-entra-client-id
ENTRA_CLIENT_SECRET=your-entra-client-secret
ENTRA_REDIRECT_URI=http://localhost:8000/auth/callback
ENTRA_INTERNAL_TENANT_NAME=profile-service-test
ENTRA_IDP_NAME=microsoft
FRONTEND_URL=http://localhost:5173

# CORS
CORS_ORIGINS='["http://localhost:5173", "http://127.0.0.1:5173"]'
```

### 2. Start the Database

Use Docker Compose to start the PostgreSQL database:

```bash
cd backend
docker compose up -d
```

### 3. Run Migrations

Apply database schema migrations using Alembic:

```bash
cd backend
alembic upgrade head
```

### 4. Start the API Server

Run the FastAPI application using Uvicorn:

```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000/docs` for interactive testing.

## API Endpoints

### Tenant Management

-   **`POST /api/v1/tenants`**: Create a new tenant.
-   **`GET /api/v1/tenants`**: List all tenants.
-   **`GET /api/v1/tenants/{tenant_id}`**: Get a tenant by ID.

### Profile Management

-   **`POST /api/v1/profiles`**: Create a new user profile.
-   **`GET /api/v1/tenants/{tenant_id}/profiles`**: List profiles for a tenant.
    -   Query Parameters: `status`, `limit`, `offset`.
-   **`GET /api/v1/profiles/{profile_id}`**: Get a profile by ID.
    -   Query Parameters: `tenant_id`.
-   **`PATCH /api/v1/profiles/{profile_id}`**: Update a profile.
    -   Query Parameters: `tenant_id`.
-   **`POST /api/v1/profiles/{profile_id}/deactivate`**: Deactivate a profile.
    -   Query Parameters: `tenant_id`, `reason`.
-   **`GET /api/v1/tenants/{tenant_id}/profiles/search`**: Search for profiles by name.
    -   Query Parameters: `q`, `limit`.

### Identity Provider Integration

-   **`POST /api/v1/profiles/identities`**: Link an external identity to a profile.
-   **`GET /api/v1/auth/profile`**: Find a profile by their external identity.
    -   Query Parameters: `idp_name`, `idp_subject`.

### Specialism Management

-   **`POST /api/v1/specialisms`**: Create a new specialism (skill).
-   **`GET /api/v1/tenants/{tenant_id}/specialisms`**: List specialisms for a tenant.
    -   Query Parameters: `active_only`.
-   **`POST /api/v1/profiles/{profile_id}/specialisms/{specialism_id}`**: Assign a specialism to a profile.
    -   Query Parameters: `tenant_id`, `proficiency_level`, `assigned_by`.
-   **`GET /api/v1/profiles/{profile_id}/specialisms`**: Get a profile's assigned specialisms.
    -   Query Parameters: `tenant_id`.

## Microsoft Entra ID Integration

The profile service is configured to handle authentication via Microsoft Entra ID. The `resolve_entra_profile` function in `profile_service.py` is responsible for:

1.  **Finding or Creating a Tenant:** It uses a default tenant name specified in the settings.
2.  **Finding or Creating an Identity Provider:** It uses a default IdP name from the settings.
3.  **Resolving the Profile:** It attempts to find an existing profile based on the user's Entra `tenant_id` and `object_id`.
4.  **Provisioning a New Profile:** If no profile is found, it creates a new one with the display name from the Entra token.
5.  **Updating Information:** It updates the user's display name if it has changed in Entra ID.

## Database Migrations

Alembic is used for database schema migrations.

-   **Create a new migration:**
    ```bash
    alembic revision --autogenerate -m "Your migration message"
    ```
-   **Apply migrations:**
    ```bash
    alembic upgrade head
    ```
-   **Downgrade migrations:**
    ```bash
    alembic downgrade -1
    ```

## Next Steps

-   **Complete Frontend Integration:** Build out the UI for profile management, specialism assignment, and user settings.
-   **Implement Avatar Uploads:** Integrate with a cloud storage service like AWS S3 or Azure Blob Storage for custom avatar uploads.
-   **Add Audit Logging:** Implement a robust audit trail for all changes to profiles and specialisms.
-   **Expand Identity Providers:** Add support for other OAuth providers like Google.
-   **Refine Authorization:** Implement role-based access control (RBAC) for managing profiles and tenants.

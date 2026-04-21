# Environment

## Purpose

This guide explains the environment and configuration values that affect local development.

It is the reference for:

- what values exist
- what they mean
- which ones have sensible defaults
- which ones you must set yourself

## Source Of Truth

This document is based primarily on:

- `backend/app/config.py`
- `frontend/src/shared/auth.ts`
- `backend/compose.yml`

## Configuration Model

The backend uses `pydantic-settings` and loads values from:

- `backend/.env`

The frontend currently uses a hard-coded API base URL in:

- `frontend/src/shared/auth.ts`

That means backend configuration is more environment-driven than frontend configuration right now.

## Backend Settings

The backend settings class currently defines these values.

### Database

#### `CORE_DATABASE_URL`

Default:

```text
postgresql+asyncpg://postgres:password@localhost:5433/secops_core_db
```

Purpose:

- tells SQLAlchemy how to connect to the core PostgreSQL database
- owns profile, auth, tenant, specialism, and AI ticket-state data

When you must change it:

- if your local DB host, port, user, password, or DB name differ from the default compose setup

#### `LOG_DATABASE_URL`

Default:

```text
postgresql+asyncpg://postgres:password@localhost:5435/logsdb
```

Purpose:

- tells the logging subsystem where to write application, performance, error, and UI interaction logs

### Application

#### `ENVIRONMENT`

Default:

```text
development
```

Purpose:

- simple environment label used in startup logging

#### `DEBUG`

Default:

```text
True
```

Purpose:

- enables debug-style behavior such as SQLAlchemy echo output

### Security And Session Settings

#### `SECRET_KEY`

Default:

```text
dev-secret-key-change-in-production
```

Purpose:

- signs backend session tokens

Important note:

- for real shared environments, this should not remain the default

#### `ALGORITHM`

Default:

```text
HS256
```

Purpose:

- JWT signing algorithm for session tokens

#### `ACCESS_TOKEN_EXPIRE_MINUTES`

Default:

```text
30
```

Purpose:

- currently part of the auth/security configuration set, though the main app flow uses session cookies rather than frontend-managed bearer tokens

#### `SESSION_COOKIE_NAME`

Default:

```text
secops_session
```

Purpose:

- name of the backend session cookie used by the frontend-authenticated flow

#### `SESSION_MAX_AGE_SECONDS`

Default:

```text
28800
```

Purpose:

- session cookie max age in seconds

## Microsoft Entra ID Settings

These are the most important non-default values for the normal authenticated app flow.

### `ENTRA_TENANT_ID`

Default:

```text
""
```

Purpose:

- Microsoft Entra tenant used for login and OpenID configuration

### `ENTRA_CLIENT_ID`

Default:

```text
""
```

Purpose:

- application client ID registered in Entra

### `ENTRA_CLIENT_SECRET`

Default:

```text
""
```

Purpose:

- application client secret for the authorization-code flow

### `ENTRA_REDIRECT_URI`

Default:

```text
http://localhost:8000/auth/callback
```

Purpose:

- redirect URI Entra will return to after login

Important note:

- this must match the Entra application registration

### `ENTRA_INTERNAL_TENANT_NAME`

Default:

```text
profile-service-test
```

Purpose:

- local app tenant name used by the profile service when resolving or provisioning Entra users

### `ENTRA_IDP_NAME`

Default:

```text
microsoft
```

Purpose:

- local identity-provider name used when linking Entra identities to profiles

### `FRONTEND_URL`

Default:

```text
http://localhost:5173
```

Purpose:

- where the backend redirects the browser after successful login

## CORS Settings

### `CORS_ORIGINS`

Default:

```text
["http://localhost:5173", "http://127.0.0.1:5173"]
```

Purpose:

- which frontend origins can make cross-origin requests to the backend

## Frontend Environment Reality

The frontend currently does not appear to use a dedicated `.env` system for API configuration.

Instead, `frontend/src/shared/auth.ts` contains:

```ts
export const API_BASE_URL = "http://localhost:8000";
```

Why this matters:

- if the backend runs somewhere else, you currently need to change frontend code rather than just a frontend env file

## Default Local Environment Shape

If you use the repository defaults, the environment is roughly:

```mermaid
flowchart LR
  Frontend[http://localhost:5173] --> Backend[http://localhost:8000]
  Backend --> Core[(secops_core_db on localhost:5433)]
  Backend --> Logs[(logsdb on localhost:5435)]
  Backend --> Entra[Configured Microsoft Entra tenant]
```

## What You Must Usually Configure Yourself

For a realistic authenticated local run, you should set:

- `SECRET_KEY`
- `ENTRA_TENANT_ID`
- `ENTRA_CLIENT_ID`
- `ENTRA_CLIENT_SECRET`
- confirm `ENTRA_REDIRECT_URI`
- confirm `FRONTEND_URL`

You may also need to change:

- `CORE_DATABASE_URL`
- `LOG_DATABASE_URL`
- `CORS_ORIGINS`

## Most Common Environment Problems

### Backend starts but auth fails

Likely cause:

- Entra values are missing or mismatched

### Frontend loads but backend requests fail

Likely cause:

- backend not actually running on `http://localhost:8000`
- CORS or redirect mismatch

### DB-related API failures

Likely cause:

- `CORE_DATABASE_URL` or `LOG_DATABASE_URL` does not match the running database

## Recommended `.env` Ownership Rule

Because there is no committed `.env.example` right now, the safest team convention is:

- keep real secrets only in local `.env`
- document settings in markdown
- do not assume old docs contain the latest valid values

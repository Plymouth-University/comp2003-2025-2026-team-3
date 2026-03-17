# Entra Profile Service Integration

This document explains the local Microsoft Entra ID integration that was added to the profile service and UI, how it works, what is stored, and how to maintain or extend it later.

## Goal

The objective was to add first-time authentication to the existing profile service without turning the system into a store of company user data.

The implemented design therefore does this:

- Microsoft Entra ID handles sign-in.
- The backend validates the Entra identity.
- The backend resolves a local profile using `tid + oid`.
- A local profile is auto-provisioned on first login.
- The UI trusts only the backend session cookie.

The design intentionally avoids copying broad directory data into the app.

## What data is stored

The current implementation stores only the minimum needed to resolve the user locally:

- Entra tenant ID `tid`
- Entra object ID `oid`
- A local `profile_id`
- A local internal `tenant_id`
- Display name
- Last login timestamp

It does not intentionally pull or persist:

- Company phone numbers
- Company addresses
- Employee directory records
- Additional profile claims beyond what is needed for login and display

## Current local tenant mapping

There are two different tenant concepts:

1. Microsoft Entra tenant
2. Internal app tenant row in the database

The implementation currently uses one internal app tenant row:

- Internal tenant name: `profile-service-test`

On first login, if this internal tenant row does not exist, the backend creates it automatically.

## Implemented auth flow

The current flow is backend-led OAuth/OIDC.

### Sequence

1. Browser opens the frontend.
2. Frontend calls `GET /api/v1/auth/me`.
3. If no session cookie exists, the UI shows the signed-out screen.
4. User clicks `Sign in with Microsoft`.
5. Browser goes to `GET /auth/login` on the backend.
6. Backend creates an OIDC state value and redirects to Entra.
7. Entra authenticates the user and redirects to `http://localhost:8000/auth/callback`.
8. Backend exchanges the authorization code for tokens.
9. Backend validates the Entra ID token.
10. Backend extracts:
   - `tid`
   - `oid`
   - `name`
   - `iss`
11. Backend builds the local identity key as `tid:oid`.
12. Backend looks for an existing `profile_identity`.
13. If none exists:
   - create `tenant` if needed
   - create `profile`
   - create `profile_display`
   - create `profile_avatar`
   - create or find `identity_provider`
   - create `profile_identity`
14. Backend creates a signed session cookie.
15. Backend redirects the browser back to `http://localhost:5173`.
16. Frontend calls `GET /api/v1/auth/me` again and renders the authenticated app.

## Files changed

### Backend

- [backend/app/auth.py](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/app/auth.py)
  Authentication helpers for Entra OIDC, token validation, and signed session cookies.

- [backend/app/routers/auth.py](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/app/routers/auth.py)
  Routes for `/auth/login`, `/auth/callback`, `/api/v1/auth/me`, and `/api/v1/auth/logout`.

- [backend/app/services/profile_service.py](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/app/services/profile_service.py)
  Added `resolve_entra_profile(...)` to find or auto-provision a local profile from Entra claims.

- [backend/app/repositories/profile_repository.py](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/app/repositories/profile_repository.py)
  Added tenant lookup by name and get-or-create identity provider support.

- [backend/app/main.py](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/app/main.py)
  Registered auth routes and protected ticket endpoints using the backend session.

- [backend/app/config.py](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/app/config.py)
  Added Entra and session-related settings.

- [backend/.env.example](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/.env.example)
  Template for required local backend environment variables.

- [backend/.env](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/.env)
  Local runtime values for this test tenant.

- [backend/run_local.sh](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/run_local.sh)
  Helper script to start the local backend server.

### Frontend

- [frontend/src/shared/auth.ts](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend/src/shared/auth.ts)
  Frontend session helpers and backend auth endpoint wrappers.

- [frontend/src/main.ts](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend/src/main.ts)
  Bootstraps the app by checking the backend session first.

- [frontend/src/app/App.ts](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend/src/app/App.ts)
  Adds the signed-out screen, sign-in button, and sign-out control.

- [frontend/src/pages/AccountPage.ts](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend/src/pages/AccountPage.ts)
  Shows local identity-linking information rather than mock personal/company data.

- [frontend/src/pages/Dashboard.ts](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend/src/pages/Dashboard.ts)
  Sends requests with session cookies.

- [frontend/src/components/TicketListContainer.ts](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend/src/components/TicketListContainer.ts)
  Sends requests with session cookies.

- [frontend/run_local.sh](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend/run_local.sh)
  Helper script to start the local frontend dev server.

## Auth endpoints

### `GET /auth/login`

Starts the Entra authorization code flow.

### `GET /auth/callback`

Handles the Entra redirect, exchanges the authorization code, validates the ID token, resolves or provisions the local profile, and sets the session cookie.

### `GET /api/v1/auth/me`

Returns:

- current backend session
- resolved local profile

If no session exists, it returns `401`.

### `POST /api/v1/auth/logout`

Clears the session cookie.

## Protected routes

The following app endpoints now require a valid backend session cookie:

- `GET /api/tickets`
- `GET /api/tickets/{autotask_ticket_id}`
- `GET /api/tickets/stream/categorize`

## Session model

The browser does not store Entra tokens directly in frontend code.

Instead, the backend creates a signed cookie containing:

- `profile_id`
- `tenant_id`
- `entra_tenant_id`
- `object_id`
- `display_name`
- `issuer`
- `iat`
- `exp`

Cookie properties:

- `HttpOnly`
- `SameSite=Lax`
- `Secure=False` for local HTTP development

For production, `Secure` should be enabled and HTTPS should be mandatory.

## Entra configuration used

Current local assumptions:

- App type: `Web`
- Tenant ID: `24e92e30-83bf-4d0e-8a69-3a7b71901db6`
- Client ID: `52b091e9-0fd8-47d7-9e82-9f140281fe55`
- Redirect URI: `http://localhost:8000/auth/callback`
- Frontend URL after login: `http://localhost:5173`

Why `Web` was used:

- The backend performs the authorization-code exchange.
- The backend uses the client secret.
- The frontend stays simple and only consumes the backend session.

## Why this design was chosen

This is the correct fit for the current repo because:

- there was no existing frontend auth library or SPA OIDC setup
- there was no existing backend auth middleware
- the backend already had profile identity tables
- the user wanted the profile service to avoid storing broader company data

## Local verification completed

The following were verified locally during implementation:

- frontend dependencies installed
- backend dependencies installed with CPU-only torch
- spaCy English model installed
- PostgreSQL container started
- Alembic migrations applied
- backend started on `localhost:8000`
- frontend started on `localhost:5173`
- `GET /health` returned `200 OK`
- `GET /api/v1/auth/me` returned `401` before login
- `GET /api/tickets` returned `401` before login
- `GET /auth/login` returned a valid `302` redirect to Microsoft Entra

What was not fully automated:

- A real end-to-end browser sign-in through Entra, because that requires an interactive browser session with your tenant account.

## Troubleshooting

### Problem: Entra login redirects but callback fails

Check:

- `backend/.env` values
- Entra redirect URI still includes `http://localhost:8000/auth/callback`
- backend logs in the terminal running `./run_local.sh`

### Problem: frontend stays on sign-in screen after login

Check:

- browser was redirected back to `http://localhost:5173`
- backend set the `secops_session` cookie
- `GET /api/v1/auth/me` returns `200` in browser dev tools

### Problem: backend starts slowly

Reason:

- sentence-transformer model loading happens on startup

That is expected on first run because `all-MiniLM-L6-v2` may need to download.

### Problem: ticket endpoints fail after login

Check:

- backend logs for AI model load failures
- internet access for initial Hugging Face model download
- local Python environment still active and intact

## Security follow-up

The Entra client secret used during setup should be rotated after testing, because it was shared interactively during implementation.

After rotation:

1. Update [backend/.env](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/.env)
2. Restart the backend

## Recommended future improvements

- Add production-only HTTPS cookie settings.
- Add a real persistent internal mapping table between Entra tenant IDs and internal tenant rows.
- Add audit logs for authentication and provisioning events.
- Add backend tests for `/auth/callback`, `/api/v1/auth/me`, and profile auto-provisioning.
- Add a lightweight health endpoint for the Entra config and model readiness.
- Move secrets into a proper secret manager instead of a local `.env`.

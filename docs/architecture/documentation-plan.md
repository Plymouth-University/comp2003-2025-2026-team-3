# Documentation Migration Plan

## Purpose

This plan defines how to migrate repository documentation so it reflects the implemented system rather than historical markdown.

Scope for verification in this plan:

- Primary source of truth: `backend/app/**` and `frontend/src/**`
- Supporting source for setup/run details: root `README.md`, `backend/requirements.txt`, `backend/compose.yml`, `backend/run_local.sh`, `frontend/package.json`, `frontend/run_local.sh`
- Historical context only: `docs/legacy/**`

Out of scope for truth claims unless explicitly needed later:

- `node_modules/`
- `dist/`
- `__pycache__/`
- logs
- generated data

## Verification Status

### Verified from source code

- The backend is a FastAPI application with:
  - health and cache endpoints
  - protected ticket endpoints
  - Microsoft Entra ID login/session routes
  - profile, tenant, identity-linking, and specialism APIs
- The ticket source is currently a local JSON-backed provider in `backend/app/providers/fake_autotask.py`
- AI ticket enrichment is implemented in `backend/app/services/ai/**`
- The backend persists profile data in PostgreSQL via async SQLAlchemy models, repositories, and services
- The frontend is a vanilla TypeScript SPA with hash-based routing and Tailwind-built styling
- The frontend depends on backend session cookies and calls the backend directly for auth state and ticket data
- Several new docs files already exist under `docs/architecture/`, `docs/getting-started/`, and `docs/runbooks/`, but they are empty placeholders

### Ambiguities or assumptions to flag

- `backend/app/main.py` still uses a `FakeAutotaskProvider`, so any documentation about a real Autotask integration should be treated as future-state or historical
- The frontend `Settings` and `ClosedTickets` pages are currently placeholder/demo behavior, not fully integrated product features
- The AI service includes both request-time enrichment used by the API and file-oriented processing/storage utilities; the operational importance of the file-processing path should be confirmed before documenting it as a core workflow
- Root `README.md` is materially outdated in places because it claims there is no persistence layer and no authentication, while the current code includes both

## Main Systems And Responsibilities

### 1. Frontend SPA

Source:

- `frontend/src/main.ts`
- `frontend/src/App.ts`
- `frontend/src/pages/**`
- `frontend/src/components/**`
- `frontend/src/shared/**`

Responsibility:

- Bootstraps the browser app
- Checks current backend-authenticated user on startup
- Presents signed-out or authenticated application states
- Provides hash-based navigation between dashboard, ticket list/detail, account, settings, and closed tickets screens
- Fetches ticket data and renders AI-enriched ticket views

Key boundaries:

- Does not perform AI categorization itself
- Depends on backend cookies for authentication
- Uses simple DOM-construction helpers rather than a frontend framework

### 2. Backend API Application

Source:

- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/database.py`

Responsibility:

- Hosts the FastAPI app
- Configures CORS and lifespan behavior
- Exposes health, cache, category, ticket, and streaming ticket endpoints
- Registers auth and profile routers
- Coordinates provider access and AI enrichment before returning ticket payloads

### 3. Authentication And Session System

Source:

- `backend/app/auth.py`
- `backend/app/routers/auth.py`
- `frontend/src/shared/auth.ts`

Responsibility:

- Starts Microsoft Entra ID authorization-code sign-in
- Validates Entra ID tokens against OpenID configuration and JWKS
- Resolves or provisions a local profile after successful login
- Issues and validates signed backend session cookies
- Exposes `/api/v1/auth/me` and logout behavior used by the frontend

### 4. Profile And Tenant Management System

Source:

- `backend/app/models/profile.py`
- `backend/app/schemas/profile.py`
- `backend/app/repositories/profile_repository.py`
- `backend/app/services/profile_service.py`
- `backend/app/routers/profiles.py`

Responsibility:

- Stores tenant, profile, identity-provider, profile-identity, avatar, and specialism data
- Enforces multi-tenant profile operations in the service and repository layers
- Supports CRUD-style profile and tenant APIs
- Links external identities to local profiles
- Stores specialism assignments for profiles

### 5. Ticket Source Provider

Source:

- `backend/app/providers/fake_autotask.py`
- `backend/app/models/ticket.py`

Responsibility:

- Loads ticket records from local JSON
- Caches those records in memory after first read
- Provides ticket objects to the API layer

Important documentation note:

- This should be documented explicitly as a fake or simulated provider, because several legacy docs imply a more mature external integration than the code shows

### 6. AI Ticket Enrichment System

Source:

- `backend/app/services/ai/__init__.py`
- `backend/app/services/ai/processor.py`
- `backend/app/services/ai/categorizer.py`
- `backend/app/services/ai/priority_calculator.py`
- `backend/app/services/ai/text_processor.py`
- `backend/app/services/ai/description_generator.py`
- `backend/app/services/ai/embedding_cache.py`
- `backend/app/services/ai/config.py`
- `backend/app/services/ai/storage.py`
- `backend/app/services/ai/logging_config.py`

Responsibility:

- Extracts and preprocesses ticket text
- Predicts categories via keyword and semantic methods
- Calculates priority scores and labels
- Generates AI descriptions
- Caches embeddings for performance
- Supports single-ticket and batch categorization flows
- Includes file-based processing/storage helpers for batch workflows

### 7. Developer Run And Environment Layer

Source:

- `backend/requirements.txt`
- `backend/compose.yml`
- `backend/run_local.sh`
- `frontend/package.json`
- `frontend/run_local.sh`

Responsibility:

- Defines local Python and frontend dependencies
- Provides a local PostgreSQL service
- Provides backend and frontend startup commands

## Proposed Documentation Structure Under `docs/`

The current preferred structure in `AGENTS.md` is good and should be retained. The migration should organize docs around stable questions a new developer asks first.

### `docs/getting-started/`

Recommended files:

- `docs/getting-started/first-time-setup.md`
  - machine prerequisites
  - Python and Node setup
  - database startup
  - backend/frontend install steps
  - first successful login and smoke test
- `docs/getting-started/environment.md`
  - required environment variables
  - which values are local defaults vs required secrets
  - backend/frontend URL coupling
  - Entra-specific configuration
- `docs/getting-started/daily-run.md`
  - everyday start/stop workflow
  - fastest dev loop
  - common validation checks before committing

### `docs/architecture/`

Recommended files:

- `docs/architecture/system-overview.md`
  - top-level system map
  - request flows
  - external dependencies
  - what is prototype vs production-like
- `docs/architecture/backend-overview.md`
  - FastAPI app structure
  - routers/services/repositories/models boundaries
  - ticket flow and auth flow entry points
- `docs/architecture/frontend-overview.md`
  - bootstrap path
  - routing model
  - screen/component/shared utility boundaries
  - backend integration pattern
- `docs/architecture/services-boundaries.md`
  - service inventory and ownership lines
  - auth vs profile vs AI vs provider responsibilities
  - which modules are placeholders
- `docs/architecture/documentation-plan.md`
  - this migration plan

### `docs/services/`

Recommended new files:

- `docs/services/authentication.md`
  - Entra flow, cookies, `/auth/*` and `/api/v1/auth/*`
- `docs/services/profile-service.md`
  - tenant/profile/specialism models and API behavior
- `docs/services/ticket-api.md`
  - `/api/tickets`, `/api/categories`, cache endpoints, SSE stream
- `docs/services/ai-ticket-enrichment.md`
  - AI module responsibilities, batch vs sequential behavior, cache behavior
- `docs/services/frontend-app.md`
  - UI screens, data dependencies, current limitations

### `docs/runbooks/`

Recommended files:

- `docs/runbooks/run-entire-code.md`
  - backend, database, frontend startup in correct order
  - smoke-test checklist
- `docs/runbooks/troubleshooting.md`
  - backend unavailable at bootstrap
  - auth callback/session failures
  - missing model or Python dependency issues
  - database connectivity problems
- `docs/runbooks/entra-local-setup.md`
  - optional dedicated runbook if Entra local setup proves too large for `environment.md`
- `docs/runbooks/ai-operations.md`
  - only if the file-processing AI workflow is still actively used and should be run by developers

## Migration Principles

- Rewrite around implemented behavior, not earlier intent
- Preserve useful legacy detail by extracting it before archiving or deleting files
- Prefer a few canonical docs over many overlapping ones
- Separate core product docs from code-level reference docs
- Mark placeholders and partial implementations clearly
- Document failure modes and operational dependencies, not just happy paths

## Existing Docs Mapping

The mapping below classifies each current doc into one of four actions:

- keep and rewrite
- merge
- archive
- delete

### Keep And Rewrite

- `docs/architecture/system-overview.md`
  - Keep as a canonical top-level architecture entry point; currently empty
- `docs/architecture/backend-overview.md`
  - Keep; currently empty and should become the verified backend map
- `docs/architecture/frontend-overview.md`
  - Keep; currently empty and should describe the actual SPA structure
- `docs/architecture/services-boundaries.md`
  - Keep; currently empty and should define module ownership lines
- `docs/getting-started/first-time-setup.md`
  - Keep; currently empty and should be rebuilt from run scripts and config
- `docs/getting-started/environment.md`
  - Keep; currently empty and should document real env vars from `backend/app/config.py`
- `docs/getting-started/daily-run.md`
  - Keep; currently empty and should capture the common dev workflow
- `docs/runbooks/run-entire-code.md`
  - Keep; currently empty and should become the canonical startup runbook
- `docs/runbooks/troubleshooting.md`
  - Keep; currently empty and should list known failure modes

### Merge

- `docs/legacy/SYSTEM_ARCHITECTURE.md`
  - Merge useful high-level framing into `docs/architecture/system-overview.md`
- `docs/legacy/FRONTEND_ARCHITECTURE.md`
  - Merge verified parts into `docs/architecture/frontend-overview.md`
- `docs/legacy/FRONTEND_APP_CONTROLLER.md`
  - Merge routing and controller details into `docs/architecture/frontend-overview.md` or `docs/services/frontend-app.md`
- `docs/legacy/AI_SYSTEM_ARCHITECTURE.md`
  - Merge verified AI module descriptions into `docs/services/ai-ticket-enrichment.md`
- `docs/legacy/API_REFERENCE.md`
  - Merge verified endpoint details into `docs/services/ticket-api.md`, `docs/services/authentication.md`, and `docs/services/profile-service.md`
- `docs/legacy/ENTRA_ID_INTEGRATION.md`
  - Merge into `docs/services/authentication.md` and possibly `docs/runbooks/entra-local-setup.md`
- `docs/legacy/PROFILE_SERVICE_GUIDE.md`
  - Merge into `docs/services/profile-service.md`
- `docs/legacy/AI_OPERATIONS_GUIDE.md`
  - Merge only the still-true operational guidance into `docs/services/ai-ticket-enrichment.md` or `docs/runbooks/ai-operations.md`
- `docs/legacy/LOCAL_DEVELOPMENT_GUIDE.md`
  - Merge into `docs/getting-started/first-time-setup.md`, `docs/getting-started/daily-run.md`, and `docs/runbooks/run-entire-code.md`
- `docs/legacy/LOGGING_ARCHITECTURE.md`
  - Merge any verified logging notes into `docs/architecture/backend-overview.md` or `docs/runbooks/troubleshooting.md`
- `docs/legacy/README.md`
  - Merge any useful index/navigation concepts into a future docs index if one is added

### Archive

- `docs/legacy/PROJECT_ORGANIZATION.md`
  - Archive as historical analysis; parts are already inaccurate relative to current structure
- `docs/legacy/PROJECT_SAFETY_GUIDE.md`
  - Archive if its guidance is still desired only as historical team process; it is not core product/system documentation
- `docs/legacy/FRONTEND_DOM_UTILS.md`
  - Archive unless the team explicitly wants file-level utility docs; the helper is small and self-explanatory
- `docs/legacy/FRONTEND_TAILWIND_CONFIG.md`
  - Archive unless styling/tooling docs are a priority; not essential for initial system understanding

### Delete

No legacy docs should be deleted in the first migration pass.

Reason:

- `AGENTS.md` explicitly says not to delete legacy docs before extracting useful information
- Several legacy docs are partially correct and valuable as rewrite inputs even when they contain outdated claims

Planned delete candidates after extraction review:

- none yet

## Missing Documentation Needed For A New Developer

These are the highest-value gaps that still force code-reading today.

### 1. Verified system overview

Missing:

- A single accurate entry point explaining how the frontend, backend, PostgreSQL, Entra ID, fake ticket provider, and AI modules fit together

Why it matters:

- Current root and legacy docs disagree about whether auth and persistence even exist

### 2. Authentication flow and local Entra setup

Missing:

- A concise, verified guide covering required env vars, login flow, cookies, callback behavior, and common auth failures

Why it matters:

- New developers will struggle to get past sign-in or understand session behavior without reading backend auth code

### 3. Ticket API and data-flow documentation

Missing:

- A clear explanation of where tickets come from, which endpoints require auth, how AI enrichment is attached, and what batch mode changes

Why it matters:

- This is the main product workflow and currently spans provider, API, and AI service code

### 4. Profile/tenant domain model guide

Missing:

- A doc that explains tenant, profile, identity provider, profile identity, avatar, and specialism relationships in one place

Why it matters:

- The model is not trivial, and auth provisioning depends on understanding it

### 5. Frontend architecture and feature status

Missing:

- An accurate explanation of routing, startup bootstrap, page responsibilities, and which screens are real versus placeholder/demo implementations

Why it matters:

- Without this, new developers will overestimate the completeness of `Settings` and `ClosedTickets`

### 6. Local runbook with smoke-test checklist

Missing:

- A canonical sequence for starting PostgreSQL, backend, and frontend, then validating health, auth, and ticket loading

Why it matters:

- Run instructions are currently spread across scripts, package metadata, and outdated markdown

### 7. Failure modes and troubleshooting

Missing:

- Known breakpoints such as backend not reachable, DB not running, missing Python models/dependencies, Entra misconfiguration, and session/profile mismatch

Why it matters:

- This directly affects onboarding speed

### 8. Documentation ownership and freshness rules

Missing:

- A short docs-maintenance note stating which files are canonical and how future updates should be sourced from code

Why it matters:

- It reduces the chance of the new docs drifting back into contradiction

## Suggested Migration Sequence

This task only creates the plan, but the recommended execution order for the rewrite phase is:

1. Write `docs/architecture/system-overview.md`
2. Write `docs/architecture/backend-overview.md`
3. Write `docs/architecture/frontend-overview.md`
4. Write `docs/services/authentication.md`
5. Write `docs/services/profile-service.md`
6. Write `docs/services/ticket-api.md`
7. Write `docs/services/ai-ticket-enrichment.md`
8. Write `docs/getting-started/environment.md`
9. Write `docs/getting-started/first-time-setup.md`
10. Write `docs/getting-started/daily-run.md`
11. Write `docs/runbooks/run-entire-code.md`
12. Write `docs/runbooks/troubleshooting.md`
13. Move superseded legacy files into an explicitly archived state only after their useful content is captured

## Recommended Success Criteria For The Migration

The migration is successful when a new developer can answer these questions without reading much code:

- What are the main systems in the repository?
- How does sign-in work end to end?
- Where do tickets come from today?
- How are tickets enriched by AI?
- Which frontend pages are production-like and which are placeholders?
- How do I run the full stack locally?
- What environment variables are required?
- Where should I update docs when behavior changes?


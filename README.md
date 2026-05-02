# SecOps Autotask AI Ticketing System

> **An end-to-end security operations prototype combining AI-assisted ticket enrichment, assignment recommendations, Microsoft Entra sign-in, persisted ticket state, and a lightweight TypeScript frontend.**

---

## Project Overview

This repository is a full-stack prototype for exploring how security-operations ticket work can be supported by local profile management, AI enrichment, assignment recommendations, and a browser-based ticket interface.

It currently includes:

- a FastAPI backend that owns auth, profile persistence, ticket enrichment, AI ticket state, and assignment logic
- a vanilla TypeScript single-page frontend for dashboard, active-ticket, closed-ticket, ticket-detail, account, and settings workflows
- Microsoft Entra ID sign-in with backend-managed session cookies
- PostgreSQL-backed tenants, profiles, identities, specialisms, and persisted AI ticket state
- a separate PostgreSQL logs database schema for durable application, performance, error, and UI interaction logs
- a fake local Autotask-style ticket provider backed by JSON data
- AI categorization and priority scoring using configured categories, keyword matching, sentence embeddings when available, and priority heuristics
- SecOps' specialism-aware assignment recommendations, manual AI assignment overrides, AI category overrides, ticket edits, and ticket-close reasons

The frontend does not categorize tickets itself. It consumes backend-authenticated API responses and displays ticket state that has already been enriched or persisted by the backend.

---

## Architecture Overview

```text
Browser
   |
Vanilla TypeScript SPA
   |
FastAPI Backend
   |-- Microsoft Entra ID auth flow + signed session cookie
   |-- Core PostgreSQL database
   |     |-- tenants, profiles, identities, avatars, specialisms
   |     `-- persisted AI ticket state in the AITicketOps schema
   |-- Logs PostgreSQL database
   |     `-- application, performance, error, and UI click log tables
   |-- Fake Autotask provider
   |     `-- backend/data/tickets.json
   |-- AI enrichment pipeline (spaCy + sentence-transformers + heuristics)
   |     `-- configured categories, keyword matching, embeddings, priority scoring
   `-- AI assignment + oversight services
         `-- recommendations, manual overrides, protected auto-assignment rules
```

### Key Principle

> **Auth, persistence, AI decisions, and assignment automation live in the backend.**
> The frontend is responsible for presentation, navigation, user interaction, and calling the backend APIs with the session cookie.

---

## Project Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py                    # FastAPI app, lifespan worker, legacy ticket/category/cache endpoints
|   |   |-- auth.py                    # Entra/OIDC helpers and backend session token handling
|   |   |-- config.py                  # pydantic-settings configuration
|   |   |-- database.py                # core DB engine/session setup
|   |   |-- log_database.py            # dedicated logs DB engine/session setup
|   |   |-- routers/
|   |   |   |-- auth.py                 # login, callback, current user, logout
|   |   |   |-- profiles.py             # tenant, profile, identity, and specialism APIs
|   |   |   `-- ai_state.py             # persisted AI ticket-state and assignment APIs
|   |   |-- services/
|   |   |   |-- ai/                     # categorization, text extraction, priority, embedding cache
|   |   |   |-- ai_assignment_service.py # specialism/workload-aware assignment recommendations
|   |   |   |-- ai_oversight_service.py  # queue-level auto-assignment rules
|   |   |   |-- ai_state_service.py      # refresh/list/edit/close/override ticket-state logic
|   |   |   |-- profile_service.py       # tenant/profile/identity/specialism business logic
|   |   |   `-- log_writer.py           # durable log-writing helpers
|   |   |-- repositories/              # database access layer
|   |   |-- models/                    # SQLAlchemy models for profiles, AI state, logs, tickets
|   |   |-- schemas/                   # Pydantic request/response schemas
|   |   `-- providers/                 # fake Autotask JSON provider
|   |-- alembic/                      # core database migrations
|   |-- alembic_logs/                 # logs database migrations
|   |-- data/                         # local ticket/category/demo data
|   |-- scripts/                      # migration and data utility scripts
|   |-- compose.yml                   # local PostgreSQL containers
|   |-- requirements.txt
|   `-- run_local.py                  # local backend runner
|
|-- frontend/
|   |-- src/
|   |   |-- main.ts                    # frontend bootstrap and backend reachability handling
|   |   |-- App.ts                     # SPA shell, auth states, sidebar, hash routing
|   |   |-- pages/                     # dashboard, active/closed tickets, detail, account, settings
|   |   |-- components/                # ticket cards, menus, edit/close/reassign modals
|   |   `-- shared/                   # auth, API clients, types, DOM helpers
|   |-- public/                       # UI images/icons used by the vanilla frontend
|   |-- scripts/                      # asset-copy helper
|   |-- package.json
|   `-- run_local.py                  # local frontend runner
|
|-- docs/
|   |-- getting-started/
|   |-- architecture/
|   |-- services/
|   |-- runbooks/
|   `-- legacy/
|
|-- README.md
`-- README.updated.md
```

---

## Backend

### Main Technologies

- FastAPI
- Uvicorn
- Pydantic and pydantic-settings
- SQLAlchemy asyncio
- Alembic
- PostgreSQL
- asyncpg
- python-jose
- sentence-transformers
- PyTorch
- Docker Compose

### Current Responsibilities

- expose health, auth, profile, specialism, category, cache, ticket, AI ticket-state, assignment, and oversight endpoints
- perform Microsoft Entra ID authorization-code sign-in and backend session-cookie management
- provision or resolve local profiles from Entra identity claims
- persist tenants, profiles, identities, avatar metadata, specialisms, and AI ticket state in the core database
- maintain a separate logs database schema for structured logging data
- load raw ticket data from the fake local provider in `backend/data/tickets.json`
- enrich tickets with category, confidence, priority label, priority score, and classification method
- refresh persisted AI ticket state  database from the provider and keep unique identifiers from being overwritten
- support manual ticket edits, ticket closing with a reason, ai-category manual override with a reason, and assignment override
- recommend assignees using profile specialisms, same-company continuity, current assignment, and workload signals
- optionally run a background AI oversight worker that evaluates queue tickets and applies conservative assignment rules

### Important Current Endpoints

| Endpoint | Description |
|---|---|
| `/health` | Backend health check |
| `/auth/login` | Start Microsoft Entra ID login |
| `/auth/callback` | Resolve Entra identity, provision/find profile, and set the backend session cookie |
| `/api/v1/auth/me` | Return the current authenticated session and resolved profile |
| `/api/v1/auth/logout` | Clear the backend session cookie |
| `/api/v1/auth/profile/specialisms` | Get or replace the authenticated user's category-aligned specialisms |
| `/api/v1/ai/categories` | Return the configured AI ticket categories for authenticated users |
| `/api/v1/ai/ticket-states/refresh` | Refresh persisted AI ticket state from the fake provider |
| `/api/v1/ai/ticket-states/my-assigned` | List open tickets where the current user is primary or secondary |
| `/api/v1/ai/ticket-states/my-primary` | List open tickets where the current user is primary |
| `/api/v1/ai/ticket-states/my-secondary` | List open tickets where the current user is secondary |
| `/api/v1/ai/ticket-states/team` | List open persisted ticket state for a queue, defaulting to `MS - SecOps` |
| `/api/v1/ai/ticket-states/my-primary/closed` | List closed primary tickets for the current user |
| `/api/v1/ai/ticket-states/my-secondary/closed` | List closed secondary tickets for the current user |
| `/api/v1/ai/ticket-states/{autotask_ticket_id}` | Get or patch one persisted AI ticket-state row |
| `/api/v1/ai/ticket-states/{autotask_ticket_id}/close` | Mark a persisted ticket as closed with a reason |
| `/api/v1/ai/ticket-states/{autotask_ticket_id}/category-override` | Manually override a ticket category with a reason |
| `/api/v1/ai/ticket-states/{autotask_ticket_id}/assignment-recommendation` | Return specialism/workload-aware assignment recommendation details |
| `/api/v1/ai/ticket-states/{autotask_ticket_id}/assignment-override` | Set or clear a manual assignment override |
| `/api/v1/ai/oversight/run` | Run AI assignment oversight once for the current tenant queue |
| `/api/categories` | Legacy unauthenticated category endpoint |
| `/api/tickets` | Legacy authenticated, on-the-fly enriched ticket listing |
| `/api/tickets/{autotask_ticket_id}` | Legacy authenticated, on-the-fly enriched ticket detail |
| `/api/tickets/stream/categorize` | Legacy authenticated SSE categorization stream |
| `/api/cache/stats` | Return embedding-cache stats |
| `/api/cache/clear` | Clear the in-memory embedding cache |

### Important Current Reality

- ticket data still comes from a fake local provider, not a real Autotask API integration
- the active frontend ticket views use persisted AI ticket-state endpoints under `/api/v1/ai`, not the older `/api/tickets` list path
- core profile data and AI ticket state now share the core database so profile foreign keys can protect assignment data and prevent data redundancy leading to inconsistency
- logs use a separate database and alembic migration tree
- the embedding model defaults to local-only loading; if the model is not available locally, the AI pipeline falls back to keyword-style behavior instead of downloading at runtime
- some assignment automation writes primary-resource changes back to `backend/data/tickets.json`, because the fake provider is the current source adapter

---

## Frontend

### Main Technologies

- Vanilla TypeScript
- Tailwind CSS
- TypeScript compiler watch mode
- live-server
- no React
- no Vite runtime

### Current Responsibilities

- bootstrap the app in the browser and mount it into `#app`
- check the current backend-authenticated user on startup through `/api/v1/auth/me`
- render signed-in and signed-out states
- start Microsoft sign-in by redirecting to `/auth/login`
- route with URL hashes between dashboard, active tickets, closed tickets, ticket detail, account, and settings
- fetch and display persisted AI ticket state from `/api/v1/ai/ticket-states/...`, `/api/v1/ai/ticket-states/my-primary`,  `/api/v1/ai/ticket-states/my-secondary`
- show active ticket views for my assigned, my primary, my secondary, and team queue tickets
- show closed-ticket views for primary and secondary assignments
- group active tickets by AI category and support search, filters, category view collapse, due-date sorting, priority sorting, and assignment-state sorting
- support ticket edit, ticket close, category reassignment, assignment recommendation, and assignment override workflows through backend APIs
- let users manage their category-aligned specialisms in Settings so the backend recommendation engine has profile skill signals
- show account/profile identity information resolved by the backend

### Important Current Reality

- the frontend uses a backend-led auth model and sends cookies with API calls
- it does not store, validate, or refresh Microsoft identity tokens itself
- the API base URL is hard-coded in `frontend/src/shared/auth.ts` as `http://localhost:8000`
- most useful ticket workflows require a valid backend session and populated AI ticket state
- the frontend is built with explicit DOM construction rather than a component framework

---

## How To Get Started

The detailed onboarding docs live under `docs/getting-started/` so setup instructions do not need to be duplicated in every document.

Use these in order:

1. [First-Time Setup](docs/getting-started/first-time-setup.md)
2. [Environment](docs/getting-started/environment.md)
3. [Daily Run](docs/getting-started/daily-run.md)

If startup fails, use:

- [Troubleshooting](docs/runbooks/troubleshooting.md)

### Quick Summary

At a high level, local development currently looks like:

1. start PostgreSQL from `backend/compose.yml`
2. prepare the backend virtual environment and install Python dependencies
3. create `backend/.env` with Entra settings if you want the authenticated flow to work
4. run the core and logs database migrations
5. start the backend on `http://localhost:8000`
6. install frontend dependencies with `npm install`
7. start the frontend on `http://localhost:5173`
8. sign in with Microsoft and make sure AI ticket state has been refreshed/populated

The backend helper can do the common local backend startup work:

```bash
cd backend
python run_local.py
```

The frontend helper expects `node_modules` to already exist:

```bash
cd frontend
python run_local.py
```

---

## Documentation Map

For architecture and service-level understanding, start with:

- [System Overview](docs/architecture/system-overview.md)
- [Backend Overview](docs/architecture/backend-overview.md)
- [Frontend Overview](docs/architecture/frontend-overview.md)
- [Service Boundaries](docs/architecture/services-boundaries.md)

For service-specific detail:

- [Profile Service](docs/services/profile-service/overview.md)
- [Logging System](docs/services/logging-system/overview.md)
- [AI Service](docs/services/ai-service/overview.md)

---

## Key Engineering Decisions

- No heavy frontend framework: the UI uses explicit DOM construction, hash routing, and small API helper modules.
- Backend-owned intelligence: categorization, priority scoring, assignment recommendation, assignment override, and oversight logic stay server-side.
- Backend-owned auth: Entra validation and session cookies are handled by the backend.
- Persisted AI state: the newer ticket workflows read and mutate `TicketAIState` rows instead of recomputing everything in the browser.
- Manual work is preserved: edited ticket fields, category overrides, assignment overrides, and close reasons are tracked in persisted AI state.
- Layered profile domain: profile/tenant/specialism logic is split into router, service, repository, schema, and model layers.
- Modular AI pipeline: category loading, text extraction, keyword/semantic matching, priority scoring, embedding caching, and logging are separated into dedicated modules.
- Conservative AI oversight: background assignment automation respects manual overrides and protects tickets that appear to have already started.

---

## Known Limitations

This is still a prototype or evolving system in several important ways:

- the ticket provider is fake/local rather than a real external Autotask integration
- local ticket data in `backend/data/tickets.json` can be mutated by fake-provider assignment operations
- authenticated flows depend on Microsoft Entra ID being configured correctly
- there is no checked-in backend `.env.example` at the moment
- the frontend API base URL is hard-coded to localhost
- the project currently has both legacy on-the-fly ticket enrichment endpoints and newer persisted AI ticket-state endpoints
- persisted AI ticket views depend on ticket-state refreshes and profile-resource mapping
- the semantic embedding model may not load unless it already exists locally, because local-only model loading is enabled by default
- the logs database schema exists separately, but logging coverage is still evolving
- automated test coverage is currently limited

---

## Final Note

This project is no longer just "AI tickets plus a frontend".

It is now better understood as:

> a backend-centered ticket-operations prototype that combines Microsoft auth, local profile persistence, category-aware AI ticket state, specialism-based assignment recommendations, conservative oversight automation, and a lightweight TypeScript interface.

That makes the newer docs under `docs/` the best place to continue after this README.

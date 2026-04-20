# SecOps Autotask AI Ticketing System

> **An end-to-end security operations prototype combining AI-assisted ticket enrichment with a lightweight TypeScript frontend and a FastAPI backend.**

---

## Project Overview

This repository is a full-stack prototype for exploring how ticket operations, local profile management, and AI-assisted enrichment can work together in one system.

It currently includes:

- an AI-assisted backend for ticket categorization, priority scoring, and explanation generation
- a vanilla TypeScript single-page frontend
- Microsoft Entra ID sign-in with backend session cookies
- a PostgreSQL-backed profile and tenant domain
- a fake local ticket provider backed by JSON data

The frontend does not categorize tickets itself. It consumes ticket data that has already been enriched by the backend.

---

## Architecture Overview

```text
Browser
   ↓
Vanilla TypeScript SPA
   ↓
FastAPI Backend
   ├─ Microsoft Entra ID auth flow
   ├─ Profile + tenant persistence (PostgreSQL)
   ├─ Fake ticket provider (local JSON)
   └─ AI enrichment pipeline (spaCy + sentence-transformers + heuristics)
```

### Key Principle

> **Auth, persistence, and AI decisions live in the backend.**
> The frontend is responsible for presentation, navigation, and user interaction.

---

## Project Structure

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ main.py                # FastAPI entry point and ticket endpoints
│  │  ├─ auth.py                # Entra/OIDC and backend session helpers
│  │  ├─ routers/               # Auth and profile API routes
│  │  ├─ services/
│  │  │  ├─ ai/                 # AI enrichment pipeline
│  │  │  └─ profile_service.py  # Profile/tenant/specialism logic
│  │  ├─ repositories/          # Database access layer
│  │  ├─ models/                # SQLAlchemy models
│  │  └─ providers/             # Ticket source providers
│  ├─ alembic/                  # Database migrations
│  ├─ data/                     # Local ticket/category data
│  ├─ compose.yml               # Local PostgreSQL
│  └─ requirements.txt
│
├─ frontend/
│  ├─ src/
│  │  ├─ main.ts                # Frontend bootstrap
│  │  ├─ App.ts                 # SPA shell and routing
│  │  ├─ pages/                 # Screen-level views
│  │  ├─ components/            # Reusable UI components
│  │  └─ shared/                # Auth helpers, types, DOM utilities
│  ├─ package.json
│  └─ run_local.sh
│
├─ docs/
│  ├─ getting-started/
│  ├─ architecture/
│  ├─ services/
│  └─ runbooks/
│
└─ README.md
```

---

## Backend

### Main Technologies

- FastAPI
- SQLAlchemy asyncio
- PostgreSQL
- sentence-transformers
- spaCy
- scikit-learn

### Current Responsibilities

- expose health, auth, profile, cache, category, and ticket endpoints
- perform Microsoft Entra ID sign-in and backend session management
- persist tenants, profiles, identities, avatar config, and specialisms
- load raw ticket data from the current fake provider
- enrich tickets with category, priority, and explanation data

### Important Current Endpoints

| Endpoint | Description |
|---|---|
| `/health` | Backend health check |
| `/auth/login` | Start Microsoft Entra ID login |
| `/api/v1/auth/me` | Return current authenticated user |
| `/api/categories` | Return category list |
| `/api/tickets` | Return AI-enriched tickets |
| `/api/cache/stats` | Return embedding-cache stats |

### Important Current Reality

- ticket data is still coming from a fake local provider, not a real Autotask API integration
- the backend owns AI categorization and auth/session logic

---

## Frontend

### Main Technologies

- Vanilla TypeScript
- Tailwind CSS
- live-server
- no React
- no Vite runtime

### Current Responsibilities

- bootstrap the app in the browser
- check current backend-authenticated user on startup
- render signed-in and signed-out states
- navigate between dashboard, active tickets, ticket detail, account, settings, and closed tickets
- fetch and display AI-enriched ticket data

### Important Current Reality

- the frontend uses a backend-led auth model
- it does not store or validate identity tokens itself
- some screens, especially `Settings` and `Closed Tickets`, are still placeholder or demo-level

---

## How To Get Started

The detailed onboarding docs now live under `docs/getting-started/` so we do not duplicate setup instructions in multiple places.

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
3. install the spaCy model
4. create `backend/.env` with Entra settings if you want the authenticated flow to work
5. run database migrations
6. start the backend
7. start the frontend

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

- No heavy frontend framework: the UI uses explicit DOM construction and simple routing.
- Backend-owned intelligence: ticket categorization and priority logic stay server-side.
- Backend-owned auth: Entra validation and session cookies are handled on the backend.
- Layered profile domain: profile/tenant logic is split into router, service, repository, and model layers.
- Modular AI pipeline: text processing, categorization, priority scoring, description generation, caching, and logging are separated into dedicated modules.

---

## Known Limitations

This is still a prototype or evolving system in several important ways:

- the ticket provider is fake/local rather than a real external integration
- authenticated flows depend on Microsoft Entra ID being configured correctly
- some frontend pages are placeholders
- AI startup can be heavy because models load at runtime
- parts of the AI service still include prototype-style offline/file-processing workflows
- there is no checked-in backend `.env.example` at the moment

---

## Final Note

This project is no longer just “AI tickets plus a frontend”.

It is now better understood as:

> a backend-centered system that combines auth, local profile persistence, ticket enrichment, and a lightweight frontend interface.

That makes the newer docs under `docs/` the best place to continue after this README.

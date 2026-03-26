# UPDATE

## Purpose

This file is an AI handoff note for rapid continuation of development.

Use this file as the first context source before making further AI-service changes.

## High-Level Status

The AI service has been moved from a prototype classifier into a hosted, database-backed recommendation layer for SecOps tickets.

Current implemented capabilities:

- configurable ticket categorisation from `backend/data/ticket_categories.json`
- CPU-friendly hybrid classification:
  - keyword matching
  - optional `all-MiniLM-L6-v2` semantic similarity
  - keyword-only fallback if model unavailable
- heuristic priority scoring
- persisted AI ticket state in `ticket_ai_state`
- profile/resource mapping from ticket primary/secondary resource names to local profiles
- frontend `Active Tickets` page backed by AI-state endpoints
- real profile specialism persistence from `Settings`
- assignment recommendation based on:
  - category-specialism match
  - company continuity
  - workload balancing
  - current ticket ownership continuity
- manual override with persisted state
- effective assignee surfaced in ticket detail and list views

## Important Architectural Decisions

### 1. Autotask boundary

- Autotask is the intended source of truth for real ticket records.
- This app should not become a second permanent ticketing system.
- The AI service stores operational AI/routing state only.

### 2. CPU-first design

- `spaCy` was removed from the live path.
- current model strategy is lightweight and CPU-friendly
- no large model dependency is currently required

### 3. Category vocabulary

- categories are config-driven, not hard-coded
- category keys are also currently reused as profile specialism keys
- this was a deliberate shortcut to get real specialism-backed routing working quickly and clearly

### 4. Recommendation vs assignment

- current system is recommendation-first
- it does not write assignment changes back to an external system
- manual override changes the effective assignee inside hosted AI state only

## Backend Files That Matter Most

### AI classification

- `backend/app/services/ai/config.py`
- `backend/app/services/ai/text_processor.py`
- `backend/app/services/ai/categorizer.py`
- `backend/app/services/ai/priority_calculator.py`
- `backend/app/services/ai/processor.py`
- `backend/data/ticket_categories.json`

### AI operational state

- `backend/app/models/ai_state.py`
- `backend/app/repositories/ai_state_repository.py`
- `backend/app/services/ai_state_service.py`
- `backend/app/routers/ai_state.py`
- `backend/app/schemas/ai_state.py`

### Assignment/recommendation

- `backend/app/services/ai_assignment_service.py`

### Profiles/specialisms

- `backend/app/models/profile.py`
- `backend/app/repositories/profile_repository.py`
- `backend/app/services/profile_service.py`
- `backend/app/routers/profiles.py`
- `backend/app/schemas/profile.py`

### App entry

- `backend/app/main.py`

## Frontend Files That Matter Most

### AI-backed ticket views

- `frontend/src/shared/api/aiTickets.ts`
- `frontend/src/shared/types.ts`
- `frontend/src/components/TicketListContainer.ts`
- `frontend/src/pages/ActiveTickets.ts`
- `frontend/src/pages/Dashboard.ts`
- `frontend/src/pages/TicketDetail.ts`
- `frontend/src/App.ts`

### Specialisms and assignment

- `frontend/src/shared/api/profileSpecialisms.ts`
- `frontend/src/shared/api/aiAssignments.ts`
- `frontend/src/pages/Settings.ts`

## Database / Migration State

These migrations exist and matter:

- `9f1b0c6d4a21_add_ticket_ai_state_table.py`
- `e3a4d9f2a1b7_add_profile_mapping_to_ticket_ai_state.py`
- `6a0dd9cb6ed1_add_created_to_ticket_ai_state.py`
- `c2d9f8a4b7e1_add_manual_override_to_ticket_ai_state.py`

Before testing after fresh pulls or schema changes, run:

```bash
cd backend
.venv/bin/alembic upgrade head
```

## Current Backend Endpoints

### Existing AI-state endpoints

- `GET /api/v1/ai/categories`
- `POST /api/v1/ai/ticket-states/refresh`
- `GET /api/v1/ai/ticket-states`
- `GET /api/v1/ai/ticket-states/my-primary`
- `GET /api/v1/ai/ticket-states/my-secondary`
- `GET /api/v1/ai/ticket-states/my-assigned`
- `GET /api/v1/ai/ticket-states/team`
- `GET /api/v1/ai/ticket-states/{autotask_ticket_id}`

### Recommendation and override

- `GET /api/v1/ai/ticket-states/{autotask_ticket_id}/assignment-recommendation`
- `PUT /api/v1/ai/ticket-states/{autotask_ticket_id}/assignment-override`
- `DELETE /api/v1/ai/ticket-states/{autotask_ticket_id}/assignment-override`

### Authenticated profile specialisms

- `GET /api/v1/auth/profile/specialisms`
- `PUT /api/v1/auth/profile/specialisms`

## Current Recommendation Logic

Implemented in `backend/app/services/ai_assignment_service.py`.

Current scoring signals:

- category-specialism match
- same-company continuity:
  - other open tickets for same company where candidate is primary
  - other open tickets for same company where candidate is secondary
- current ownership continuity:
  - already primary on this ticket
  - already secondary on this ticket
- workload balancing:
  - penalty if weighted open load is above team average
  - bonus if weighted open load is below team average

Current workload approximation:

- primary open ticket adds more load than secondary
- high/critical tickets add extra load

Current output:

- recommended assignee
- effective assignee
- candidate list
- reasons
- workload counts
- manual override metadata

## Current Frontend Behavior

### Active tickets

- `Active Tickets` is the main queue page
- view tabs:
  - `My Assigned`
  - `My Primary`
  - `My Secondary`
  - `Team Queue`
- URL hash reflects selected view:
  - `#/active-tickets`
  - `#/active-tickets/my-primary`
  - `#/active-tickets/my-secondary`
  - `#/active-tickets/team`

### Ticket cards

- show category grouping
- show effective assignee
- show manual override badge when present

### Ticket detail

- shows AI recommendation panel
- shows candidate reasoning
- shows workload values
- allows setting manual override
- allows clearing manual override

### Settings

- loads current user's specialisms from backend
- saves category-aligned specialisms to backend

## Testing Notes

### Common required sequence

```bash
cd backend
.venv/bin/alembic upgrade head
```

Then:

- restart backend
- if AI-state is stale, trigger refresh

### Refresh note

Swagger may return `401` even if frontend login works because Swagger and frontend may not share auth state cleanly.

If needed, trigger refresh from browser console while logged into the frontend:

```js
fetch("http://localhost:8000/api/v1/ai/ticket-states/refresh", {
  method: "POST",
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ include_closed: false, limit: 100 })
}).then(async (r) => {
  console.log(r.status, await r.text());
});
```

### Build/verification commands used successfully

```bash
backend/.venv/bin/python -m compileall backend/app
cd frontend && npm run build
```

## Known Constraints / Truths

- no external Autotask write-back
- no scheduled refresh/sync yet
- no category-management API
- no full historical audit log beyond current manual override fields
- no reporting/evaluation layer yet
- no fairness analytics beyond simple workload balancing
- no availability/shift/away-status signal
- no explicit profile specialism management UI beyond category-aligned tags

## Remaining Work To Reach “Complete” AI Service

### Must-have next decisions / implementation

1. Decide operating mode
- Should the service remain recommendation-first?
- Or should some tickets become auto-assigned?

2. Add external write-back hooks
- Persisting effective assignee internally is not enough for final production workflow.
- Need a place to push confirmed assignment to real source of truth later.

3. Add refresh automation
- Current refresh is manual.
- Need scheduled job, webhook-style trigger, or controlled auto-refresh.

4. Improve audit depth
- current override fields are useful but shallow
- full history should track recommendation, override, reassignment, timestamp, actor

5. Improve queue operations UX
- filters for override state
- filters for effective assignee
- maybe sort by overridden/recommended/current owner

### Strongly recommended next work

6. Category-management API/UI
- categories currently require JSON edit + restart

7. Evaluation/reporting
- recommendation quality checks
- classification regression checks
- fairness/load-distribution reporting

8. Availability-aware scoring
- analyst away/offline/deactivated status beyond simple profile active status

9. Better admin controls
- team lead override visibility
- assignment review views
- audit export

## Suggested Immediate Next Task

Best next task if continuing development:

- add queue filtering/sorting for:
  - effective assignee
  - manual override state
  - recommended vs overridden tickets

Alternative next task if moving toward production:

- design external write-back boundary and final assignment-confirmation workflow

## Common Pitfalls

- forgetting to run migrations after schema changes
- forgetting to refresh AI ticket state after creating/updating profiles
- assuming Swagger auth equals frontend auth
- assuming manual override changes external source of truth
- assuming recommendation already means production-complete workflow automation

## If Resuming Tomorrow

Recommended first actions:

1. Read this file.
2. Read `docs/services/ai-service/overview.md`.
3. Run `git status`.
4. Run migrations if needed.
5. Start backend/frontend.
6. Test a ticket detail recommendation and one override action.
7. Continue from “Suggested Immediate Next Task” unless user redirects.

# AI Service Troubleshooting

## Purpose

This guide helps developers diagnose common AI-service problems in the current implementation.

## Quick Checks

When the AI service behaves unexpectedly, check these first:

1. Does `backend/data/ticket_categories.json` exist and validate?
2. Is the backend able to load the sentence-transformer model?
3. Are you testing batch mode or sequential mode?
4. Does `/api/categories` return the category list you expect?
5. Are the ticket endpoints returning AI metadata with `category`, `confidence`, `priority`, and `priority_score`?
6. If using AI-state endpoints, has the database migration been applied?
7. If using `/my-primary` or `/my-secondary`, have you refreshed AI ticket state after creating matching local profiles?
8. If Swagger shows `401 Unauthorized`, are you authenticated in Swagger itself or only in the frontend UI?
9. If assignment recommendation is empty, does any active profile actually have a stored specialism matching the ticket category?
10. If override actions fail, has the latest AI-state migration been applied?

## Symptom: categories look wrong

Likely causes:

- the configured categories do not match the real SecOps workflow
- keyword lists are too weak or too broad
- ticket text does not contain the expected language

What to check:

- [ticket_categories.json](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/data/ticket_categories.json)
- `/api/categories`
- backend logs from `config.py` and `categorizer.py`

## Symptom: category changes do not appear in the API

Likely cause:

- the backend has not been restarted after changing the JSON config

What to check:

- restart the backend process
- call `/api/categories` again
- call `/api/v1/ai/categories` as well if you are testing the AI-specific router

## Symptom: semantic classification is unavailable

Likely causes:

- the embedding model is not provisioned in the environment
- local-only model loading is enabled and the model is not cached locally

What to check:

- backend startup logs from `config.py`
- `AI_EMBEDDING_MODEL_NAME`
- `AI_EMBEDDING_MODEL_LOCAL_ONLY`

Expected behavior:

- the service should still start
- keyword-only fallback should still classify tickets

## Symptom: semantic categorization is slow

Likely causes:

- model encoding is expensive
- cache hit rate is low
- batch mode is not being used

What to check:

- whether `/api/tickets` is being called with default `batch=true`
- cache stats from `/api/cache/stats`
- AI performance logs if enabled

Code locations:

- `categorizer.py`
- `embedding_cache.py`
- `main.py`

## Symptom: batch and sequential results differ slightly

Likely cause:

- the two paths share the same category logic, but batch mode uses batched semantic scoring and sequential mode goes through `categorise_ticket(...)`

What to check:

- `GET /api/tickets`
- `GET /api/tickets?batch=false`

Important note:

- major differences are a bug
- small score differences may happen because the two paths are assembled differently

## Symptom: priority labels feel surprising

Likely cause:

- priority scoring is heuristic and depends on configured category weights plus urgency text

What to check:

- category `priority_weight` values in `ticket_categories.json`
- urgency keywords in the ticket text
- semantic confidence value
- text length adjustment

Code location:

- `backend/app/services/ai/priority_calculator.py`

## Symptom: cache seems ineffective

Likely causes:

- requests are using different text each time
- cache TTL expired
- cache was cleared
- the process restarted

What to check:

- `/api/cache/stats`
- whether texts are truly repeated

## Symptom: AI ticket-state refresh fails

Likely causes:

- database migration has not been applied
- the backend database is unavailable
- authentication is missing for `/api/v1/ai/...` endpoints

What to check:

- `alembic upgrade head`
- backend database connectivity
- `POST /api/v1/ai/ticket-states/refresh`
- backend logs from `ai_state_service.py` or the router

Expected behavior:

- refresh returns a non-zero `refreshed_count`
- `GET /api/v1/ai/ticket-states` then returns persisted rows

Important troubleshooting endpoint:

- `POST /api/v1/ai/ticket-states/refresh`

What it does:

- pulls the current provider ticket set
- reruns AI categorization
- updates persisted hosted AI ticket state
- attempts to map ticket resources to matching local profiles

Why it matters:

- if AI-state endpoints are stale, use refresh
- if you created new test SecOps profiles, use refresh
- if `/my-primary` and `/my-secondary` are empty unexpectedly, use refresh

Recommended local-dev order:

1. run `alembic upgrade head`
2. restart the backend
3. trigger refresh
4. test the frontend views again

## Symptom: `column ticket_ai_state.created does not exist`

Likely cause:

- the local database schema is behind the current code

What to check:

- run `cd backend && .venv/bin/alembic upgrade head`
- restart the backend
- rerun `POST /api/v1/ai/ticket-states/refresh`

Why this happens:

- the AI-state table now stores the original ticket `created` timestamp for frontend use

## Symptom: override buttons fail or `manual_override_*` columns do not exist

Likely cause:

- the database is missing the latest AI-state override migration

What to check:

- run `cd backend && .venv/bin/alembic upgrade head`
- restart the backend
- retry the override action

## Symptom: `401 Unauthorized` when calling AI-state endpoints in Swagger

Likely cause:

- Swagger is not sharing the frontend login session from `localhost:5173`

Practical workaround:

Use the authenticated browser console from the signed-in frontend:

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

## Symptom: `/my-primary` or `/my-secondary` is empty even though `/team` works

Likely causes:

- the logged-in profile does not match any `primary_resource` or `secondary_resource` values
- matching local profiles were created after the last refresh
- profile display names do not exactly match the resource names in the ticket data

What to check:

- `POST /api/v1/ai/ticket-states/refresh`
- whether local profile display names match the ticket resource names
- `GET /api/v1/ai/ticket-states/team`
- `GET /api/v1/ai/ticket-states/my-primary`
- `GET /api/v1/ai/ticket-states/my-secondary`

## Symptom: Settings still looks like placeholder data

Likely causes:

- the frontend is not running the latest build
- the authenticated specialism endpoints are failing

What to check:

- `GET /api/v1/auth/profile/specialisms`
- `PUT /api/v1/auth/profile/specialisms`
- frontend network requests from the `Settings` page
- whether category options from `GET /api/v1/ai/categories` are loading

Expected behavior:

- the `Settings` page should load category-aligned specialisations from the backend
- adding or removing a specialisation should persist immediately

## Symptom: assignment recommendation shows no suggested assignee

Likely causes:

- no active profile has a specialism matching the ticket's AI category
- the user saved specialisms before the latest frontend build and needs to reload
- the ticket category is valid, but no one has claimed that category as a strength yet

What to check:

- `GET /api/v1/auth/profile/specialisms` for one or more test users
- `GET /api/v1/ai/ticket-states/{autotask_ticket_id}/assignment-recommendation`
- the ticket category shown in ticket detail
- whether at least one active test user has saved that same category key as a specialism

## Symptom: recommendation ignores company continuity or workload

Likely causes:

- the AI-state snapshot is stale
- there are too few open tickets for that company to create a continuity signal
- the team workload is currently too even to create a visible penalty/bonus

What to check:

- refresh AI ticket state again
- inspect recommendation reasons for same-company and workload lines
- confirm the company appears on multiple open tickets in the team queue

## Symptom: the wrong active-ticket tab looks selected or the URL hash does not change

Likely cause:

- the frontend is not running the latest build after the AI-state view-switcher update

What to check:

- rebuild or restart the frontend
- verify these hashes update as you switch views:
  - `#/active-tickets`
  - `#/active-tickets/my-primary`
  - `#/active-tickets/my-secondary`
  - `#/active-tickets/team`

## Known Structural Gaps

Verified from the current code:

 - no category-management API yet
 - no model version surfaced in AI responses
 - no durable metrics store
 - persisted AI ticket state, recommendation logic, continuity scoring, workload balancing, and manual override exist, but external write-back and full workflow automation do not yet

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

## Known Structural Gaps

Verified from the current code:

- no persisted AI state store
- no assignment or workload-balancing logic yet
- no category-management API yet
- no model version surfaced in AI responses
- no durable metrics store

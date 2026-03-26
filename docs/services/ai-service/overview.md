# AI Service Overview

## Why This Exists

The AI service helps the backend turn raw SecOps ticket text into operational metadata the frontend can use immediately.

Today that means:

- assigning a category
- producing a confidence-like score
- calculating a priority score
- returning a priority label
- exposing the configured category list through the API
- persisting hosted AI ticket state for refreshable ticket snapshots

In plain English:

- the ticket provider returns raw tickets
- the AI service reads the ticket text
- the AI service decides which configured category fits best
- the AI service scores how urgent the ticket appears

## Human-Friendly Summary

This is not a generative AI system and it is not yet the future workflow manager you want.

It is currently a lightweight ticket-classification pipeline made of:

1. text extraction
2. lightweight text normalization
3. keyword matching
4. semantic similarity, when the embedding model is available
5. heuristic priority scoring

That makes it a CPU-friendly AI-assisted classifier rather than an autonomous decision engine.

## What The AI Service Actually Does Today

Verified from the current code:

- loads category definitions from `backend/data/ticket_categories.json`
- exposes those categories through `GET /api/categories`
- exposes AI-specific endpoints under `GET/POST /api/v1/ai/...`
- extracts relevant fields from ticket data before classification
- uses regex-based normalization instead of spaCy
- uses keyword matching for interpretable category detection
- uses sentence embeddings with `all-MiniLM-L6-v2` when available
- falls back to keyword-only classification if the embedding model is unavailable
- supports both single-ticket and batch categorization paths
- caches embeddings in memory for repeated batch work
- calculates priority scores from configured weights plus simple heuristics
- can refresh and persist AI ticket state into the hosted backend database

## What "AI" Means Here

There are two main decision techniques in the current implementation.

### 1. Config-driven keyword classification

Each category has:

- a stable key
- a UI label
- a description
- a keyword list
- a priority weight

Those definitions live in [ticket_categories.json](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/data/ticket_categories.json).

This is the most important current change because categories are no longer hard-coded inside Python source.

### 2. Semantic similarity with embeddings

When the embedding model is available, the service:

- encodes the ticket text
- compares it with precomputed category embeddings
- uses cosine similarity as a semantic signal

If the model is not provisioned, the service still starts and falls back to keyword-only behavior.

## High-Level Pipeline

```mermaid
flowchart TD
  Raw[Raw ticket data] --> Extract[Extract relevant text]
  Extract --> Normalize[Normalize text]
  Normalize --> Keyword[Keyword category scoring]
  Extract --> Semantic[Sentence embedding comparison]
  Keyword --> Decision[Hybrid category decision]
  Semantic --> Decision
  Decision --> Priority[Priority score calculation]
  Priority --> Output[AI metadata for ticket]
```

## Source Of Truth

This documentation is based on the current implementation in:

- `backend/app/services/ai/__init__.py`
- `backend/app/services/ai/config.py`
- `backend/app/services/ai/text_processor.py`
- `backend/app/services/ai/categorizer.py`
- `backend/app/services/ai/priority_calculator.py`
- `backend/app/services/ai/embedding_cache.py`
- `backend/app/services/ai/processor.py`
- `backend/app/services/ai_state_service.py`
- `backend/app/repositories/ai_state_repository.py`
- `backend/app/models/ai_state.py`
- `backend/app/routers/ai_state.py`
- `backend/app/main.py`
- `backend/data/ticket_categories.json`

## Where The AI Service Is Used

The current backend integration points are:

- `GET /api/categories`
- `GET /api/tickets`
- `GET /api/tickets/{autotask_ticket_id}`
- `GET /api/tickets/stream/categorize`
- `GET /api/v1/ai/categories`
- `POST /api/v1/ai/ticket-states/refresh`
- `GET /api/v1/ai/ticket-states`
- `GET /api/v1/ai/ticket-states/{autotask_ticket_id}`

## Important Current Limitations

Verified from the current implementation:

- this service does not yet assign tickets to SecOps users
- it does not yet use profile specialisms for routing
- it does not yet enforce company continuity ownership
- it does not yet balance workloads across analysts
- category quality depends on the configured category definitions and ticket text quality
- embedding cache and metrics are in-memory only
- persisted AI ticket state exists, but routing/assignment state does not yet
- there is still no category-management API yet, only category reading plus ticket-state refresh/list/get endpoints

## Recommended Reading Order

1. [overview.md](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/docs/services/ai-service/overview.md)
2. [architecture.md](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/docs/services/ai-service/architecture.md)
3. [flows.md](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/docs/services/ai-service/flows.md)
4. [dependencies.md](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/docs/services/ai-service/dependencies.md)
5. [troubleshooting.md](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/docs/services/ai-service/troubleshooting.md)
6. [future-direction.md](/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/docs/services/ai-service/future-direction.md)

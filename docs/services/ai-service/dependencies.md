# AI Service Dependencies

## Purpose

This document explains what the current AI service depends on and why those dependencies matter.

## Internal Code Dependencies

### `config.py`

Depends on:

- `sentence_transformers.SentenceTransformer`
- `torch`
- `logging_config.py`
- `backend/data/ticket_categories.json`

Why it matters:

- this module loads the category registry and semantic model used by the rest of the service

### `text_processor.py`

Depends on:

- constants from `config.py`
- metrics/logging objects

Why it matters:

- it provides the normalization and ticket-text extraction used by classification

### `categorizer.py`

Depends on:

- category definitions, embeddings, and model state from `config.py`
- `text_processor.py`
- `embedding_cache.py`
- metrics/logging objects

Why it matters:

- this is where the category decision logic lives

### `priority_calculator.py`

Depends on:

- category and urgency constants from `config.py`

Why it matters:

- priority scores depend on configured category weights

### `processor.py`

Depends on:

- text extraction
- categorization
- priority calculation

Why it matters:

- this is the live orchestrator used by the request-time API path

### `ai_state_service.py`

Depends on:

- the current ticket provider
- `categorise_ticket(...)`
- `ai_state_repository.py`
- AI-state schemas

Why it matters:

- this is the bridge between provider tickets and persisted hosted AI ticket state

### `ai_state_repository.py`

Depends on:

- `TicketAIState` model
- async SQLAlchemy session

Why it matters:

- it stores and retrieves the hosted AI snapshots used by new AI endpoints

### `embedding_cache.py`

Depends on:

- in-memory process state

Why it matters:

- repeated batch requests can be faster when embeddings are reused

## Third-Party Dependencies

### sentence-transformers

Declared in:

- `backend/requirements.txt`

Used for:

- encoding category descriptions and ticket text into embeddings

Important runtime detail:

- the current default model is `all-MiniLM-L6-v2`
- the service can fall back to keyword-only classification if the model is unavailable

### PyTorch

Used indirectly by:

- sentence-transformers
- tensor operations in batch categorization

Why it matters:

- semantic similarity depends on it

### NumPy

Declared in:

- `backend/requirements.txt`

Why it matters:

- it remains available in the backend environment, although it is not a major part of the current live AI path

## Runtime Dependencies

### Category configuration file

Relevant file:

- `backend/data/ticket_categories.json`

Why it matters:

- it defines category keys, labels, descriptions, keywords, and priority weights
- `/api/categories` reflects this file
- the classifier depends on this file being valid

### Embedding model availability

Relevant configuration:

- `AI_EMBEDDING_MODEL_NAME`
- `AI_EMBEDDING_MODEL_LOCAL_ONLY`

Why it matters:

- the semantic path only works if the model is provisioned in the deployment environment
- if not, the service uses keyword fallback behavior

### In-memory cache

Relevant module:

- `embedding_cache.py`

Why it matters:

- batch performance depends partly on cache hit rate

### Hosted database

Relevant pieces:

- `ticket_ai_state` table
- Alembic migration for AI state

Why it matters:

- AI ticket snapshots now persist in the hosted backend instead of existing only in request memory

### Local profile data

Relevant pieces:

- `profile`
- `profile_display`

Why it matters:

- resource-to-profile mapping depends on local profiles existing with matching display names
- endpoints like `/api/v1/ai/ticket-states/my-primary` only become useful once refresh has mapped those resources

## Dependency Risks

Visible from the current code:

- if `ticket_categories.json` is malformed, startup should fail fast
- if the embedding model is unavailable, semantic classification is disabled until the model is provisioned
- import-time model loading still affects startup time
- cache and metrics are process-local, so they do not survive restarts or scale across instances
- AI-state refresh depends on the hosted database being migrated and available

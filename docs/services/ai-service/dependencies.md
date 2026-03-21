# AI Service Dependencies

## Purpose

This document explains what the AI service depends on and why those dependencies matter.

## Internal Code Dependencies

### `config.py`

Depends on:

- `sentence_transformers.SentenceTransformer`
- `torch`
- `logging_config.py`
- optional `category_generator.py`

Why it matters:

- this file loads the model and category configuration that many other modules rely on

### `text_processor.py`

Depends on:

- `spacy`
- constants from `config.py`
- metrics/logging objects

Why it matters:

- without spaCy loading successfully, preprocessing quality drops sharply and some downstream logic becomes weaker

### `categorizer.py`

Depends on:

- category keywords and embeddings from `config.py`
- the sentence-transformer model from `config.py`
- `text_processor.py`
- `embedding_cache.py`
- metrics/logging objects

Why it matters:

- this module is where the main classification logic lives

### `priority_calculator.py`

Depends on:

- category and urgency constants from `config.py`

Why it matters:

- the priority system is only as good as its configured weights and heuristics

### `description_generator.py`

Depends on:

- metrics/logging objects
- ticket input fields

Why it matters:

- it relies more on rule/template logic than on model inference in the current implementation

### `processor.py`

Depends on:

- text extraction
- categorization
- priority calculation
- company detection
- description generation
- storage

Why it matters:

- this is the orchestrator that ties the AI service together

### `category_generator.py`

Depends on:

- the sentence-transformer model
- preprocessing
- `numpy`
- `sklearn.cluster.KMeans`
- `sklearn.metrics.silhouette_score`

Why it matters:

- this path is what makes startup-time dynamic category generation possible

### `storage.py`

Depends on:

- file paths from `config.py`
- filesystem read/write access

Why it matters:

- if those paths are wrong for the current environment, file-based processing workflows will fail

## Third-Party Dependencies

### spaCy

Declared in:

- `backend/requirements.txt`

Used for:

- tokenization
- lemmatization
- filtering stopwords and punctuation

Developer-friendly explanation:

- spaCy is the main text-cleaning and linguistic preprocessing library in this codebase

Important runtime detail:

- `text_processor.py` expects the `en_core_web_sm` model to be installed

### sentence-transformers

Declared in:

- `backend/requirements.txt`

Used for:

- encoding category descriptions and ticket text into embeddings

Developer-friendly explanation:

- this library provides the semantic-similarity part of the service

### PyTorch

Used indirectly by:

- sentence-transformers
- embedding tensors
- batch operations in categorization

Why it matters:

- embeddings and tensor operations rely on it

### NumPy

Used by:

- `category_generator.py`

Why it matters:

- clustering inputs are handled as arrays there

### scikit-learn

Declared in:

- `backend/requirements.txt`

Used by:

- `category_generator.py`

Why it matters:

- KMeans and silhouette scoring come from scikit-learn

## Runtime Dependencies

### Ticket data files

Relevant files or expected inputs:

- `backend/data/tickets.json`
- `backend/data/generated_categories.json`

Why they matter:

- `tickets.json` can be used to auto-generate categories
- `generated_categories.json` can override the default category set

### In-memory cache

Relevant module:

- `embedding_cache.py`

Why it matters:

- batch performance depends partly on cache hit rate

### Filesystem paths in config

Relevant constants:

- `TICKETS_BASE_PATH`
- `INPUT_TICKETS_PATH`

Important note:

- these are currently hard-coded Windows-style paths
- that may not line up with the current repository location or OS environment

## Dependency Risks

Visible from the current code:

- if `en_core_web_sm` is missing, preprocessing falls back badly and logs warnings/errors
- if the sentence-transformer model cannot load, major AI functionality will fail
- if generated categories are malformed, the system falls back to defaults
- if file paths are invalid, storage workflows will fail even if API-time enrichment still works
- import-time model loading can make startup heavier and failures more immediate

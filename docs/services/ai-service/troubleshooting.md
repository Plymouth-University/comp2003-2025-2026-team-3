# AI Service Troubleshooting

## Purpose

This guide helps developers diagnose common AI-service problems in the current implementation.

## Quick Checks

When the AI service behaves unexpectedly, check these first:

1. Is the backend able to start the sentence-transformer model?
2. Is the spaCy model `en_core_web_sm` installed?
3. Are categories being loaded from `generated_categories.json` or default fallbacks?
4. Are you using batch mode or sequential mode?
5. Are file-based storage paths valid for the current machine?

## Symptom: categories look wrong or too generic

Likely causes:

- generated categories were loaded and may not be high quality
- the system fell back to default categories
- preprocessing removed too much useful signal

What to check:

- backend logs from `config.py`
- whether `backend/data/generated_categories.json` exists
- whether startup logged "Using default fallback categories"

## Symptom: preprocessing returns poor tokens or empty results

Likely cause:

- spaCy model not loaded successfully

What to check:

- backend logs for warnings like `spaCy model not found`
- whether `python -m spacy download en_core_web_sm` has been run in the active environment

Code location:

- `backend/app/services/ai/text_processor.py`

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

## Symptom: one ticket path works, but file-processing path fails

Likely cause:

- the request-time API path and the file-storage path are not the same workflow

What to check:

- whether the failure is coming from `processor.py` and `storage.py`
- whether `TICKETS_BASE_PATH` and `INPUT_TICKETS_PATH` are valid on this machine

Important note:

- hard-coded Windows paths in `config.py` are a likely source of failure outside that environment

## Symptom: generated descriptions do not feel very "AI"

Likely cause:

- the description generator is mostly template/remediation based in the current implementation

What to check:

- `backend/app/services/ai/description_generator.py`

Explanation:

- this is expected from the current code
- the name sounds more advanced than the implementation actually is

## Symptom: category generation at startup takes too long or fails

Likely causes:

- ticket dataset is large
- clustering work is expensive
- not enough tickets exist for meaningful clustering
- dependencies or file inputs are missing

What to check:

- logs from `category_generator.py`
- whether `tickets.json` exists
- whether there are at least about 10 tickets

## Symptom: priority labels feel surprising

Likely cause:

- priority scoring is heuristic, not learned from labeled training data

What to check:

- category weight
- urgency keywords in the text
- semantic confidence value
- text length adjustment

Code location:

- `backend/app/services/ai/priority_calculator.py`

## Symptom: cache seems ineffective

Likely causes:

- requests are using different text each time
- cache TTL expired
- cache was cleared

What to check:

- `/api/cache/stats`
- whether texts are truly repeated
- whether the process restarted

## Symptom: batch and sequential results differ slightly

Likely cause:

- the request-time implementation uses slightly different enrichment paths for batch and sequential modes

What to check:

- batch mode in `/api/tickets` returns `ai` objects assembled from batch categorization and batch priority scoring
- sequential mode relies more directly on `categorise_ticket(...)`

Why this matters:

- performance and output shape may not be perfectly identical between the two paths

## Known Structural Gaps

Verified from the current code:

- no persisted metrics store
- no experiment tracking
- no model versioning surfaced in API responses
- hard-coded storage paths
- a mixture of prototype-style file processing and live API inference paths

# AI Service Architecture

## Architecture In One Sentence

The AI service is a configurable ticket-classification pipeline with a hosted AI-state layer that combines category configuration, lightweight text normalization, keyword matching, optional semantic similarity, heuristic priority scoring, persisted ticket snapshots, and simple profile-specialism assignment recommendations.

## Why It Is Structured This Way

The current design is intentionally lighter than the earlier prototype.

That matters because the target deployment is CPU-based and should:

- start reliably on hosted infrastructure
- avoid unnecessary runtime dependencies
- keep category behavior configurable
- separate real request-time logic from prototype-only experiments

## Module Map

```mermaid
flowchart TD
  Config[config.py] --> Text[text_processor.py]
  Config --> Categorizer[categorizer.py]
  Config --> Priority[priority_calculator.py]

  Text --> Categorizer
  Text --> Processor[processor.py]
  Categorizer --> Processor
  Priority --> Processor
  Cache[embedding_cache.py] --> Categorizer
  AIStateService[ai_state_service.py] --> AIRepo[ai_state_repository.py]
  AIRepo --> AIStateTable[(ticket_ai_state)]
  Assign[AIAssignmentService] --> AIRepo
  Assign --> ProfileRepo[profile_repository.py]

  Processor --> API[backend/app/main.py]
  API --> AIRouter[ai_state.py router]
  API --> ProfileRouter[profiles.py router]
  CategoryFile[ticket_categories.json] --> Config
```

## Beginner-Friendly Explanation Of Each Module

### `config.py`

Purpose:

- load category definitions
- load the embedding model
- build shared category embeddings
- expose shared constants

What it does now:

- reads `backend/data/ticket_categories.json`
- validates category definitions
- loads `all-MiniLM-L6-v2` when available
- falls back safely if the semantic model cannot be loaded

Why it matters:

- this is the central source of AI-service behavior

### `text_processor.py`

Purpose:

- normalize raw ticket text into a simpler classification-friendly form

What it does now:

- lowercases text
- tokenizes with regex
- removes simple stop words
- extracts the relevant fields from ticket dictionaries

Important current detail:

- the service no longer depends on spaCy preprocessing

### `categorizer.py`

Purpose:

- decide which configured category best matches the ticket

How it works:

- keyword scoring checks configured keywords first
- semantic similarity compares ticket text to category descriptions when the model is available
- hybrid logic chooses between those signals

Important current detail:

- batch mode and single-ticket mode both support keyword-only fallback

### `priority_calculator.py`

Purpose:

- convert the chosen category and urgency signals into a 0-100 priority score

How it works:

- uses category weights from the category config
- checks urgency words in the text
- uses semantic confidence as a small adjustment
- applies a small text-length adjustment

### `embedding_cache.py`

Purpose:

- avoid recomputing embeddings for repeated texts

How it works:

- stores embeddings in memory
- supports TTL and reuse across requests in the same process

### `processor.py`

Purpose:

- provide the live AI response shape used by ticket endpoints

What it coordinates:

- text extraction
- category prediction
- priority calculation
- response shaping

### `ai_state_service.py`

Purpose:

- refresh and read persisted AI ticket state for the hosted backend

What it coordinates:

- pulling tickets from the current provider
- classifying them through the existing AI path
- storing the resulting AI metadata in the database
- mapping ticket resources onto local profiles when display names match
- returning refresh/list/get responses for AI endpoints

### `ai_assignment_service.py`

Purpose:

- recommend candidate assignees from persisted AI ticket state and stored profile specialisms

What it coordinates:

- loading one persisted AI ticket state row
- loading active profiles with assigned specialisms
- matching ticket category keys to specialism keys
- returning an explainable candidate list and top recommendation

### `ai_state_repository.py`

Purpose:

- persist tenant-scoped AI ticket state

What it stores:

- ticket snapshot fields needed by the AI/routing layer
- original ticket `created` timestamp used by frontend dashboard and active-ticket views
- category and confidence
- priority label and score
- classification method
- primary and secondary profile mappings
- refresh timestamps
- closed/open state

## Runtime Architecture

### Request-time classification path

```mermaid
flowchart LR
  Ticket[Ticket fields] --> Extract[extract_ticket_text]
  Extract --> Normalize[normalize_text]
  Normalize --> Keyword[Keyword scoring]
  Extract --> Embed[Semantic embedding]
  Embed --> Compare[Compare with category embeddings]
  Keyword --> Hybrid[Hybrid decision]
  Compare --> Hybrid
  Hybrid --> Score[Priority score]
  Score --> Final[AI response]
```

### Persisted AI-state path

```mermaid
flowchart TD
  Provider[Ticket provider] --> Refresh[POST /api/v1/ai/ticket-states/refresh]
  Refresh --> AIService[AIStateService]
  AIService --> Processor[process_ticket]
  AIService --> ProfileLookup[Resolve resource names to profiles]
  Processor --> Persist[(ticket_ai_state)]
  ProfileLookup --> Persist
  Persist --> Read[GET /api/v1/ai/ticket-states]
  Persist --> MyAssigned[GET /api/v1/ai/ticket-states/my-assigned]
  Persist --> MyPrimary[GET /api/v1/ai/ticket-states/my-primary]
  Persist --> MySecondary[GET /api/v1/ai/ticket-states/my-secondary]
  Persist --> Team[GET /api/v1/ai/ticket-states/team]
  Persist --> One[GET /api/v1/ai/ticket-states/{id}]
  Persist --> Recommend[GET /assignment-recommendation]
  MyAssigned --> Frontend[Active Tickets UI]
  MyPrimary --> Frontend
  MySecondary --> Frontend
  Team --> Frontend
  Recommend --> TicketDetail[Ticket Detail UI]
```

## Important Design Choices

### Configurable categories instead of hard-coded categories

Why:

- SecOps should be able to change the classification scheme without rewriting Python modules
- category labels, keywords, and priority weights belong to data/config, not code

### Optional semantic model

Why:

- hosted environments should not hard-fail if the embedding model has not been provisioned yet
- keyword-only fallback is better than total service failure

### Lightweight normalization

Why:

- spaCy added dependency and startup cost without being central to the desired product direction
- the current classifier only needs simple normalization for this phase

### Category keys reused as specialism keys

Why:

- it gives the team one stable vocabulary for the first assignment slice
- the Settings page can be wired to real backend data without inventing a second taxonomy first
- it keeps the recommendation logic explainable and low-risk

## Architecture Strengths

Verified from the current code:

- category behavior is now externally configurable
- request-time logic is cleaner and more honest
- deleted prototype-only modules are no longer in the live path
- single-ticket and batch modes both still work
- model availability failures are handled more safely
- AI ticket state can now be persisted centrally in the hosted backend
- AI-specific endpoints now exist for category reading and ticket-state refresh/list/get
- AI ticket state can now support profile-based primary/secondary ticket views
- the frontend now consumes AI-state endpoints for `My Assigned`, `My Primary`, `My Secondary`, and `Team Queue`
- the Settings page now persists authenticated-user specialisms into the profile service database
- the ticket detail page can now show a specialism-aware assignee recommendation

## Architecture Weaknesses

Also visible in the current code:

- the current assignment recommendation only considers category-specialism matching
- category management still requires editing a JSON file rather than using a dedicated API
- cache and metrics are still process-local rather than durable
- persisted state now includes profile-resource mapping, but not company continuity or workload-based routing decisions yet
- AI-state refresh is still a manual sync step during development and testing

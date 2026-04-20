# Logging System Troubleshooting

## Purpose

This guide helps developers understand what to check when the current logging behavior is confusing, missing, or inconsistent.

## Quick Checks

When logs do not look right, check these first:

1. Which logging path are you expecting: backend console, AI file logs, or browser console?
2. Are you looking at a module that actually uses `backend/app/services/ai/logging_config.py`?
3. Is the backend process able to create and write to `backend/logs/ai_services/`?
4. Are you trying to correlate frontend and backend activity without a shared request ID?
5. Did the backend process restart and clear in-memory AI metrics?

## Symptom: I can see backend logs in the terminal but not in AI log files

Likely cause:

- not all backend modules use the AI logging configuration

What to check:

- whether the module imports `backend/app/services/ai/logging_config.py`
- whether the message comes from `backend/app/main.py`, `database.py`, or `fake_autotask.py`, which primarily use normal Python logging

## Symptom: AI log files are missing

Likely causes:

- the AI logging module has not been imported yet
- file handler creation failed
- the backend process cannot write to the target directory

What to check:

- confirm `backend/app/services/ai/logging_config.py` is being imported through AI modules
- inspect the backend terminal for warnings like `Could not create ... log file handler`
- check whether `backend/logs/ai_services/` exists

## Symptom: Frontend logs disappear

Likely cause:

- frontend logs live only in the browser console

What to check:

- open browser devtools
- confirm the console has not been cleared
- remember that refreshing the page does not preserve logs the way a backend file would

## Symptom: I cannot match frontend events to backend requests reliably

Likely cause:

- there is no shared correlation ID or trace ID in the current implementation

What to check:

- compare timestamps manually
- compare the order of events rather than expecting exact trace continuity

Longer-term fix:

- introduce request IDs and include them in both frontend request metadata and backend logs

## Symptom: Performance metrics seem to reset

Likely cause:

- `PerformanceMetrics` stores timings only in process memory

What to check:

- whether the backend process restarted
- whether a new import/session lifecycle recreated the metrics object

## Symptom: The system is logging too much in development

Likely causes:

- backend `basicConfig` is set to `DEBUG`
- frontend components emit many timing logs
- AI modules emit debug and timing information

What to check:

- whether you are in an especially noisy ticket-rendering or categorization path
- whether verbose mode or batch processing is producing extra detail

## Symptom: The system is not logging enough for root-cause analysis

Likely causes:

- some failures are only surfaced at a high level
- logs are split across terminal, files, and browser console
- not all business flows have dedicated log events

What to check:

- backend console output
- AI rotating log files
- browser console

Structural limitation:

- the current architecture is not yet a complete observability platform

## Symptom: File logging feels like the wrong long-term solution

This concern is reasonable.

Based on the current implementation, file logging is helpful for local development and basic retention, but it has clear limitations:

- it is harder to query
- it is local to the machine/process
- it does not model logs as first-class application data
- it does not naturally support richer analysis or cross-request views

See [future-direction.md](docs/services/logging-system/future-direction.md) for the improvement direction.

## Known Structural Gaps

Verified from the current code:

- no centralized log database
- no request correlation IDs
- no unified structured event schema
- no durable frontend logging
- no single logging configuration for the whole repository

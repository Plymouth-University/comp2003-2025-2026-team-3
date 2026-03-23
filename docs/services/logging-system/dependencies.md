# Logging System Dependencies

## Purpose

This document lists the code and platform dependencies that the current logging system relies on.

## Internal Code Dependencies

### Backend entrypoint logging

Files:

- `backend/app/main.py`
- `backend/app/database.py`
- `backend/app/providers/fake_autotask.py`

Dependency:

- Python standard `logging`

Used for:

- startup/shutdown messages
- request instrumentation
- provider load/cache messages
- database lifecycle messages

### AI logging configuration

File:

- `backend/app/services/ai/logging_config.py`

Depends on:

- `logging`
- `logging.handlers`
- `pathlib.Path`
- filesystem write access for the log directory

Used for:

- named AI logger setup
- rotating file handlers
- performance logger setup
- in-memory metrics collection

### AI modules that emit logs and metrics

Files:

- `backend/app/services/ai/config.py`
- `backend/app/services/ai/categorizer.py`
- `backend/app/services/ai/processor.py`
- `backend/app/services/ai/text_processor.py`
- `backend/app/services/ai/description_generator.py`
- `backend/app/services/ai/storage.py`

Depend on:

- the logger and metrics objects from `logging_config.py`

### Frontend logging call sites

Files:

- `frontend/src/pages/Dashboard.ts`
- `frontend/src/components/TicketListContainer.ts`

Depend on:

- browser `console`
- browser `performance.now()`
- local helper timestamp functions in those modules

## Platform Dependencies

### Filesystem access

Required by:

- `backend/app/services/ai/logging_config.py`

Why:

- it creates `backend/logs/ai_services/`
- it writes rotating log files into that directory

What happens if this matters:

- if the directory cannot be created or files cannot be opened, the code catches exceptions and prints warnings instead of crashing immediately

### Running process memory

Required by:

- `PerformanceMetrics`

Why:

- metrics are accumulated in memory while the backend process is alive

Limitation:

- memory-held metrics are not durable

### Browser developer tools

Required for:

- seeing frontend logs

Why:

- frontend instrumentation is not persisted anywhere else

## Third-Party And Standard Library Dependencies

### Python standard logging

Used by:

- backend app modules
- AI logging setup

Purpose:

- logger creation
- log-level handling
- formatting
- stream/file handlers

### `logging.handlers.RotatingFileHandler`

Used by:

- `backend/app/services/ai/logging_config.py`

Purpose:

- rotate AI log files instead of letting them grow forever

### Browser console and timing APIs

Used by:

- frontend dashboard and ticket list components

Purpose:

- local debugging
- timing measurements for fetch and render paths

## Operational Assumptions

The current logging system assumes:

- the backend process can write to the AI logs directory if file logging is desired
- the backend process will stay alive long enough for in-memory metrics to be useful
- developers will inspect browser console logs manually during frontend debugging
- timestamps are good enough for rough manual correlation across layers

## Dependency Gaps

The current system does not depend on:

- a database logging table
- a centralized log service
- OpenTelemetry
- a metrics backend such as Prometheus
- a structured log pipeline

That absence is important because it explains why the logging story is currently developer-focused rather than fully operationally mature.

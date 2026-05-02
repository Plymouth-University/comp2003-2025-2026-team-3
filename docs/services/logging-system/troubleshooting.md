# Logging System Troubleshooting

## Purpose

This guide helps developers debug missing, surprising, or incomplete logs in the current database-backed logging system.

Start by identifying which logging path you are checking:

- durable logs in `logsdb`
- backend terminal logs
- AI rotating file logs
- browser console logs

Durable structured logs are the current canonical path for important application, error, performance, and UI interaction events. Terminal and file logs still exist for development support.

## Quick Checks

When logs do not look right, check these first:

1. Is `postgres_logs` running?
2. Does `LOG_DATABASE_URL` point to the same database you are inspecting?
3. Have `backend/alembic_logs` migrations been applied?
4. Is the route or frontend action expected to write a durable log?
5. Are you checking the right table?
6. Did `LogWriter` fall back to Python logging because the log write failed?

Useful local query:

```sql
select request_id, first_seen_at, last_seen_at, source, environment
from request_trace
order by last_seen_at desc
limit 20;
```

## Symptom: No Rows Appear In Any Logs Table

Likely causes:

- the logs database is not running
- `LOG_DATABASE_URL` points somewhere else
- migrations were not applied
- backend startup is using an environment without `asyncpg`
- the code path being tested does not call durable logging

What to check:

- `backend/compose.yml` has `postgres_logs` on port `5435`
- `backend/app/config.py` default `LOG_DATABASE_URL`
- `backend/scripts/migrate_all_databases.py`
- backend terminal output for `Failed during log writer operation`

Recommended local setup command from `backend/`:

```bash
python scripts/migrate_all_databases.py
```

## Symptom: Request Traces Exist But Application Logs Are Missing

Likely causes:

- a log write failed after `request_trace` was touched
- you are filtering by the wrong `request_id`
- the event is written to another table, such as `error_logs` or `ui_click_analytics_logs`

What to check:

```sql
select *
from application_logs
order by occurred_at desc
limit 20;
```

Then compare with:

```sql
select *
from error_logs
order by occurred_at desc
limit 20;
```

## Symptom: `performance_logs` Has Rows But Some Metric Columns Are `NULL`

This can be expected.

Currently populated by request middleware:

- `total_duration_ms`
- `app_logic_ms`
- `memory_used_mb`, if measurable
- `payload_size_kb`, if request or response `Content-Length` is known
- `is_slow`

Currently not populated:

- `db_latency_ms`
- `external_api_latency_ms`

Why:

- middleware sees total request time, but it cannot know which internal time was database latency or external/provider latency without dedicated instrumentation.

Also expected:

- `payload_size_kb` may be `NULL` for streaming responses or responses without `Content-Length`
- `memory_used_mb` may be `NULL` if memory measurement fails on the runtime platform

## Symptom: `memory_used_mb` Looks Large

Likely cause:

- the value represents process resident memory, not memory used only by one request

The current implementation records process RSS memory. It is useful for spotting broad memory growth, but it should not be interpreted as per-request allocation size.

## Symptom: `payload_size_kb` Is `NULL`

Likely causes:

- request had no body and no `Content-Length`
- response did not include `Content-Length`
- response was streamed

Current behavior:

- payload size is calculated only from known request and response `Content-Length` headers
- the middleware does not consume response bodies to calculate exact size, because that could change response behavior

## Symptom: UI Click Logs Are Missing

Likely causes:

- the user is not authenticated
- the frontend action does not call `logUIClick()`
- the request to `/api/v1/logs/ui-clicks` failed
- the browser blocked or interrupted the best-effort request

What to check:

- browser network tab for `POST /api/v1/logs/ui-clicks`
- browser console for `UI log event was not persisted`
- backend table:

```sql
select *
from ui_click_analytics_logs
order by occurred_at desc
limit 20;
```

Important behavior:

- frontend UI logging is intentionally non-blocking
- a failed UI log does not stop the user action

## Symptom: Frontend UI Logs Have Different Request IDs From The Main API Action

This is currently expected.

The UI log is sent as its own HTTP request to `/api/v1/logs/ui-clicks`. The backend middleware generates a server-owned request ID for that ingestion request.

Future improvement:

- add a browser action ID or trace ID that groups a UI action and subsequent API calls together

## Symptom: Inbound `X-Request-ID` Is Not Used As The Primary Request ID

This is intentional.

The backend always creates its own authoritative request ID. A valid inbound `X-Request-ID` is stored only as metadata in JSON `details`.

Reason:

- request IDs are correlation data, not identity or authorization data
- accepting arbitrary client request IDs as authoritative can make tracing confusing and easier to spoof

## Symptom: Backend Works But Durable Logs Are Not Written

Likely cause:

- `LogWriter` swallows logging failures by design

Why:

- logging must not break normal application behavior

What to check:

- backend terminal output for fallback logger messages:

```text
Failed during log writer operation ...
```

Common underlying causes:

- logs database unavailable
- missing logs tables
- invalid UUID passed as tenant/profile context
- JSON details containing values that cannot be encoded

## Symptom: AI File Logs And Database Logs Do Not Match

This is expected.

The AI logger in `backend/app/services/ai/logging_config.py` writes console/file logs and in-memory metrics. Durable database logging records selected request and business events.

The two systems overlap in purpose but are not the same sink.

## Symptom: Too Many Request Logs

Current behavior:

- middleware logs every HTTP request start and completion
- every completed request also writes one performance row

This is useful for visibility but can be noisy in development. There is no sampling or route exclusion policy yet.

Future options:

- exclude health checks
- sample low-value routes
- reduce request-start logs and keep only completion/performance rows
- add environment-specific logging policies

## Symptom: Important Business Action Is Not In `application_logs`

Likely cause:

- that route has not been explicitly instrumented yet

Current durable business instrumentation covers:

- auth login/logout/session-profile failures
- AI refresh, oversight, close, update, category override, assignment override
- profile, tenant, identity, and specialism management
- cache clear

If another business action matters operationally, add a `LogWriter.write_application_log()` call at the route or service boundary.

## Safe Debugging Queries

Recent request lifecycle:

```sql
select occurred_at, endpoint, method, status_code, outcome, duration_ms, request_id
from application_logs
where log_type = 'backend_request'
order by occurred_at desc
limit 50;
```

Recent errors:

```sql
select occurred_at, service_name, action, severity, error_type, message, request_id
from error_logs
order by occurred_at desc
limit 50;
```

Slow requests:

```sql
select occurred_at, endpoint, method, status_code, total_duration_ms, memory_used_mb, payload_size_kb
from performance_logs
where is_slow = 1
order by occurred_at desc
limit 50;
```

Recent UI events:

```sql
select occurred_at, page_path, component, action_type, element_id, tenant_id, profile_id
from ui_click_analytics_logs
order by occurred_at desc
limit 50;
```

# Logging Architecture Diagram

## System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Services Execution                        │
│                                                                 │
│  process_ticket() → categorizer → text_processor → storage    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ (all logging calls)
                              ▼
                    ┌─────────────────┐
                    │ logging_config  │
                    │   (setup)       │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌────────────┐   ┌──────────────┐   ┌──────────────┐
    │  Console   │   │   Loggers    │   │   Handlers   │
    │            │   │              │   │              │
    │ INFO+      │   │ ai_services  │   │ Rotating     │
    │            │   │ .processor   │   │ FileHandler  │
    │ "Process   │   │ .categorizer │   │              │
    │  ticket"   │   │ .performance │   │ 10MB/5.5MB   │
    │            │   │              │   │ max files    │
    └────────────┘   └──────────────┘   └──────────────┘
         │                   │                   │
         │                   ▼                   │
         │          ┌──────────────────┐         │
         │          │   METRICS        │         │
         │          │                  │         │
         │          │ record_operation │         │
         │          │ get_summary()    │         │
         │          │ log_summary()    │         │
         │          └──────────────────┘         │
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌──────────┐      ┌──────────────┐    ┌──────────────┐
    │ CONSOLE  │      │  MAIN LOG    │    │    PERF LOG  │
    │          │      │              │    │              │
    │ Clean    │      │ ai_services. │    │ ai_services_ │
    │ Terminal │      │ log          │    │ performance. │
    │ Output   │      │              │    │ log          │
    │          │      │ All details  │    │              │
    │ INFO+    │      │ DEBUG+       │    │ [TIMING]     │
    │          │      │              │    │ metrics only │
    └──────────┘      └──────────────┘    └──────────────┘
                             │                   │
                             ▼                   ▼
                    ┌──────────────────────────────┐
                    │    ERROR LOG                 │
                    │  ai_services_errors.log      │
                    │  WARNING+ only               │
                    └──────────────────────────────┘
```

## Data Flow: Single Ticket Processing

```
START: process_ticket()
  │
  ├─→ extract_ticket_text()
  │   ├─→ metrics.record_operation("extract_ticket_text", time)
  │   └─→ perf_logger.debug("[TIMING] ...")
  │
  ├─→ predict_category_hybrid()
  │   ├─→ model.encode()
  │   │   ├─→ metrics.record_operation("model.encode", time)
  │   │   └─→ perf_logger.debug("[TIMING] ...")
  │   │
  │   └─→ cosine_similarity()
  │       ├─→ metrics.record_operation("cosine_similarity", time)
  │       └─→ perf_logger.debug("[TIMING] ...")
  │
  ├─→ save_ticket_to_json()
  │   ├─→ metrics.record_operation("save_ticket_to_json", time)
  │   └─→ perf_logger.debug("[TIMING] ...")
  │
  ├─→ logger.info("Processed ticket '...' in Xms")  ← CONSOLE
  │
  ├─→ metrics.record_operation("process_ticket_total", time)
  │
  └─→ RETURN
  
END (console shows: "Processed ticket 'X' in 52.74ms - Category: Y, Priority: Z")
```

## Batch Processing Flow

```
START: process_input_tickets()
  │
  ├─→ logger.info("Found N ticket files")  ← CONSOLE
  │
  ├─→ FOR EACH ticket_file:
  │   │
  │   ├─→ load_tickets_from_file()
  │   │
  │   └─→ FOR EACH ticket IN file:
  │       │
  │       └─→ process_ticket()  [see above]
  │           (metrics accumulate)
  │
  ├─→ logger.info("Batch complete: X tickets in Ys")  ← CONSOLE
  │
  ├─→ metrics.log_summary(logger)
  │   │
  │   └─→ logger.info(PERFORMANCE SUMMARY)  ← CONSOLE
  │       ├─→ model.encode: count=100, avg=5.23ms, ...
  │       ├─→ cosine_similarity: count=100, avg=3.40ms, ...
  │       ├─→ extract_ticket_text: count=100, avg=2.34ms, ...
  │       └─→ ... (all aggregated stats)
  │
  └─→ RETURN

END (all detailed [TIMING] in perf_logger file, console shows clean summary)
```

## Log File Organization

```
logs/ai_services/
│
├── ai_services.log                   ← Main log (ALL details)
│   ├── 2026-01-31 10:00 - DEBUG - [TIMING] model.encode...
│   ├── 2026-01-31 10:00 - DEBUG - [TIMING] cosine_similarity...
│   ├── 2026-01-31 10:00 - INFO - Processed ticket 'X'...
│   ├── 2026-01-31 10:05 - INFO - Batch complete...
│   ├── 2026-01-31 10:05 - INFO - PERFORMANCE SUMMARY...
│   └── (rotates when reaches 10MB, keeps 5 backups)
│
├── ai_services.log.1                ← Previous rotated file
├── ai_services.log.2
├── ai_services.log.3
├── ai_services.log.4
├── ai_services.log.5
│
├── ai_services_performance.log       ← Performance metrics only
│   ├── 2026-01-31 10:00 - model.encode() took 5.23ms...
│   ├── 2026-01-31 10:00 - cosine_similarity took 3.40ms...
│   ├── 2026-01-31 10:00 - extract_ticket_text took 2.34ms...
│   └── (rotates when reaches 5MB, keeps 3 backups)
│
├── ai_services_performance.log.1
├── ai_services_performance.log.2
├── ai_services_performance.log.3
│
├── ai_services_errors.log           ← Errors only
│   ├── 2026-01-31 10:12 - ERROR - Failed to process file...
│   ├── 2026-01-31 10:15 - WARNING - Model encoding slow...
│   └── (rotates when reaches 5MB, keeps 10 backups)
│
├── ai_services_errors.log.1
├── ai_services_errors.log.2
├── ... (up to 10 backups)
```

## Handler Configuration Reference

```python
┌─────────────────────────────────────────────────────────────┐
│                    HANDLER MATRIX                           │
├──────────────────┬──────────┬──────────┬──────────┬──────────┤
│ Log Level        │ Console  │  Main    │ Perf Log │  Errors  │
├──────────────────┼──────────┼──────────┼──────────┼──────────┤
│ DEBUG            │    ✗     │    ✓     │    ✓     │    ✗     │
│ INFO             │    ✓     │    ✓     │    ✗     │    ✗     │
│ WARNING          │    ✗     │    ✓     │    ✗     │    ✓     │
│ ERROR            │    ✗     │    ✓     │    ✗     │    ✓     │
│ CRITICAL         │    ✗     │    ✓     │    ✗     │    ✓     │
├──────────────────┴──────────┴──────────┴──────────┴──────────┤
│ File Rotation                                                │
├──────────────────┬──────────────────────────────────────────┤
│ Console          │ N/A (stdout)                             │
│ Main Log         │ 10MB max, keep 5 backups                │
│ Performance Log  │ 5MB max, keep 3 backups                 │
│ Error Log        │ 5MB max, keep 10 backups                │
└────────────────────────────────────────────────────────────┘
```

## Integration Points for Future Scaling

```
Current State                          Future Possibilities
─────────────────────                 ──────────────────────

Rotating File Handlers    ─────────→  Fluentd/Logstash
                                     (log shipping)

Performance Metrics       ─────────→  Prometheus Exporter
                                     (metrics scraping)

Structured JSON Format    ─────────→  Elasticsearch
                                     (centralized search)

Logger Hierarchy          ─────────→  OpenTelemetry
                                     (distributed tracing)

Console Output            ─────────→  Grafana Dashboards
                                     (visualization)

Error Aggregation         ─────────→  Sentry/Rollbar
                                     (error tracking)
```

This architecture is **production-ready** and scales horizontally! 🚀

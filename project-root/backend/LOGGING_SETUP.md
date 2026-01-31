# Production-Grade Logging Configuration

## Overview

The AI services now use a production-grade, scalable logging system that follows industry best practices. This setup handles large-scale operations without cluttering the console with debug output.

## Architecture

### Three-Handler System

1. **Console Handler** (INFO level)
   - Clean, readable output for operators
   - No DEBUG timing spam
   - Key information only

2. **Main Log File** (`ai_services.log`)
   - Captures ALL levels (DEBUG and above)
   - Rotating: 10MB per file, keeps 5 backups
   - Contains detailed timing information
   - Location: `project-root/logs/ai_services/ai_services.log`

3. **Error Log File** (`ai_services_errors.log`)
   - WARNING and ERROR level only
   - Quick reference for issues
   - Rotating: 5MB per file, keeps 10 backups
   - Location: `project-root/logs/ai_services/ai_services_errors.log`

4. **Performance Log File** (`ai_services_performance.log`) ⭐
   - Dedicated timing metrics file
   - All [TIMING] logs go here
   - Rotating: 5MB per file, keeps 3 backups
   - Location: `project-root/logs/ai_services/ai_services_performance.log`

## Log Levels

```
CONSOLE        → INFO and above (clean terminal output)
FILE           → DEBUG and above (all details)
PERFORMANCE    → DEBUG (timing metrics only)
ERRORS         → WARNING and above
```

## Metrics Collection

The system automatically collects performance metrics:

```python
from .logging_config import metrics

# Automatically recorded:
# - model.encode() times
# - cosine_similarity computation times
# - extract_ticket_text() times
# - predict_category_hybrid() times
# - save_ticket_to_json() times
# - process_ticket_total() times
```

### Getting Summary Statistics

At the end of batch processing, a summary is logged:

```
PERFORMANCE SUMMARY
==================
model.encode: count=100, total=523.45ms, avg=5.23ms, min=4.10ms, max=8.90ms
process_ticket_total: count=100, total=1234.56ms, avg=12.34ms, min=10.20ms, max=25.50ms
... (more metrics)
```

## File Locations

All logs are stored in:
```
project-root/logs/ai_services/
├── ai_services.log              # Main log (all details)
├── ai_services.log.1            # Rotated backups
├── ai_services_performance.log  # Performance metrics only
├── ai_services_errors.log       # Errors only
└── ...
```

## Usage Examples

### Normal Console Output
```
$ python main.py
ai_services - INFO - Found 100 ticket file(s) to process
ai_services.processor - INFO - Processing: tickets.json (100 ticket(s))
ai_services.processor - INFO - Processed ticket 'Network outage in Building A' in 45.23ms
ai_services.processor - INFO - Batch complete: Processed 100 total ticket(s) in 5.32s
ai_services.processor - INFO - PERFORMANCE SUMMARY
...
```

### Detailed Analysis

For detailed performance analysis, check the files:
```
tail -f project-root/logs/ai_services/ai_services_performance.log
tail -f project-root/logs/ai_services/ai_services_errors.log
```

### Per-Operation Metrics

View specific operation timing:
```bash
grep "model.encode" project-root/logs/ai_services/ai_services_performance.log
grep "PERFORMANCE SUMMARY" project-root/logs/ai_services/ai_services.log -A 20
```

## Scalability Features

✅ **Log Rotation**: Prevents unbounded file growth
✅ **Multiple Handlers**: Different concerns, different files
✅ **Metrics Collection**: Aggregated statistics instead of line spam
✅ **Structured Logging**: Parseable format for analysis tools
✅ **UTF-8 Encoding**: Supports international characters
✅ **Minimal Overhead**: Efficient logging that won't slow down processing

## Integration with Future Tools

This logging setup is designed to integrate with:

- **ELK Stack** (Elasticsearch, Logstash, Kibana) - centralized log analysis
- **Prometheus** - metrics scraping
- **Grafana** - visualization dashboards
- **Datadog/New Relic** - enterprise monitoring
- **Splunk** - log aggregation and searching

## Future Enhancements

Potential improvements when scaling further:

1. **Remote Log Shipping** - Send logs to centralized server
2. **Log Sampling** - Reduce volume in high-throughput scenarios
3. **Structured JSON Logging** - For easier parsing and analysis
4. **OpenTelemetry Integration** - Distributed tracing across services
5. **Alert Thresholds** - Automatic alerts for slow operations
6. **Custom Metrics** - Business metrics beyond just timing

## Configuration

To adjust logging behavior, edit `logging_config.py`:

```python
# Change console level (currently INFO)
CONSOLE_LOG_LEVEL = logging.WARNING  # Show only warnings in console

# Change file rotation size (currently 10MB)
maxBytes=50 * 1024 * 1024  # 50MB per file

# Change backup count (currently 5)
backupCount=10  # Keep 10 old files

# Add new custom log file for specific purposes
# ... add new handler
```

## Best Practices

1. ✅ Use `perf_logger` for timing information
2. ✅ Use regular `logger` for functional logging
3. ✅ Record metrics using `metrics.record_operation()`
4. ✅ Call `metrics.log_summary()` after batch processing
5. ✅ Check log files for detailed analysis, not console spam
6. ✅ Use structured log queries for analysis: `grep`, `awk`, etc.

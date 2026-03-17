# AI Services Logging: Developer Guide

This document provides a concise overview of the logging system for the AI services. For the complete implementation, see [`backend/app/services/ai/logging_config.py`](backend/app/services/ai/logging_config.py).

## Core Concepts

The logging system is built on Python's standard `logging` module and is designed to be robust, scalable, and easy to use. It separates logs into multiple streams based on their purpose.

### Key Features:
- **Centralized Configuration**: All setup is handled in a single file.
- **Multiple Handlers**: Logs are sent to the console, a main log file, a performance log file, and an error log file.
- **Rotating Files**: Log files are automatically rotated to prevent them from growing indefinitely.
- **Structured Performance Metrics**: A dedicated class (`PerformanceMetrics`) and logger (`perf_logger`) are available for tracking performance.

## Log Files

All log files are stored in the `backend/logs/ai_services/` directory.

| File Name                     | Log Level | Purpose                                                                                             | Rotation Policy              |
| ----------------------------- | --------- | --------------------------------------------------------------------------------------------------- | ---------------------------- |
| `ai_services.log`             | `DEBUG`+  | **Main Log**: Captures all log messages, providing a complete record of events for detailed debugging.  | 10MB file size, 5 backups    |
| `ai_services_performance.log` | `DEBUG`+  | **Performance Log**: Exclusively records performance-related timing metrics from the `perf_logger`.     | 5MB file size, 3 backups     |
| `ai_services_errors.log`      | `WARNING`+ | **Error Log**: Captures only warnings, errors, and critical failures for quick issue identification. | 5MB file size, 10 backups    |
| **Console Output**            | `INFO`+   | Provides a clean, high-level view of the application's status in the terminal without debug spam.   | N/A                          |

## How to Add Logs

To add logging to any module within the AI services, import the necessary components and use the logger instances.

### 1. Import Loggers

Add this import statement to your Python file:

```python
from .logging_config import logger, perf_logger, metrics
```

### 2. Use the Loggers

Call the appropriate method on the logger instance. The system will automatically route the message to the correct destinations.

#### General Logging (`logger`)

- **Informational Messages**: For high-level status updates.
  ```python
  logger.info("Ticket processing has started for batch 'abc'.")
  ```

- **Debug Messages**: For detailed, low-level information useful during development.
  ```python
  logger.debug(f"Ticket data: {ticket.to_dict()}")
  ```

- **Warnings**: For non-critical issues that should be noted.
  ```python
  logger.warning(f"Configuration value 'x' is missing. Using default.")
  ```

- **Errors**: For exceptions and critical failures.
  ```python
  try:
      result = 10 / 0
  except ZeroDivisionError:
      logger.error("An attempt to divide by zero occurred.", exc_info=True)
  ```
  *(`exc_info=True` automatically includes the stack trace in the log.)*

#### Performance Logging (`perf_logger` & `metrics`)

For tracking execution time, use both the `perf_logger` and the `metrics` collector.

```python
import time

start_time = time.perf_counter()

# --- Code you want to measure ---
heavy_computation()
# --------------------------------

duration_ms = (time.perf_counter() - start_time) * 1000

# 1. Log the specific timing to the performance log file
perf_logger.debug(f"[TIMING] 'heavy_computation' took {duration_ms:.2f}ms")

# 2. Add the timing to the metrics collector for end-of-run summary
metrics.record_operation("heavy_computation", duration_ms)
```

At the end of a batch process, `metrics.log_summary(logger)` is called to print an aggregated performance report to the main log and console.

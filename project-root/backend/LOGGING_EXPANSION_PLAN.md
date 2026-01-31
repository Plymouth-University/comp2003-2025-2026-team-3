# Project-Wide Logging: Expansion Plan

This document outlines a strategic plan for extending the robust logging system, currently implemented in the AI services, to other parts of the application, such as a future `billing_service` or `notification_service`.

## Guiding Principles

1.  **Consistency**: All services should follow the same fundamental logging patterns.
2.  **Isolation**: Each service's logs should be clearly separated to simplify debugging.
3.  **Centralized Patterns, Decentralized Configuration**: The overall architecture should be consistent, but each service will manage its own logging configuration.

## Proposed Directory Structure

To maintain isolation, each new service should have its own dedicated log directory.

```
project-root/
└── backend/
    ├── logs/
    │   ├── ai_services/
    │   │   ├── ai_services.log
    │   │   └── ai_services_errors.log
    │   ├── billing_service/
    │   │   ├── billing.log
    │   │   └── billing_errors.log
    │   └── notification_service/
    │       ├── notifications.log
    │       └── notifications_errors.log
    │
    ├── app/
    │   ├── services/
    │   │   ├── ai/
    │   │   │   └── logging_config.py
    │   │   ├── billing/
    │   │   │   └── logging_config.py  // Future
    │   │   └── notifications/
    │   │       └── logging_config.py  // Future
```

## Implementation Strategy

When adding a new service (e.g., `billing_service`), follow these steps:

### 1. Create a Service-Specific `logging_config.py`

- **Copy and Adapt**: Duplicate `project-root/backend/app/services/ai/logging_config.py` into the new service's directory (e.g., `project-root/backend/app/services/billing/`).
- **Customize Paths and Names**:
  - Modify the `LOG_DIR` to point to the new service's log folder (e.g., `.../logs/billing_service`).
  - Change the log file names (e.g., `billing.log`, `billing_errors.log`).
  - Update the root logger name (e.g., `logging.getLogger("billing_service")`).

**Example (`billing/logging_config.py`):**
```python
# Log directory
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs" / "billing_service"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file paths
MAIN_LOG_FILE = LOG_DIR / "billing.log"
ERROR_LOG_FILE = LOG_DIR / "billing_errors.log"

def setup_logging():
    # Use a unique name for the service's root logger
    root_logger = logging.getLogger("billing_service")
    # ... rest of the configuration
```

### 2. No Global Logger

Avoid creating a single, global logger for the entire application. Each service should initialize and use its own logger instance. This prevents log message collisions and ensures clear ownership.

### 3. Future: Centralized Log Aggregation

While isolated log files are ideal for development, a production environment at scale would benefit from centralized log management.

**Future Integration Points:**

- **Log Shippers (Fluentd/Logstash)**: Deploy agents to collect logs from all service directories and forward them to a central analysis platform.
- **Analysis Platform (Elasticsearch/Graylog/Datadog)**: Aggregate logs for advanced searching, visualization, and alerting across all services.
- **Distributed Tracing (OpenTelemetry)**: For even deeper insights, especially in a microservices architecture, we can integrate OpenTelemetry to trace requests as they travel between different services. This would involve adding correlation IDs to log messages.

By following this plan, we can maintain a clean and scalable logging architecture as the project grows in complexity.

# Logging Overview

This document provides a comprehensive overview of the logging strategy for both the frontend and backend of the SecOps Autotask Prototype.

## Backend Logging

The backend, built with FastAPI, uses Python's standard `logging` library.

### Configuration

-   **Level:** `logging.DEBUG`
-   **Format:** `%(asctime)s - %(levelname)s - %(message)s`
-   **Output:** Console (stdout)

This configuration is established in `backend/app/main.py`.

### Key Logging Points

-   **Application Lifespan:** Logs application startup and shutdown events.
-   **API Requests:**
    -   Logs the start and end of every API request to `/api/tickets`.
    -   Includes a timestamp and detailed context about the request, such as filters and batch mode.
    -   Provides a performance breakdown of key operations:
        -   Time to fetch tickets from the provider.
        -   Time for AI categorization.
        -   Time to prepare the response.
    -   Logs errors with stack traces if they occur during the request.
-   **AI Services:**
    -   Detailed logs for ticket categorization, including per-ticket processing time in verbose mode.
    -   Performance metrics for batch processing.
-   **Cache:** Logs statistics for the embedding cache.
-   **Streaming Endpoints:** Logs the progress and errors of the real-time categorization stream.

### Example Log Output

```
2023-10-27 10:30:00,123 - INFO - [10:30:00.123] ========== API REQUEST START ==========
2023-10-27 10:30:00,124 - INFO - [10:30:00.124] Filters: status=None, priority=None, category=None, limit=100, verbose=False, batch=True
2023-10-27 10:30:00,124 - INFO - [10:30:00.124] STEP 1: Fetching tickets from provider...
2023-10-27 10:30:00,250 - INFO - [10:30:00.250] STEP 1 COMPLETE: Retrieved 500 tickets in 0.126s
2023-10-27 10:30:00,251 - INFO - [10:30:00.251] STEP 4: Starting categorization of 100 tickets (batch mode: True)...
2023-10-27 10:30:01,500 - INFO - [10:30:01.500] BATCH: Categorized 100 tickets in 1.249s (avg 0.0125s per ticket)
2023-10-27 10:30:01,502 - INFO - [10:30:01.502] STEP 4 COMPLETE: Categorized 100 tickets in 1.251s (avg 0.013s per ticket)
2023-10-27 10:30:01,505 - INFO - [10:30:01.505] ========== API REQUEST COMPLETE ==========
2023-10-27 10:30:01,505 - INFO - [10:30:01.505] Total time: 1.381s - Returning 100 tickets
```

## Frontend Logging

The frontend uses the browser's `console.log` for performance and debugging information. The logging is designed to provide a clear timeline of operations from data fetching to rendering.

### Key Logging Points

-   **Performance Metrics:** The frontend is instrumented to measure and log the time taken for various critical operations.
-   **Data Fetching:**
    -   Logs the start and end of API requests.
    -   Measures and logs the time for network requests, receiving the response, and parsing JSON.
-   **Rendering:**
    -   Logs the start and end of the rendering process.
    -   Measures and logs the time for filtering, categorization, and UI rendering.
-   **Dashboard Load:**
    -   Provides a detailed breakdown of the total time to load the dashboard, including fetching, processing, and rendering times.

### Log Format

Frontend logs include a timestamp and a descriptive message, often with performance measurements in milliseconds.

```
[HH:MM:SS.ms] CATEGORY: Message
```

### Example Log Output

```
[10:30:02.123] ========== FRONTEND FETCH START ==========
[10:30:02.124] Initiating API request to /api/tickets
[10:30:02.125] Sending fetch request...
[10:30:03.550] Network request completed in 1425.0ms, status: 200
[10:30:03.560] JSON parsed in 10.0ms
[10:30:03.561] ========== FRONTEND FETCH COMPLETE ==========
[10:30:03.562] Total request time: 1438.0ms | Network: 1425.0ms | Parse: 10.0ms

[10:30:04.000] ========== FRONTEND RENDER START ==========
[10:30:04.001] Input: 100 total tickets, filters: search="" company="" queue=""
[10:30:04.015] Filtering complete in 14.0ms - 100 tickets to display
[10:30:04.025] Categorization complete in 10.0ms - 5 categories found
[10:30:04.035] Rendering UI for 5 categories...
[10:30:04.050] UI rendering complete in 15.0ms
[10:30:04.051] ========== FRONTEND RENDER COMPLETE ==========
[10:30:04.052] TIMING BREAKDOWN: Filter=14.0ms | Categorize=10.0ms | RenderUI=15.0ms | Total=40.0ms
```

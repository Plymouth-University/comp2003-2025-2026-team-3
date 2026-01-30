"""
Services package

This package contains backend service modules organized by concern:
- ai: AI-powered ticket categorization, prioritization, and processing
- [future]: Additional services can be added here

⚠️ Do not import heavy dependencies at package import time.
Import the specific service modules you need, e.g.:

    from app.services.ai import categorise_ticket
    from app.services.ai.processor import process_ticket
"""

# Intentionally left minimal to avoid side effects during import.
# Backwards compatibility: allow importing from old location
try:
    from app.services.ai import categorise_ticket
except ImportError:
    pass

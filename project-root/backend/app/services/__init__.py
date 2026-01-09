"""
Services package

This package contains backend service modules (AI categorisation, ticket processing, etc.).

⚠️ Do not import heavy dependencies at package import time.
Import the specific service modules you need, e.g.:

    from app.services.ai_categoriser import categorise_ticket
"""

# Intentionally left minimal to avoid side effects during import.

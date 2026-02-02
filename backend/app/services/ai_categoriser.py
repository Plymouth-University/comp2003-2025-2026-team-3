"""
Backwards Compatibility Module for AI Categoriser

This module maintains backwards compatibility with the original ai_categoriser.py
by re-exporting all functions from the refactored ai service package.

⚠️ DEPRECATED: New code should import from app.services.ai directly.

Migration guide:
    OLD: from app.services.ai_categoriser import categorise_ticket
    NEW: from app.services.ai import categorise_ticket
"""

import logging

logger = logging.getLogger(__name__)

# Import and re-export all public functions from the new modular structure
from app.services.ai.processor import (
    process_ticket,
    categorise_ticket,
    process_input_tickets,
)
from app.services.ai.text_processor import (
    preprocess_text,
    extract_ticket_text,
    detect_company,
)
from app.services.ai.categorizer import (
    predict_category_by_keywords,
    predict_category_by_semantic,
    predict_category_hybrid,
)
from app.services.ai.priority_calculator import (
    calculate_priority_score,
    get_priority_label,
)
from app.services.ai.description_generator import (
    generate_ai_description,
)
from app.services.ai.storage import (
    save_ticket_to_json,
    get_input_tickets,
    load_tickets_from_file,
)
from app.services.ai.config import (
    CATEGORY_DESCRIPTIONS,
    CATEGORY_KEYWORDS,
    CATEGORY_EMBEDDINGS,
    PRIORITY_WEIGHTS,
    COMPANY_NAMES,
    TICKETS_BASE_PATH,
    INPUT_TICKETS_PATH,
)

__all__ = [
    # Processor functions
    "process_ticket",
    "categorise_ticket",
    "process_input_tickets",
    # Text processing
    "preprocess_text",
    "extract_ticket_text",
    "detect_company",
    # Category prediction
    "predict_category_by_keywords",
    "predict_category_by_semantic",
    "predict_category_hybrid",
    # Priority
    "calculate_priority_score",
    "get_priority_label",
    # Description
    "generate_ai_description",
    # Storage
    "save_ticket_to_json",
    "get_input_tickets",
    "load_tickets_from_file",
    # Config
    "CATEGORY_DESCRIPTIONS",
    "CATEGORY_KEYWORDS",
    "CATEGORY_EMBEDDINGS",
    "PRIORITY_WEIGHTS",
    "COMPANY_NAMES",
    "TICKETS_BASE_PATH",
    "INPUT_TICKETS_PATH",
]

logger.info("ai_categoriser module loaded in compatibility mode. Consider updating imports to use app.services.ai directly.")

# Legacy aliases for backwards compatibility with different naming conventions
predict_category = predict_category_by_keywords
semantic_category_prediction = predict_category_by_semantic
hybrid_category_prediction = predict_category_hybrid
calculate_dynamic_priority = calculate_priority_score

if __name__ == "__main__":
    # Load config and process input tickets
    process_input_tickets()

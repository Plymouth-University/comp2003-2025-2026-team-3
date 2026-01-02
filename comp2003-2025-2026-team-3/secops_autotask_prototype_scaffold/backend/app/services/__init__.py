"""
Ticket Processing System

A comprehensive ticket categorization and processing system that uses:
- SentenceTransformer for semantic analysis
- Spacy for NLP processing
- Hybrid keyword + AI categorization
- Dynamic priority calculation
- AI-generated ticket descriptions
"""

from .ai_categoriser import (
    process_ticket,
    process_input_tickets,
    detect_company,
    hybrid_category_prediction,
    calculate_dynamic_priority,
    generate_ai_description,
    load_config,
    save_config,
    CATEGORY_KEYWORDS,
    COMPANY_NAMES,
    TICKETS_BASE_PATH,
    INPUT_TICKETS_PATH,
    CONFIG_PATH
)

# Alias for backwards compatibility
categorise_ticket = process_ticket

__version__ = "1.0.0"
__author__ = "Toby Wood"
__all__ = [
    "process_ticket",
    "categorise_ticket",
    "process_input_tickets",
    "detect_company",
    "hybrid_category_prediction",
    "calculate_dynamic_priority",
    "generate_ai_description",
    "load_config",
    "save_config",
    "CATEGORY_KEYWORDS",
    "COMPANY_NAMES",
    "TICKETS_BASE_PATH",
    "INPUT_TICKETS_PATH",
    "CONFIG_PATH"
]

"""
AI Service Package

Modular AI service for ticket categorization and prioritization.

Modules:
    - config: Configuration and constants
    - text_processor: Text preprocessing and extraction
    - categorizer: Category prediction (keyword + semantic)
    - priority_calculator: Priority scoring
    - processor: Main orchestrator
"""

from .processor import process_ticket, categorise_ticket
from .categorizer import list_available_categories, predict_categories_batch

__all__ = [
    "process_ticket",
    "categorise_ticket",
    "predict_categories_batch",
    "list_available_categories",
]

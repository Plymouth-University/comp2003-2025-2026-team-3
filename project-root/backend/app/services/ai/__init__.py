"""
AI Service Package

Modular AI service for ticket categorization, prioritization, and processing.
This package organizes AI functionality into specialized modules for better
maintainability and scalability.

Modules:
    - config: Configuration and constants
    - text_processor: Text preprocessing and extraction
    - categorizer: Category prediction (keyword + semantic)
    - priority_calculator: Priority scoring
    - description_generator: AI-powered description generation
    - storage: File storage and I/O
    - processor: Main orchestrator
"""

from .processor import process_ticket, categorise_ticket, process_input_tickets

__all__ = [
    "process_ticket",
    "categorise_ticket",
    "process_input_tickets",
]

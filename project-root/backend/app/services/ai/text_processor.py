"""
Text Processing Module

Handles text preprocessing, cleaning, and extraction from various ticket formats.
"""

import spacy
import logging
import time
from .config import MIN_TOKEN_LENGTH, COMPANY_NAMES
from .logging_config import perf_logger, metrics

logger = logging.getLogger(__name__)

# Load spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None


def preprocess_text(text: str) -> list:
    """
    Preprocess text using spaCy for tokenization, lemmatization, and filtering.
    
    Args:
        text: Raw text to preprocess
        
    Returns:
        List of lemmatized, cleaned tokens
    """
    if not nlp:
        logger.error("spaCy model not loaded, cannot preprocess text")
        return []
    
    spacy_start = time.time()
    doc = nlp(text.lower())
    spacy_time = time.time() - spacy_start
    metrics.record_operation("spacy_nlp", spacy_time * 1000)
    
    if spacy_time > 0.05:  # Only log if slow
        perf_logger.debug(f"[TIMING] spaCy nlp() took {spacy_time*1000:.2f}ms for text length {len(text)}")
    
    # Build set of company words to filter
    company_words = set()
    for company in COMPANY_NAMES:
        company_words.update(company.lower().split())
    
    # Find multi-word company names in text
    text_lower = text.lower()
    company_tokens_to_exclude = set()
    for company in COMPANY_NAMES:
        if company in text_lower:
            company_tokens_to_exclude.update(company.split())
    
    # Filter tokens: remove stopwords, punctuation, company names, and short tokens
    filtered = [
        token.lemma_ for token in doc 
        if not token.is_stop 
        and not token.is_punct 
        and token.lemma_ not in company_tokens_to_exclude
        and len(token.lemma_) > MIN_TOKEN_LENGTH
    ]
    
    return filtered


def extract_ticket_text(ticket_item) -> str:
    """
    Extract and combine relevant text from various ticket formats.
    
    Args:
        ticket_item: Can be a string, dict with text fields, or structured ticket
        
    Returns:
        Combined text representation of the ticket
    """
    if isinstance(ticket_item, str):
        return ticket_item
    
    if not isinstance(ticket_item, dict):
        return None
    
    # Try direct text fields first
    if "text" in ticket_item:
        return ticket_item["text"]
    if "input_text" in ticket_item:
        return ticket_item["input_text"]
    
    # For structured tickets, combine relevant fields
    parts = []
    
    if "title" in ticket_item:
        parts.append(ticket_item["title"])
    
    if "description" in ticket_item:
        parts.append(ticket_item["description"])
    
    if "sub_issue_type" in ticket_item:
        parts.append(f"Type: {ticket_item['sub_issue_type']}")
    
    return " ".join(parts) if parts else None


def detect_company(text: str) -> list:
    """
    Detect company names mentioned in ticket text.
    
    Args:
        text: Ticket text to search
        
    Returns:
        List of detected company names
    """
    tokens = preprocess_text(text)
    text_lower = text.lower()
    
    detected_companies = []
    for company in COMPANY_NAMES:
        if company in tokens or company in text_lower:
            detected_companies.append(company)
    
    return detected_companies

"""
Priority Calculation Module

Calculates ticket priority scores based on category, urgency, and other factors.
"""

import logging
from .config import (
    CATEGORY_PRIORITY_WEIGHTS,
    URGENCY_KEYWORDS,
    MAX_PRIORITY_SCORE,
    MIN_PRIORITY_SCORE,
    MAX_LENGTH_ADJUSTMENT,
    WORDS_PER_LENGTH_UNIT
)
from .text_processor import preprocess_text

logger = logging.getLogger(__name__)


def calculate_priority_score(
    text: str,
    category: str,
    semantic_scores: dict
) -> int:
    """
    Calculate dynamic priority score based on multiple factors.
    
    Args:
        text: Ticket text
        category: Predicted category
        semantic_scores: Dictionary of semantic confidence scores
        
    Returns:
        Priority score (0-100)
    """
    base = 10
    
    # Category weight (most important factor)
    cat_weight = CATEGORY_PRIORITY_WEIGHTS.get(category, 10)
    base += cat_weight
    logger.debug(f"Priority: base={base}, category weight={cat_weight}")
    
    # Urgency words in text
    urgency_score = sum(10 for w in URGENCY_KEYWORDS if w in text.lower())
    base += urgency_score
    if urgency_score > 0:
        logger.debug(f"Priority: urgency score={urgency_score}")
    
    # Semantic confidence adjustment
    semantic_confidence = semantic_scores.get(category, 0)
    confidence_adjustment = int(semantic_confidence / 10)  # Scale 0-100 to 0-10
    base += confidence_adjustment
    logger.debug(f"Priority: semantic confidence={semantic_confidence}%, adjustment={confidence_adjustment}")
    
    # Length adjustment (longer tickets may indicate more complex issues)
    word_count = len(text.split())
    length_adjustment = min(word_count // WORDS_PER_LENGTH_UNIT, MAX_LENGTH_ADJUSTMENT)
    base += length_adjustment
    if length_adjustment > 0:
        logger.debug(f"Priority: length adjustment={length_adjustment} (words={word_count})")
    
    # Cap between min and max
    final_priority = max(MIN_PRIORITY_SCORE, min(base, MAX_PRIORITY_SCORE))
    
    logger.debug(f"Final priority score: {final_priority}")
    return final_priority


def get_priority_label(priority_score: int) -> str:
    """
    Convert priority score to human-readable label.
    
    Args:
        priority_score: Numerical priority score (0-100)
        
    Returns:
        Priority label: "Critical", "High", "Medium", or "Low"
    """
    if priority_score > 80:
        return "Critical"
    elif priority_score > 60:
        return "High"
    elif priority_score > 40:
        return "Medium"
    else:
        return "Low"

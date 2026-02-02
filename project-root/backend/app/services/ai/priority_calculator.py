"""
Priority Calculation Module

Calculates ticket priority scores based on category, urgency, and other factors.
Dynamically adapts to both predefined and AI-generated categories.
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


def get_dynamic_category_weight(category: str) -> int:
    """
    Get priority weight for a category, using heuristics for AI-generated categories.
    
    Args:
        category: Category name
        
    Returns:
        Priority weight (0-70)
    """
    # First check if it's a predefined category
    if category in CATEGORY_PRIORITY_WEIGHTS:
        return CATEGORY_PRIORITY_WEIGHTS[category]
    
    # For AI-generated categories, use keyword heuristics
    cat_lower = category.lower()
    
    # Security-related keywords get higher priority
    security_keywords = ['breach', 'malware', 'virus', 'security', 'vulnerability', 'hack', 'attack', 'ransomware']
    critical_keywords = ['backup', 'offline', 'down', 'critical', 'failed', 'hardware']
    high_keywords = ['patch', 'update', 'access', 'login', 'password', 'authentication']
    
    for keyword in security_keywords:
        if keyword in cat_lower:
            return 70
    
    for keyword in critical_keywords:
        if keyword in cat_lower:
            return 50
    
    for keyword in high_keywords:
        if keyword in cat_lower:
            return 35
    
    # Default priority for other categories
    return 30


def calculate_priority_score(
    text: str,
    category: str,
    semantic_scores: dict
) -> int:
    """
    Calculate dynamic priority score based on multiple factors.
    Optimized version with minimal logging overhead.
    
    Args:
        text: Ticket text
        category: Predicted category
        semantic_scores: Dictionary of semantic confidence scores
        
    Returns:
        Priority score (0-100)
    """
    # Start with category weight (most important factor)
    base = 10 + get_dynamic_category_weight(category)
    
    # Quick urgency check (avoid redundant lower() calls)
    text_lower = text.lower()
    base += sum(10 for w in URGENCY_KEYWORDS if w in text_lower)
    
    # Semantic confidence adjustment (scaled 0-100 to 0-10)
    base += semantic_scores.get(category, 0) // 10
    
    # Length adjustment (quick word count)
    base += min(len(text.split()) // WORDS_PER_LENGTH_UNIT, MAX_LENGTH_ADJUSTMENT)
    
    # Cap between min and max
    return max(MIN_PRIORITY_SCORE, min(base, MAX_PRIORITY_SCORE))


def calculate_priority_scores_batch(
    texts: list[str],
    categories: list[str],
    semantic_scores_list: list[dict]
) -> list[int]:
    """
    Calculate priority scores for multiple tickets at once.
    Much faster than calling calculate_priority_score in a loop.
    
    Args:
        texts: List of ticket texts
        categories: List of predicted categories
        semantic_scores_list: List of semantic score dictionaries
        
    Returns:
        List of priority scores
    """
    scores = []
    
    # Pre-compute category weights
    category_weights = {cat: get_dynamic_category_weight(cat) for cat in set(categories)}
    
    for text, category, semantic_scores in zip(texts, categories, semantic_scores_list):
        base = 10 + category_weights[category]
        text_lower = text.lower()
        base += sum(10 for w in URGENCY_KEYWORDS if w in text_lower)
        base += semantic_scores.get(category, 0) // 10
        base += min(len(text.split()) // WORDS_PER_LENGTH_UNIT, MAX_LENGTH_ADJUSTMENT)
        scores.append(max(MIN_PRIORITY_SCORE, min(base, MAX_PRIORITY_SCORE)))
    
    return scores


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

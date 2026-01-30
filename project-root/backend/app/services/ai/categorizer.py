"""
Category Prediction Module

Implements both keyword-based and semantic-based category prediction for tickets.
"""

import logging
from sentence_transformers import util
from .config import (
    CATEGORY_KEYWORDS,
    CATEGORY_EMBEDDINGS,
    MIN_KEYWORD_MATCHES,
    model
)
from .text_processor import preprocess_text

logger = logging.getLogger(__name__)


def predict_category_by_keywords(text: str) -> dict:
    """
    Predict category using keyword matching.
    
    Args:
        text: Ticket text to analyze
        
    Returns:
        Dictionary of category scores (higher = better match)
    """
    tokens = preprocess_text(text)
    scores = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in tokens)
        if score > 0:
            scores[category] = score
    
    return scores


def predict_category_by_semantic(text: str) -> tuple:
    """
    Predict category using semantic similarity with sentence embeddings.
    
    Args:
        text: Ticket text to analyze
        
    Returns:
        Tuple of (best_category, similarity_scores_dict)
    """
    import time
    
    # TIMING: model.encode() - expensive operation
    encode_start = time.time()
    ticket_embedding = model.encode(text, convert_to_tensor=True)
    encode_time = time.time() - encode_start
    logger.debug(f"[TIMING] model.encode() took {encode_time*1000:.2f}ms (text length: {len(text)})")
    
    # TIMING: cosine similarity computation
    similarities = {}
    sim_start = time.time()
    
    for category, cat_emb in CATEGORY_EMBEDDINGS.items():
        similarity = util.cos_sim(ticket_embedding, cat_emb).item()
        # Scale similarity from [-1, 1] to [0, 100]
        scaled = int(((similarity + 1) / 2) * 100)
        similarities[category] = scaled
    
    sim_time = time.time() - sim_start
    logger.debug(f"[TIMING] Cosine similarity computation took {sim_time*1000:.2f}ms ({len(CATEGORY_EMBEDDINGS)} categories)")
    
    # Return category with highest semantic similarity
    best_cat = max(similarities, key=similarities.get)
    total_time = encode_time + sim_time
    logger.debug(f"[TIMING] semantic prediction total: {total_time*1000:.2f}ms")
    
    return best_cat, similarities


def predict_category_hybrid(text: str) -> tuple:
    """
    Hybrid prediction: tries keywords first, falls back to semantic matching.
    
    Args:
        text: Ticket text to analyze
        
    Returns:
        Tuple of (predicted_category, method_used, confidence_scores)
        where method_used is "keyword" or "semantic"
    """
    keyword_scores = predict_category_by_keywords(text)
    semantic_best, semantic_scores = predict_category_by_semantic(text)
    
    # If keywords were confident, trust them
    if keyword_scores and max(keyword_scores.values()) >= MIN_KEYWORD_MATCHES:
        predicted = max(keyword_scores, key=keyword_scores.get)
        logger.debug(f"Using keyword prediction: {predicted} (score: {keyword_scores[predicted]})")
        return predicted, "keyword", semantic_scores
    
    # Otherwise fall back to semantic match
    logger.debug(f"Using semantic prediction: {semantic_best} (confidence: {semantic_scores[semantic_best]}%)")
    return semantic_best, "semantic", semantic_scores

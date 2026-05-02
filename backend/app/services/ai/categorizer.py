"""
Category Prediction Module

Implements both keyword-based and semantic-based category prediction for tickets.
"""

import logging
from sentence_transformers import util
import torch
from .config import (
    CATEGORY_KEYWORDS,
    CATEGORY_EMBEDDINGS,
    CATEGORY_LABELS,
    MIN_KEYWORD_MATCHES,
    model,
)
from .text_processor import normalize_text, preprocess_text
from .logging_config import perf_logger, metrics
from .embedding_cache import get_cache

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
    normalized_text = normalize_text(text)
    token_set = set(tokens)
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            normalized_keyword = normalize_text(keyword)
            if not normalized_keyword:
                continue
            if " " in normalized_keyword:
                score += int(normalized_keyword in normalized_text)
            else:
                score += int(normalized_keyword in token_set)
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

    if model is None or not CATEGORY_EMBEDDINGS:
        similarities = {category: 0 for category in CATEGORY_KEYWORDS}
        fallback_category = next(iter(CATEGORY_KEYWORDS))
        logger.warning(
            "Semantic classifier unavailable; using zero-confidence fallback for semantic prediction"
        )
        return fallback_category, similarities

    # TIMING: model.encode() - expensive operation
    encode_start = time.time()
    ticket_embedding = model.encode(text, convert_to_tensor=True)
    encode_time = time.time() - encode_start
    metrics.record_operation("model.encode", encode_time * 1000)
    perf_logger.debug(
        f"[TIMING] model.encode() took {encode_time * 1000:.2f}ms (text length: {len(text)})"
    )

    # TIMING: cosine similarity computation
    similarities = {}
    sim_start = time.time()

    for category, cat_emb in CATEGORY_EMBEDDINGS.items():
        similarity = util.cos_sim(ticket_embedding, cat_emb).item()
        # Scale similarity from [-1, 1] to [0, 100]
        scaled = int(((similarity + 1) / 2) * 100)
        similarities[category] = scaled

    sim_time = time.time() - sim_start
    metrics.record_operation("cosine_similarity", sim_time * 1000)
    perf_logger.debug(
        f"[TIMING] Cosine similarity computation took {sim_time * 1000:.2f}ms ({len(CATEGORY_EMBEDDINGS)} categories)"
    )

    # Return category with highest semantic similarity
    best_cat = max(similarities, key=similarities.get)
    total_time = encode_time + sim_time
    metrics.record_operation("semantic_prediction_total", total_time * 1000)
    perf_logger.debug(f"[TIMING] semantic prediction total: {total_time * 1000:.2f}ms")

    return best_cat, similarities


def predict_categories_batch(texts: list[str]) -> list[tuple]:
    """
    Predict categories for multiple tickets at once using batch processing.
    This is MUCH faster than processing tickets one-by-one.

    Args:
        texts: List of ticket texts to analyze

    Returns:
        List of tuples (category, method_used, similarity_scores) for each ticket
    """
    import time

    if not texts:
        return []

    if model is None or not CATEGORY_EMBEDDINGS:
        zero_scores = {category: 0 for category in CATEGORY_KEYWORDS}
        fallback_category = next(iter(CATEGORY_KEYWORDS))
        results = []
        for text in texts:
            keyword_scores = predict_category_by_keywords(text)
            if keyword_scores:
                predicted = max(keyword_scores, key=keyword_scores.get)
                method_used = "keyword_fallback"
            else:
                predicted = fallback_category
                method_used = "unclassified"
            results.append((predicted, method_used, dict(zero_scores)))
        return results

    batch_start = time.time()
    logger.debug(f"[BATCH] Processing {len(texts)} tickets in batch mode")

    # CHECK CACHE: Get cached embeddings and identify what needs encoding
    cache = get_cache()
    cache_start = time.time()
    cached_embeddings, indices_to_encode = cache.get_batch(texts)
    cache_time = time.time() - cache_start

    cache_hits = len(texts) - len(indices_to_encode)
    logger.debug(
        f"[CACHE] {cache_hits}/{len(texts)} cache hits ({cache_time * 1000:.2f}ms)"
    )

    # BATCH ENCODING: Only encode texts that aren't cached
    if indices_to_encode:
        encode_start = time.time()
        texts_to_encode = [texts[i] for i in indices_to_encode]

        new_embeddings = model.encode(
            texts_to_encode,
            convert_to_tensor=True,
            batch_size=16,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        encode_time = time.time() - encode_start
        logger.debug(
            f"[BATCH] Encoded {len(texts_to_encode)} new tickets in {encode_time * 1000:.2f}ms"
        )

        # Store in cache
        cache.put_batch(texts_to_encode, new_embeddings)

        # Merge cached and new embeddings
        new_idx = 0
        for i in range(len(texts)):
            if cached_embeddings[i] is None:
                cached_embeddings[i] = new_embeddings[new_idx]
                new_idx += 1

    # Stack all embeddings into tensor
    ticket_embeddings = torch.stack(cached_embeddings)

    # Prepare category embeddings as tensor (cache this for reuse)
    categories = list(CATEGORY_EMBEDDINGS.keys())
    category_embeddings_tensor = torch.stack(
        [CATEGORY_EMBEDDINGS[cat] for cat in categories]
    )

    # BATCH SIMILARITY: Compute all similarities at once
    sim_start = time.time()
    similarities_matrix = util.cos_sim(ticket_embeddings, category_embeddings_tensor)
    sim_time = time.time() - sim_start
    logger.debug(f"[BATCH] Computed similarities in {sim_time * 1000:.2f}ms")

    # Process results for each ticket
    results = []
    for i, text in enumerate(texts):
        # Get similarities for this ticket (already computed)
        ticket_similarities = similarities_matrix[i]

        # Convert to dictionary and scale
        similarities = {}
        for j, category in enumerate(categories):
            similarity = ticket_similarities[j].item()
            scaled = int(((similarity + 1) / 2) * 100)
            similarities[category] = scaled

        # Get best semantic category
        best_cat = categories[torch.argmax(ticket_similarities).item()]

        # Quick keyword check (only preprocess if needed)
        keyword_scores = predict_category_by_keywords(text)

        # Hybrid decision
        if keyword_scores:
            best_keyword = max(keyword_scores, key=keyword_scores.get)
            if keyword_scores[best_keyword] >= MIN_KEYWORD_MATCHES:
                final_category = best_keyword
                method_used = "keyword"
            else:
                final_category = best_cat
                method_used = "semantic"
        else:
            final_category = best_cat
            method_used = "semantic"

        results.append((final_category, method_used, similarities))

    batch_time = time.time() - batch_start
    logger.debug(
        f"[BATCH] Total batch processing: {batch_time * 1000:.2f}ms ({batch_time / len(texts) * 1000:.2f}ms per ticket)"
    )
    logger.info(
        f"[BATCH] Processed {len(texts)} tickets in {batch_time:.3f}s (avg {batch_time / len(texts):.4f}s per ticket)"
    )

    return results


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

    if model is None or not CATEGORY_EMBEDDINGS:
        zero_scores = {category: 0 for category in CATEGORY_KEYWORDS}
        if keyword_scores:
            predicted = max(keyword_scores, key=keyword_scores.get)
            logger.debug(
                "Semantic classifier unavailable, using keyword fallback prediction: %s",
                predicted,
            )
            return predicted, "keyword_fallback", zero_scores

        fallback_category = next(iter(CATEGORY_KEYWORDS))
        logger.debug(
            "Semantic classifier unavailable and no keywords matched, returning fallback category: %s",
            fallback_category,
        )
        return fallback_category, "unclassified", zero_scores

    semantic_best, semantic_scores = predict_category_by_semantic(text)

    # If keywords were confident, trust them
    if keyword_scores and max(keyword_scores.values()) >= MIN_KEYWORD_MATCHES:
        predicted = max(keyword_scores, key=keyword_scores.get)
        logger.debug(
            f"Using keyword prediction: {predicted} (score: {keyword_scores[predicted]})"
        )
        return predicted, "keyword", semantic_scores

    # Otherwise fall back to semantic match
    logger.debug(
        f"Using semantic prediction: {semantic_best} (confidence: {semantic_scores[semantic_best]}%)"
    )
    return semantic_best, "semantic", semantic_scores


def list_available_categories() -> list[dict[str, str]]:
    """Expose the configured category list for API consumers."""
    return [
        {"key": category_key, "label": CATEGORY_LABELS[category_key]}
        for category_key in CATEGORY_LABELS
    ]

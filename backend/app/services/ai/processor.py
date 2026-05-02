"""Ticket classification orchestrator for the live AI request path."""

import time

from .categorizer import predict_category_hybrid
from .logging_config import logger as base_logger, metrics, perf_logger
from .priority_calculator import calculate_priority_score, get_priority_label
from .text_processor import extract_ticket_text

logger = base_logger.getChild("processor")


def process_ticket(ticket_input: dict | str) -> dict:
    """Analyze a ticket and return the AI metadata used by the API."""
    ticket_start = time.time()

    if isinstance(ticket_input, dict):
        extract_start = time.time()
        ticket_text = extract_ticket_text(ticket_input)
        extract_time = time.time() - extract_start
        metrics.record_operation("extract_ticket_text", extract_time * 1000)
        perf_logger.debug(
            "[TIMING] extract_ticket_text() took %.2fms",
            extract_time * 1000,
        )
        ticket_metadata = ticket_input
    else:
        ticket_text = ticket_input
        ticket_metadata = {}

    if not ticket_text:
        raise ValueError("Ticket text could not be extracted from the supplied input")

    pred_start = time.time()
    category, method_used, semantic_scores = predict_category_hybrid(ticket_text)
    pred_time = time.time() - pred_start
    metrics.record_operation("predict_category_hybrid", pred_time * 1000)
    perf_logger.debug(
        "[TIMING] predict_category_hybrid() took %.2fms",
        pred_time * 1000,
    )

    priority_score = calculate_priority_score(ticket_text, category, semantic_scores)
    priority_label = get_priority_label(priority_score)

    total_time = time.time() - ticket_start
    metrics.record_operation("process_ticket_total", total_time * 1000)
    logger.info(
        "Processed ticket '%s' in %.2fms - Category: %s, Priority: %s",
        str(ticket_metadata.get("title", "No title provided"))[:50],
        total_time * 1000,
        category,
        priority_label,
    )

    return {
        "category": category,
        "confidence": semantic_scores.get(category, 0),
        "priority": priority_label,
        "priority_score": priority_score,
        "method": method_used,
    }


def categorise_ticket(ticket_data: dict) -> dict:
    """Backwards-compatible alias for the live AI ticket analysis path."""
    try:
        logger.debug("categorise_ticket called with data: %s", ticket_data)
        result = process_ticket(ticket_data)
        logger.debug("categorise_ticket returning: %s", result)
        return result
    except Exception as error:
        logger.error("Error in categorise_ticket: %s", str(error), exc_info=True)
        return {
            "category": "unknown",
            "confidence": 0,
            "priority": "Low",
            "priority_level": "Low",
            "priority_score": 0,
            "method": "error",
            "error": str(error),
        }

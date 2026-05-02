"""Text normalization helpers for ticket classification."""

import logging
import re
import time

from .config import MIN_TOKEN_LENGTH
from .logging_config import metrics, perf_logger

logger = logging.getLogger(__name__)

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "will",
    "with",
}


def normalize_text(text: str | None) -> str:
    """Normalize free text into a lowercase token-friendly string."""
    if not text:
        return ""
    return " ".join(TOKEN_PATTERN.findall(text.lower()))


def preprocess_text(text: str) -> list[str]:
    """Tokenize text using a lightweight regex-based normalizer."""
    start_time = time.time()
    normalized_text = normalize_text(text)
    tokens = [
        token
        for token in normalized_text.split()
        if token not in STOP_WORDS and len(token) > MIN_TOKEN_LENGTH
    ]

    duration = time.time() - start_time
    metrics.record_operation("text_normalization", duration * 1000)
    if duration > 0.05:
        perf_logger.debug(
            "[TIMING] normalize_text() took %.2fms for text length %s",
            duration * 1000,
            len(text),
        )

    return tokens


def extract_ticket_text(ticket_item) -> str:
    """Extract the ticket fields that should influence AI categorization."""
    if isinstance(ticket_item, str):
        return ticket_item

    if not isinstance(ticket_item, dict):
        return ""

    if "text" in ticket_item:
        return str(ticket_item["text"])
    if "input_text" in ticket_item:
        return str(ticket_item["input_text"])

    parts: list[str] = []
    for field_name in (
        "title",
        "description",
        "issue_type",
        "sub_issue_type",
        "queue",
        "source",
    ):
        value = ticket_item.get(field_name)
        if value:
            parts.append(str(value))

    return " ".join(parts)

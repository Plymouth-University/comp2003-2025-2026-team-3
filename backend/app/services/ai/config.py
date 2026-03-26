"""Configuration and shared runtime state for the AI ticket classifier."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

from .logging_config import setup_logging

logger = setup_logging().getChild("config")

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
CATEGORY_CONFIG_PATH = Path(
    os.getenv("AI_CATEGORY_CONFIG_PATH", DATA_DIR / "ticket_categories.json")
)
EMBEDDING_MODEL_NAME = os.getenv("AI_EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
EMBEDDING_MODEL_LOCAL_ONLY = (
    os.getenv("AI_EMBEDDING_MODEL_LOCAL_ONLY", "true").strip().lower() != "false"
)


@dataclass(frozen=True)
class CategoryDefinition:
    """Runtime category definition loaded from JSON configuration."""

    key: str
    label: str
    description: str
    keywords: tuple[str, ...]
    priority_weight: int


def load_category_definitions() -> tuple[CategoryDefinition, ...]:
    """Load category definitions from the configured JSON file."""
    if not CATEGORY_CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"AI category configuration file not found: {CATEGORY_CONFIG_PATH}"
        )

    with CATEGORY_CONFIG_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    raw_categories = payload.get("categories")
    if not isinstance(raw_categories, list) or not raw_categories:
        raise ValueError(
            f"AI category configuration at {CATEGORY_CONFIG_PATH} must contain a non-empty 'categories' list"
        )

    definitions: list[CategoryDefinition] = []
    for index, raw_category in enumerate(raw_categories, start=1):
        key = str(raw_category["key"]).strip()
        label = str(raw_category["label"]).strip()
        description = str(raw_category["description"]).strip()
        raw_keywords = raw_category.get("keywords", [])
        if not isinstance(raw_keywords, list) or not raw_keywords:
            raise ValueError(f"Category #{index} ({key}) must define at least one keyword")

        keywords = tuple(
            str(keyword).strip().lower()
            for keyword in raw_keywords
            if str(keyword).strip()
        )
        if not keywords:
            raise ValueError(
                f"Category #{index} ({key}) must define at least one non-empty keyword"
            )

        definitions.append(
            CategoryDefinition(
                key=key,
                label=label,
                description=description,
                keywords=keywords,
                priority_weight=int(raw_category.get("priority_weight", 30)),
            )
        )

    logger.info(
        "Loaded %s AI ticket categories from %s",
        len(definitions),
        CATEGORY_CONFIG_PATH,
    )
    return tuple(definitions)


def load_embedding_model() -> SentenceTransformer | None:
    """Load the semantic model if it is available in the deployment environment."""
    try:
        embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME,
            local_files_only=EMBEDDING_MODEL_LOCAL_ONLY,
        )
        embedding_model = embedding_model.to("cpu")
        if hasattr(torch, "set_num_threads"):
            torch.set_num_threads(4)
        return embedding_model
    except Exception as error:
        logger.warning(
            "Semantic model '%s' could not be loaded. Falling back to keyword-only classification until the model is provisioned. Error: %s",
            EMBEDDING_MODEL_NAME,
            error,
        )
        return None


model = load_embedding_model()


CATEGORY_DEFINITIONS = load_category_definitions()
CATEGORY_LABELS = {category.key: category.label for category in CATEGORY_DEFINITIONS}
CATEGORY_KEYWORDS = {category.key: category.keywords for category in CATEGORY_DEFINITIONS}
CATEGORY_PRIORITY_WEIGHTS = {
    category.key: category.priority_weight for category in CATEGORY_DEFINITIONS
}
CATEGORY_EMBEDDINGS = (
    {
        category.key: model.encode(
            f"{category.label}. {category.description}",
            convert_to_tensor=True,
        )
        for category in CATEGORY_DEFINITIONS
    }
    if model is not None
    else {}
)

SLOW_OPERATION_THRESHOLD = 0.05
MIN_KEYWORD_MATCHES = 2
MAX_PRIORITY_SCORE = 100
MIN_PRIORITY_SCORE = 0

URGENCY_KEYWORDS = ["urgent", "immediately", "asap", "critical", "priority"]

MIN_TOKEN_LENGTH = 2
MAX_LENGTH_ADJUSTMENT = 10
WORDS_PER_LENGTH_UNIT = 20

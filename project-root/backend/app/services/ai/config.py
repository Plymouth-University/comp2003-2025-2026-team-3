"""
AI Service Configuration Module

Centralized configuration for all AI-related constants, models, and paths.
Dynamically loads categories from generated_categories.json if available.
Automatically generates categories on startup if they don't exist.
"""

from sentence_transformers import SentenceTransformer
import logging
import json
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

# ============================================================================
# MODEL INITIALIZATION
# ============================================================================

# Initialize semantic model (cached after first load)
model = SentenceTransformer('all-MiniLM-L6-v2')

# ============================================================================
# DYNAMIC CATEGORY LOADING
# ============================================================================

def load_generated_categories():
    """
    Load dynamically generated categories from generated_categories.json.
    Generates categories if they don't exist.
    Falls back to default categories if generation fails.
    
    Returns:
        Tuple of (category_descriptions, category_keywords)
    """
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    categories_file = data_dir / "generated_categories.json"
    tickets_file = data_dir / "tickets.json"
    
    # Auto-generate categories if they don't exist
    if not categories_file.exists() and tickets_file.exists():
        logger.info("No generated categories found. Auto-generating from ticket data...")
        try:
            from .category_generator import generate_categories_from_tickets
            generate_categories_from_tickets(tickets_file, categories_file, force_regenerate=False)
        except Exception as e:
            logger.warning(f"Failed to auto-generate categories: {e}")
    
    # Try to load generated categories
    if categories_file.exists():
        try:
            logger.info(f"Loading dynamically generated categories from {categories_file}")
            with open(categories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Build category descriptions from generated data
            category_descriptions = {}
            category_keywords = {}
            
            for category in data.get('categories', []):
                cat_name = category['category_name']
                category_descriptions[cat_name] = category['description']
                # Use common themes as keywords
                category_keywords[cat_name] = category.get('common_themes', [])[:10]
            
            logger.info(f"✓ Loaded {len(category_descriptions)} dynamically generated categories")
            return category_descriptions, category_keywords
            
        except Exception as e:
            logger.warning(f"Failed to load generated categories: {e}. Using defaults.")
    else:
        logger.info("No generated categories available. Using default categories.")
    
    # Fallback to default categories
    logger.info("Using default fallback categories")
    default_descriptions = {
        "malware": "Device infected with malware, virus, trojan or ransomware.",
        "phishing": "User received fraudulent or deceptive emails asking for credentials.",
        "network": "Network outage, slow connectivity, servers unreachable.",
        "access": "Login problems, password resets, authentication issues, 2FA failures.",
        "data_breach": "Sensitive information leaked or exposed without authorisation."
    }
    
    default_keywords = {
        "malware": ["malware", "virus", "infect", "trojan", "ransomware"],
        "phishing": ["phish", "scam", "fraud", "fake", "login", "suspicious", "email"],
        "network": ["network", "offline", "unreachable", "latency", "dns"],
        "access": ["password", "login", "2fa", "authentication", "lock"],
        "data_breach": ["breach", "leak", "compromise", "expose"]
    }
    
    return default_descriptions, default_keywords


# Load categories (either generated or default)
CATEGORY_DESCRIPTIONS, CATEGORY_KEYWORDS = load_generated_categories()

# Build category embeddings from loaded categories
CATEGORY_EMBEDDINGS = {
    cat: model.encode(desc, convert_to_tensor=True)
    for cat, desc in CATEGORY_DESCRIPTIONS.items()
}

# Company names for detection
COMPANY_NAMES = {
    "association a",
    "business b",
    "company c",
    "division d",
    "employer e",
    "foundation f",
    "gym g",
    "hotel h"
}

# ============================================================================
# PRIORITY CONFIGURATION
# ============================================================================

# Priority weights for different levels
PRIORITY_WEIGHTS = {
    "critical": 90,
    "high": 70,
    "medium": 50,
    "low": 20
}

# Category weights for priority calculation (dynamic/generated categories use heuristics)
CATEGORY_PRIORITY_WEIGHTS = {
    "data_breach": 70,
    "malware": 60,
    "phishing": 35,
    "network": 30,
    "access": 20,
}

# Urgency keywords
URGENCY_KEYWORDS = ["urgent", "immediately", "asap", "critical", "priority"]

# ============================================================================
# FILE STORAGE PATHS
# ============================================================================

# Base path for processed ticket storage
TICKETS_BASE_PATH = r"c:\secops_autotask_prototype_scaffold\backend\data\Processed Tickets"

# Input path for unprocessed tickets
INPUT_TICKETS_PATH = r"c:\secops_autotask_prototype_scaffold\backend\data\Unprocessed Tickets"

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# Timing threshold (in seconds) for logging slow operations
SLOW_OPERATION_THRESHOLD = 0.05

# Minimum keyword matches to trust keyword-based prediction
MIN_KEYWORD_MATCHES = 2

# Maximum priority score
MAX_PRIORITY_SCORE = 100

# Minimum priority score
MIN_PRIORITY_SCORE = 0

# ============================================================================
# TEXT PROCESSING
# ============================================================================

# Minimum token length to keep in preprocessing
MIN_TOKEN_LENGTH = 2

# Maximum length adjustment for priority (per 20 words)
MAX_LENGTH_ADJUSTMENT = 10
WORDS_PER_LENGTH_UNIT = 20

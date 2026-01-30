"""
AI Service Configuration Module

Centralized configuration for all AI-related constants, models, and paths.
"""

from sentence_transformers import SentenceTransformer
import logging

# Setup logging
logger = logging.getLogger(__name__)

# ============================================================================
# MODEL INITIALIZATION
# ============================================================================

# Initialize semantic model (cached after first load)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Category descriptions for semantic embedding
CATEGORY_DESCRIPTIONS = {
    "malware": "Device infected with malware, virus, trojan or ransomware.",
    "phishing": "User received fraudulent or deceptive emails asking for credentials.",
    "network": "Network outage, slow connectivity, servers unreachable.",
    "access": "Login problems, password resets, authentication issues, 2FA failures.",
    "data_breach": "Sensitive information leaked or exposed without authorisation."
}

# Build category embeddings once at startup
CATEGORY_EMBEDDINGS = {
    cat: model.encode(desc, convert_to_tensor=True)
    for cat, desc in CATEGORY_DESCRIPTIONS.items()
}

# ============================================================================
# KEYWORDS AND DETECTION
# ============================================================================

# Keywords for keyword-based category prediction
CATEGORY_KEYWORDS = {
    "malware": ["malware", "virus", "infect", "trojan", "ransomware"],
    "phishing": ["phish", "scam", "fraud", "fake", "login", "suspicious", "email"],
    "network": ["network", "offline", "unreachable", "latency", "dns"],
    "access": ["password", "login", "2fa", "authentication", "lock"],
    "data_breach": ["breach", "leak", "compromise", "expose"]
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

# Category weights for priority calculation
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

# AI Service Architecture

This document describes the refactored AI service structure within the backend services.

## Overview

The AI service has been reorganized from a monolithic `ai_categoriser.py` into a modular, scalable structure. This allows for:

- **Better separation of concerns**: Each module handles a specific responsibility
- **Easier testing**: Individual modules can be tested in isolation
- **Improved maintainability**: Changes to one area don't affect others
- **Future scalability**: Easy to add new services beyond AI in the `services/` folder
- **Code reusability**: Modules can be imported and used independently

## Directory Structure

```
backend/app/services/
├── ai/                           # AI Service (specialized service)
│   ├── __init__.py              # Package exports
│   ├── config.py                # Constants, models, and configurations
│   ├── text_processor.py        # Text preprocessing and extraction
│   ├── categorizer.py           # Category prediction (keyword + semantic)
│   ├── priority_calculator.py   # Priority scoring logic
│   ├── description_generator.py # AI-powered description generation
│   ├── storage.py               # JSON storage and I/O operations
│   └── processor.py             # Main orchestrator (coordinates all modules)
├── ai_categoriser.py            # Backwards compatibility shim
└── __init__.py                  # Services package init
```

## Module Breakdown

### 1. **config.py** - Configuration & Constants
Centralized configuration for all AI operations:
- Model initialization (SentenceTransformer)
- Category definitions and keywords
- Priority weights and thresholds
- File paths
- Performance tuning parameters

**Use when:** You need to update constants, adjust weights, or change paths.

### 2. **text_processor.py** - Text Processing
Handles text preprocessing, cleaning, and extraction:
- `preprocess_text()`: Tokenization and lemmatization using spaCy
- `extract_ticket_text()`: Combines text from multiple formats
- `detect_company()`: Identifies company names in text

**Use when:** You need to extract or process ticket text data.

### 3. **categorizer.py** - Category Prediction
Implements two prediction strategies:
- `predict_category_by_keywords()`: Keyword-based matching
- `predict_category_by_semantic()`: Semantic similarity using embeddings
- `predict_category_hybrid()`: Hybrid approach (keywords first, falls back to semantic)

**Use when:** You need to categorize a ticket.

### 4. **priority_calculator.py** - Priority Scoring
Calculates ticket priority based on multiple factors:
- `calculate_priority_score()`: Multi-factor scoring
- `get_priority_label()`: Converts score to label (Critical/High/Medium/Low)

Factors considered:
- Category weight
- Urgency keywords in text
- Semantic confidence
- Ticket length

**Use when:** You need to assign a priority to a ticket.

### 5. **description_generator.py** - AI Description Generation
Generates comprehensive descriptions with remediation suggestions:
- `generate_ai_description()`: Creates AI-powered descriptions
- `_get_issue_remediation()`: Provides issue-specific solutions

**Use when:** You need to generate helpful descriptions for tickets.

### 6. **storage.py** - File Storage Operations
Manages ticket file I/O:
- `save_ticket_to_json()`: Saves organized by category/priority/company
- `get_input_tickets()`: Lists unprocessed ticket files
- `load_tickets_from_file()`: Loads tickets from JSON/TXT

**Use when:** You need to read/write ticket data to disk.

### 7. **processor.py** - Main Orchestrator
Coordinates all modules in a complete workflow:
- `process_ticket()`: End-to-end ticket processing
- `process_input_tickets()`: Batch processing
- `categorise_ticket()`: Backwards-compatible alias
- `_print_ticket_summary()`: Formats output

**Use when:** You need to process complete tickets.

## Usage

### New Code (Recommended)
```python
from app.services.ai import process_ticket, categorise_ticket

# Process a single ticket
result = process_ticket(ticket_data)

# Or import specific modules
from app.services.ai.categorizer import predict_category_hybrid
from app.services.ai.priority_calculator import calculate_priority_score

category, method, scores = predict_category_hybrid(text)
priority = calculate_priority_score(text, category, scores)
```

### Legacy Code (Still Supported)
```python
# Old imports still work for backwards compatibility
from app.services.ai_categoriser import categorise_ticket, process_ticket

result = process_ticket(ticket_data)
```

## Adding New AI Services

### To add a new feature within AI:
1. Create a new module in `services/ai/`
2. Import in `services/ai/processor.py` if needed
3. Export from `services/ai/__init__.py`

### To add a new service (beyond AI):
1. Create a new folder: `services/new_service/`
2. Structure it similarly with:
   - `__init__.py` (exports)
   - `config.py` (configuration)
   - Module files
   - `processor.py` or equivalent main coordinator
3. Update `services/__init__.py`

## Performance Considerations

- **Text preprocessing (spaCy)**: ~5-20ms per ticket
- **Semantic embedding (SentenceTransformer)**: ~50-100ms per ticket
- **Hybrid prediction**: ~60-120ms per ticket (keyboard first, fast-path typical)

Timing is logged with `[TIMING]` prefix when enabled at DEBUG level.

## Testing

Each module can be tested independently:

```python
# Test text processor
from app.services.ai.text_processor import preprocess_text
tokens = preprocess_text("Sample ticket text")

# Test categorizer
from app.services.ai.categorizer import predict_category_hybrid
cat, method, scores = predict_category_hybrid("Network outage reported")

# Test priority
from app.services.ai.priority_calculator import calculate_priority_score
priority = calculate_priority_score(text, "network", scores)
```

## Configuration

Global settings are in `config.py`. Key configurations:

```python
# Update weights to change priority calculation
CATEGORY_PRIORITY_WEIGHTS = {
    "data_breach": 70,  # Increase for higher impact
    "malware": 60,
    ...
}

# Change keyword confidence threshold
MIN_KEYWORD_MATCHES = 2

# Adjust paths for your environment
TICKETS_BASE_PATH = r"your\path\here"
INPUT_TICKETS_PATH = r"your\path\here"
```

## Error Handling

All modules include proper error handling:
- Functions return `None` or empty defaults on error
- Errors are logged with context
- Falls back gracefully (e.g., semantic prediction if keywords fail)

## Future Enhancements

- [ ] Add batch processing optimizations
- [ ] Implement caching for embeddings
- [ ] Add model versioning/updates
- [ ] Integrate with external AI APIs
- [ ] Add anomaly detection module
- [ ] Add feedback loop for model improvement
- [ ] Add webhook/async processing for long-running tasks

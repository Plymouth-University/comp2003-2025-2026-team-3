# Migration Guide: AI Categoriser Refactoring

## Overview

The AI categorisation logic has been refactored from a single monolithic file into a modular service structure. This document helps you understand where things have moved and how to update your imports.

## Quick Reference

### Finding Moved Functions

#### Text Processing
```python
# OLD
from app.services.ai_categoriser import preprocess_text, extract_ticket_text, detect_company

# NEW (Recommended)
from app.services.ai.text_processor import preprocess_text, extract_ticket_text, detect_company

# Also works (backwards compatible)
from app.services.ai_categoriser import preprocess_text, extract_ticket_text, detect_company
```

#### Category Prediction
```python
# OLD
from app.services.ai_categoriser import predict_category, semantic_category_prediction, hybrid_category_prediction

# NEW (Recommended)
from app.services.ai.categorizer import (
    predict_category_by_keywords,      # Renamed from predict_category
    predict_category_by_semantic,      # Renamed from semantic_category_prediction
    predict_category_hybrid            # Same name
)

# Legacy aliases still work
from app.services.ai_categoriser import predict_category, semantic_category_prediction, hybrid_category_prediction
```

#### Priority Calculation
```python
# OLD
from app.services.ai_categoriser import calculate_dynamic_priority, get_priority_label

# NEW (Recommended)
from app.services.ai.priority_calculator import (
    calculate_priority_score,      # Renamed from calculate_dynamic_priority
    get_priority_label
)

# Legacy aliases still work
from app.services.ai_categoriser import calculate_dynamic_priority, get_priority_label
```

#### Main Processing
```python
# OLD
from app.services.ai_categoriser import process_ticket, categorise_ticket, process_input_tickets

# NEW (Recommended)
from app.services.ai import process_ticket, categorise_ticket, process_input_tickets

# Also works (backwards compatible)
from app.services.ai_categoriser import process_ticket, categorise_ticket, process_input_tickets
```

#### Storage Operations
```python
# OLD
from app.services.ai_categoriser import save_ticket_to_json, get_input_tickets

# NEW (Recommended)
from app.services.ai.storage import save_ticket_to_json, get_input_tickets, load_tickets_from_file

# Legacy imports still work
from app.services.ai_categoriser import save_ticket_to_json, get_input_tickets
```

#### Configuration
```python
# OLD
from app.services.ai_categoriser import (
    CATEGORY_KEYWORDS, CATEGORY_DESCRIPTIONS, CATEGORY_EMBEDDINGS,
    PRIORITY_WEIGHTS, COMPANY_NAMES, TICKETS_BASE_PATH, INPUT_TICKETS_PATH
)

# NEW (Recommended)
from app.services.ai.config import (
    CATEGORY_KEYWORDS,
    CATEGORY_DESCRIPTIONS,
    CATEGORY_EMBEDDINGS,
    PRIORITY_WEIGHTS,
    COMPANY_NAMES,
    TICKETS_BASE_PATH,
    INPUT_TICKETS_PATH,
)

# Legacy imports still work
from app.services.ai_categoriser import (
    CATEGORY_KEYWORDS, CATEGORY_DESCRIPTIONS, CATEGORY_EMBEDDINGS,
    PRIORITY_WEIGHTS, COMPANY_NAMES, TICKETS_BASE_PATH, INPUT_TICKETS_PATH
)
```

## Migration Timeline

### Immediately (No Changes Required)
Your existing code continues to work without any changes.

### Phase 1: Update to New Locations (Recommended)
Update imports to use new module structure:
```python
# Before
from app.services.ai_categoriser import process_ticket, categorise_ticket

# After
from app.services.ai import process_ticket, categorise_ticket
```

### Phase 2: Use Specific Modules (Optional)
For better code organization, import directly from the module you need:
```python
from app.services.ai.processor import process_ticket
from app.services.ai.categorizer import predict_category_hybrid
from app.services.ai.priority_calculator import calculate_priority_score
```

### Phase 3: Deprecate Compatibility Layer (Future)
Once all code is migrated, the `ai_categoriser.py` file can be deprecated and eventually removed (if desired).

## Function Name Changes

Some functions have been renamed for clarity. Legacy aliases are provided for backwards compatibility:

| Old Name | New Name | Module | Status |
|---|---|---|---|
| `predict_category` | `predict_category_by_keywords` | categorizer.py | Alias provided |
| `semantic_category_prediction` | `predict_category_by_semantic` | categorizer.py | Alias provided |
| `hybrid_category_prediction` | `predict_category_hybrid` | categorizer.py | Alias provided |
| `calculate_dynamic_priority` | `calculate_priority_score` | priority_calculator.py | Alias provided |

## Example: Complete Migration

### Before (Old Style)
```python
from app.services.ai_categoriser import (
    extract_ticket_text,
    hybrid_category_prediction,
    calculate_dynamic_priority,
    get_priority_label,
    save_ticket_to_json,
    detect_company
)

def process_my_ticket(ticket_data):
    text = extract_ticket_text(ticket_data)
    category, method, scores = hybrid_category_prediction(text)
    priority = calculate_dynamic_priority(text, category, scores)
    label = get_priority_label(priority)
    companies = detect_company(text)
    
    save_ticket_to_json(ticket_data, category, label, companies)
    return {"category": category, "priority": label}
```

### After (New Style)
```python
# Option A: Use the main entry point (recommended for simplicity)
from app.services.ai import process_ticket

def process_my_ticket(ticket_data):
    return process_ticket(ticket_data)

# Option B: Use specific modules (recommended for clarity)
from app.services.ai.text_processor import extract_ticket_text, detect_company
from app.services.ai.categorizer import predict_category_hybrid
from app.services.ai.priority_calculator import calculate_priority_score, get_priority_label
from app.services.ai.storage import save_ticket_to_json

def process_my_ticket(ticket_data):
    text = extract_ticket_text(ticket_data)
    category, method, scores = predict_category_hybrid(text)
    priority = calculate_priority_score(text, category, scores)
    label = get_priority_label(priority)
    companies = detect_company(text)
    
    save_ticket_to_json(ticket_data, category, label, companies)
    return {"category": category, "priority": label}
```

## Checking Your Code

To find all instances of old imports in your codebase:

```bash
# Search for old imports
grep -r "from app.services.ai_categoriser import" .
grep -r "import app.services.ai_categoriser" .
```

Then update each file to use the new locations.

## Troubleshooting

### Import Error: "No module named 'app.services.ai'"
Make sure you're running from the project root and the Python path includes `backend/`.

### Function Not Found
1. Check the migration guide above
2. Make sure you're importing from the correct new module
3. The old location still works for backwards compatibility

### Type Hints Not Working
The refactored code includes type hints. If your IDE doesn't recognize them:
1. Make sure you have Pylance or similar installed
2. Configure your Python path correctly
3. Restart your IDE

## Support

If you encounter any issues during migration:
1. Check the [AI Service README](./backend/app/services/ai/README.md)
2. Review the module docstrings in the new files
3. The old imports still work while you transition

## Summary

| Aspect | Status |
|---|---|
| Backwards Compatibility | ✅ Fully maintained |
| Migration Required | ❌ No (but recommended) |
| Breaking Changes | ❌ None |
| Timeline | Whenever convenient |
| Effort Level | Low (just update imports) |

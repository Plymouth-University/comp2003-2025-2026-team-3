# Dynamic AI Category System

The backend now automatically generates and uses AI-discovered categories from your ticket data.

## How It Works

**Categories are generated automatically when the backend starts!**

When you run:
```powershell
cd backend
uvicorn app.main:app --reload
```

The system automatically:
1. ✅ Checks if `data/generated_categories.json` exists
2. ✅ If missing, generates categories from `data/tickets.json` using AI clustering
3. ✅ Loads categories into memory
4. ✅ Uses them for all ticket categorization

**No manual steps required!**

## What Gets Generated

- **Optimal number of categories** (4-12, determined by silhouette analysis)
- **Category names** based on common keywords in each cluster
- **Descriptions** summarizing what each category covers
- **Keywords** for faster categorization

## Category File Location

Generated categories are saved to:
```
backend/data/generated_categories.json
```

## Forcing Regeneration

To regenerate categories with updated ticket data:

```powershell
# Option 1: Delete and restart
Remove-Item backend/data/generated_categories.json
uvicorn app.main:app --reload

# Option 2: Run standalone script (for debugging)
python backend/predict_categories.py
```

## Fallback Behavior

If category generation fails:
- System falls back to default hardcoded categories
- Backend still works normally
- Check logs for generation errors

## Benefits

✅ **Zero configuration** - works out of the box
✅ **Data-driven** - categories match your actual tickets  
✅ **Automatic updates** - delete file to regenerate with new data
✅ **Smart priority** - priority calculation adapts to category keywords
✅ **API compatible** - `/api/categories` returns generated categories

## Technical Details

**Generation Process:**
1. Load all tickets from `tickets.json`
2. Generate AI embeddings for each ticket
3. Use K-means clustering to find natural groupings
4. Analyze each cluster for common themes/keywords
5. Generate descriptive category names
6. Save to `generated_categories.json`

**Files Modified:**
- `app/services/ai/config.py` - Auto-generates and loads categories
- `app/services/ai/category_generator.py` - Generation logic
- `app/services/ai/priority_calculator.py` - Dynamic priority weights
- `app/main.py` - Returns generated categories in API

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .providers.fake_autotask import FakeAutotaskProvider
from .services.ai_categoriser import categorise_ticket
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="SecOps Autotask Prototype API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

provider = FakeAutotaskProvider()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api/categories")
def categories():
    return {"items": [{"key": k, "label": k} for k in [
        "Email blocked/held",
        "Backup failed",
        "Backup suspended",
        "Hardware offline",
        "Patching vulnerabilities",
        "Patch failed",
    ]]}

@app.get("/api/tickets")
def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    limit: int = Query(100, ge=1, le=500),
):
    try:
        logger.debug(f"list_tickets called with status={status}, priority={priority}, category={category}, limit={limit}")
        tickets = provider.get_tickets()
        logger.debug(f"Retrieved {len(tickets)} tickets from provider")
        
        if status:
            tickets = [t for t in tickets if t.status == status]
            logger.debug(f"Filtered to {len(tickets)} tickets by status={status}")
        if priority:
            tickets = [t for t in tickets if t.priority == priority]
            logger.debug(f"Filtered to {len(tickets)} tickets by priority={priority}")

        enriched = []
        for i, t in enumerate(tickets[:limit]):
            try:
                logger.debug(f"Processing ticket {i+1}/{len(tickets[:limit])}: {t.ticket_number}")
                ai = categorise_ticket({"title": t.title, "description": t.description})
                row = t.model_dump()
                row["ai"] = ai
                enriched.append(row)
                logger.debug(f"Successfully categorized ticket {t.ticket_number}")
            except Exception as e:
                logger.error(f"Error categorizing ticket {t.ticket_number}: {str(e)}", exc_info=True)
                # Return ticket without AI categorization on error
                row = t.model_dump()
                row["ai"] = {"category": "unknown", "confidence": 0}
                enriched.append(row)

        if category:
            enriched = [t for t in enriched if t["ai"]["category"] == category]
            logger.debug(f"Filtered to {len(enriched)} tickets by category={category}")

        logger.info(f"Returning {len(enriched)} enriched tickets")
        return {"items": enriched, "count": len(enriched)}
    except Exception as e:
        logger.error(f"Error in list_tickets: {str(e)}", exc_info=True)
        return {"items": [], "count": 0, "error": str(e)}

@app.get("/api/tickets/{autotask_ticket_id}")
def get_ticket(autotask_ticket_id: int):
    t = provider.get_ticket(autotask_ticket_id)
    row = t.model_dump()
    row["ai"] = categorise_ticket({"title": t.title, "description": t.description})
    return row

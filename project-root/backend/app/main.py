from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .providers.fake_autotask import FakeAutotaskProvider
from .services.ai_categoriser import categorise_ticket
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
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
    verbose: bool = Query(False),
):
    request_start = time.time()
    request_start_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    try:
        logger.info(f"[{request_start_str}] ========== API REQUEST START ==========")
        logger.info(f"[{request_start_str}] Filters: status={status}, priority={priority}, category={category}, limit={limit}, verbose={verbose}")
        
        # Step 1: Get tickets from provider
        provider_start = time.time()
        logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STEP 1: Fetching tickets from provider...")
        tickets = provider.get_tickets()
        provider_time = time.time() - provider_start
        logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STEP 1 COMPLETE: Retrieved {len(tickets)} tickets in {provider_time:.3f}s")
        
        # Step 2: Filter by status if provided
        if status:
            filter_start = time.time()
            tickets = [t for t in tickets if t.status == status]
            filter_time = time.time() - filter_start
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STEP 2: Filtered by status in {filter_time:.3f}s - {len(tickets)} tickets remaining")
        
        # Step 3: Filter by priority if provided
        if priority:
            filter_start = time.time()
            tickets = [t for t in tickets if t.priority == priority]
            filter_time = time.time() - filter_start
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STEP 3: Filtered by priority in {filter_time:.3f}s - {len(tickets)} tickets remaining")
        
        # Step 4: Categorize tickets (this is usually the bottleneck)
        categorization_start = time.time()
        logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STEP 4: Starting categorization of {min(len(tickets[:limit]), len(tickets))} tickets...")
        
        enriched = []
        ticket_times = []
        for i, t in enumerate(tickets[:limit]):
            try:
                ticket_cat_start = time.time()
                ai = categorise_ticket({"title": t.title, "description": t.description})
                ticket_cat_time = time.time() - ticket_cat_start
                row = t.model_dump()
                row["ai"] = ai
                enriched.append(row)
                ticket_times.append((t.ticket_number, ticket_cat_time))
                
                if verbose:
                    logger.debug(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Ticket {i+1}/{min(len(tickets[:limit]), len(tickets))}: {t.ticket_number} categorized in {ticket_cat_time:.3f}s ({ai['category']})")
                elif i % 10 == 0:  # Log every 10 tickets in normal mode
                    logger.debug(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Progress: {i+1}/{min(len(tickets[:limit]), len(tickets))} tickets categorized")
            except Exception as e:
                logger.error(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Error categorizing ticket {t.ticket_number}: {str(e)}", exc_info=True)
                row = t.model_dump()
                row["ai"] = {"category": "unknown", "confidence": 0}
                enriched.append(row)
        
        categorization_time = time.time() - categorization_start
        logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STEP 4 COMPLETE: Categorized {len(enriched)} tickets in {categorization_time:.3f}s (avg {categorization_time/len(enriched) if enriched else 0:.3f}s per ticket)")
        
        # If verbose, log timing statistics
        if verbose and ticket_times:
            min_time = min(t[1] for t in ticket_times)
            max_time = max(t[1] for t in ticket_times)
            avg_time = categorization_time / len(ticket_times)
            slowest = max(ticket_times, key=lambda x: x[1])
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] VERBOSE TIMING: Min={min_time:.3f}s | Max={max_time:.3f}s | Avg={avg_time:.3f}s | Slowest={slowest[0]} ({slowest[1]:.3f}s)")
        
        # Step 5: Filter by category if provided
        if category:
            filter_start = time.time()
            enriched = [t for t in enriched if t["ai"]["category"] == category]
            filter_time = time.time() - filter_start
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STEP 5: Filtered by category in {filter_time:.3f}s - {len(enriched)} tickets remaining")
        
        # Final: Prepare response
        response_prep_start = time.time()
        response_data = {"items": enriched, "count": len(enriched)}
        response_prep_time = time.time() - response_prep_start
        
        total_time = time.time() - request_start
        logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ========== API REQUEST COMPLETE ==========")
        logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Total time: {total_time:.3f}s - Returning {len(enriched)} tickets")
        logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] TIMING BREAKDOWN: Provider={provider_time:.3f}s | Categorization={categorization_time:.3f}s | Response Prep={response_prep_time:.3f}s")
        logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] To see per-ticket timing, add ?verbose=true to the query")
        
        return response_data
    except Exception as e:
        total_error_time = time.time() - request_start
        logger.error(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ERROR in list_tickets after {total_error_time:.3f}s: {str(e)}", exc_info=True)
        return {"items": [], "count": 0, "error": str(e)}

@app.get("/api/tickets/{autotask_ticket_id}")
def get_ticket(autotask_ticket_id: int):
    t = provider.get_ticket(autotask_ticket_id)
    row = t.model_dump()
    row["ai"] = categorise_ticket({"title": t.title, "description": t.description})
    return row

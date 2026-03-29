from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
from .providers.fake_autotask import FakeAutotaskProvider
from .services.ai import (
    categorise_ticket,
    list_available_categories,
    predict_categories_batch,
)
from .services.ai.priority_calculator import (
    calculate_priority_scores_batch,
    get_priority_label,
)
from .services.ai.text_processor import extract_ticket_text
from .services.ai.embedding_cache import get_cache
from .auth import AuthenticatedSession, get_current_session
from .routers.auth import router as auth_router
from .routers.ai_state import router as ai_state_router
from .routers.profiles import router as profiles_router
from .database import AsyncSessionLocal, close_db
from .config import settings
from .repositories.profile_repository import TenantRepository
from .services.ai_state_service import AIStateService
import logging
import time
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("Starting up application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    oversight_task: asyncio.Task | None = None

    async def oversight_worker() -> None:
        interval = max(5, settings.AI_OVERSIGHT_INTERVAL_SECONDS)
        queue_name = settings.AI_OVERSIGHT_QUEUE
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    tenant_repo = TenantRepository(db)
                    tenants = await tenant_repo.get_all_tenants()
                    for tenant in tenants:
                        service = AIStateService(db)
                        await service.refresh_ticket_states(
                            tenant_id=tenant.tenant_id,
                            include_closed=settings.AI_OVERSIGHT_INCLUDE_CLOSED,
                            limit=settings.AI_OVERSIGHT_REFRESH_LIMIT,
                            apply_oversight=True,
                            oversight_queue=queue_name,
                        )
                    await db.commit()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info("AI oversight worker cancelled.")
                raise
            except Exception:
                logger.exception("AI oversight worker cycle failed.")
                await asyncio.sleep(interval)

    if settings.AI_OVERSIGHT_ENABLED:
        logger.info(
            "AI oversight worker enabled: queue=%s, interval=%ss",
            settings.AI_OVERSIGHT_QUEUE,
            max(5, settings.AI_OVERSIGHT_INTERVAL_SECONDS),
        )
        oversight_task = asyncio.create_task(oversight_worker())
    else:
        logger.info("AI oversight worker disabled by configuration.")

    yield
    # Shutdown
    logger.info("Shutting down application...")
    if oversight_task is not None:
        oversight_task.cancel()
        try:
            await oversight_task
        except asyncio.CancelledError:
            pass
    await close_db()


app = FastAPI(
    title="SecOps Autotask Prototype API",
    version="0.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include profile management router
app.include_router(auth_router)
app.include_router(ai_state_router)
app.include_router(profiles_router)

provider = FakeAutotaskProvider()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api/cache/stats")
def cache_stats():
    """Get embedding cache statistics and performance metrics."""
    cache = get_cache()
    return cache.get_stats()

@app.post("/api/cache/clear")
def clear_cache():
    """Clear the embedding cache (useful for debugging)."""
    cache = get_cache()
    cache.clear()
    return {"status": "cache cleared"}

@app.get("/api/categories")
def categories():
    return {"items": list_available_categories()}

@app.get("/api/tickets")
def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    verbose: bool = Query(False),
    batch: bool = Query(True, description="Use batch processing (much faster)"),
    session: AuthenticatedSession = Depends(get_current_session),
):
    request_start = time.time()
    request_start_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    try:
        logger.info(f"[{request_start_str}] ========== API REQUEST START ==========")
        logger.info(f"[{request_start_str}] Filters: status={status}, priority={priority}, category={category}, limit={limit}, verbose={verbose}, batch={batch}")
        
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
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STEP 3: Filtered by priority in {filter_time:.3f}s - {len(tickets)} remaining")
        
        # Apply limit
        tickets = tickets[:limit]
        
        # Step 4: Categorize tickets
        categorization_start = time.time()
        logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STEP 4: Starting categorization of {len(tickets)} tickets (batch mode: {batch})...")
        
        enriched = []
        ticket_times = []
        
        if batch and len(tickets) > 1:
            # BATCH PROCESSING MODE (MUCH FASTER)
            extract_start = time.time()
            ticket_texts = [extract_ticket_text(t.model_dump()) for t in tickets]
            extract_time = time.time() - extract_start
            logger.debug(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Text preparation: {extract_time:.3f}s")
            
            # Process all at once
            batch_start = time.time()
            batch_results = predict_categories_batch(ticket_texts)
            batch_time = time.time() - batch_start
            
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] BATCH: Categorized {len(tickets)} tickets in {batch_time:.3f}s (avg {batch_time/len(tickets):.4f}s per ticket)")
            
            # Build enriched tickets - batch priority calculation
            categories_list = [cat for cat, _, _ in batch_results]
            scores_list = [scores for _, _, scores in batch_results]
            
            # Calculate all priorities at once
            priority_scores = calculate_priority_scores_batch(ticket_texts, categories_list, scores_list)
            
            for t, ticket_text, (cat, method, scores), priority_score in zip(tickets, ticket_texts, batch_results, priority_scores):
                # Skip early if category filter doesn't match
                if category and cat != category:
                    continue
                
                priority_label = get_priority_label(priority_score)
                
                row = t.model_dump()
                row["ai"] = {
                    "category": cat,
                    "confidence": scores[cat],
                    "priority": priority_label,
                    "priority_score": priority_score,
                    "method": method
                }
                enriched.append(row)
        else:
            # SEQUENTIAL PROCESSING (slower, for compatibility)
            for i, t in enumerate(tickets):
                try:
                    ticket_cat_start = time.time()
                    ai = categorise_ticket(t.model_dump())
                    ticket_cat_time = time.time() - ticket_cat_start
                    row = t.model_dump()
                    row["ai"] = ai
                    enriched.append(row)
                    ticket_times.append((t.ticket_number, ticket_cat_time))
                    
                    if verbose:
                        logger.debug(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Ticket {i+1}/{len(tickets)}: {t.ticket_number} categorized in {ticket_cat_time:.3f}s ({ai['category']})")
                    elif i % 10 == 0:  # Log every 10 tickets in normal mode
                        logger.debug(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Progress: {i+1}/{len(tickets)} tickets categorized")
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
        
        # Step 5: Filter by category (only needed in sequential mode now)
        if category and not batch:
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
        if batch:
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🚀 BATCH MODE: {len(tickets)} tickets processed {(categorization_time/len(tickets) if tickets else 0):.4f}s per ticket (try ?batch=false to compare)")
        else:
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] To see per-ticket timing, add ?verbose=true to the query. Try ?batch=true for faster processing!")
        
        return response_data
    except Exception as e:
        total_error_time = time.time() - request_start
        logger.error(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ERROR in list_tickets after {total_error_time:.3f}s: {str(e)}", exc_info=True)
        return {"items": [], "count": 0, "error": str(e)}

@app.get("/api/tickets/{autotask_ticket_id}")
def get_ticket(
    autotask_ticket_id: int,
    session: AuthenticatedSession = Depends(get_current_session),
):
    t = provider.get_ticket(autotask_ticket_id)
    row = t.model_dump()
    row["ai"] = categorise_ticket({"title": t.title, "description": t.description})
    return row


@app.get("/api/tickets/stream/categorize")
async def stream_categorize_tickets(
    status: str | None = None,
    priority: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    session: AuthenticatedSession = Depends(get_current_session),
):
    """
    Stream ticket categorization results in real-time.
    Returns Server-Sent Events (SSE) with each ticket as it's processed.
    """
    async def event_generator():
        try:
            # Get tickets
            tickets = provider.get_tickets()
            
            # Apply filters
            if status:
                tickets = [t for t in tickets if t.status == status]
            if priority:
                tickets = [t for t in tickets if t.priority == priority]
            
            tickets = tickets[:limit]
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'start', 'total': len(tickets)})}\n\n"
            
            # Process and stream each ticket
            for i, t in enumerate(tickets, 1):
                try:
                    # Categorize ticket
                    ai_result = categorise_ticket({"title": t.title, "description": t.description})
                    
                    # Prepare ticket data
                    row = t.model_dump()
                    row["ai"] = ai_result
                    
                    # Stream this ticket
                    ticket_event = {
                        'type': 'ticket',
                        'index': i,
                        'total': len(tickets),
                        'data': row
                    }
                    yield f"data: {json.dumps(ticket_event)}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error processing ticket {t.ticket_number}: {str(e)}")
                    error_event = {
                        'type': 'error',
                        'ticket_number': t.ticket_number,
                        'error': str(e)
                    }
                    yield f"data: {json.dumps(error_event)}\n\n"
            
            # Send completion status
            yield f"data: {json.dumps({'type': 'complete', 'total': len(tickets)})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

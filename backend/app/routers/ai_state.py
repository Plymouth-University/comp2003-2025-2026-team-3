"""API routes for AI operational state."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthenticatedSession, get_current_session
from ..database import get_db
from ..schemas.ai_state import (
    TicketAIRefreshRequest,
    TicketAIRefreshResponse,
    TicketAIStateResponse,
)
from ..services.ai import list_available_categories
from ..services.ai_state_service import AIStateService

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.get("/categories")
async def get_ai_categories(
    session: AuthenticatedSession = Depends(get_current_session),
):
    """Return the configured AI ticket categories."""
    return {
        "tenant_id": session.tenant_id,
        "items": list_available_categories(),
    }


@router.post("/ticket-states/refresh", response_model=TicketAIRefreshResponse)
async def refresh_ai_ticket_states(
    refresh_request: TicketAIRefreshRequest,
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """Refresh persisted AI state from the ticket provider for the current tenant."""
    service = AIStateService(db)
    return await service.refresh_ticket_states(
        tenant_id=UUID(session.tenant_id),
        include_closed=refresh_request.include_closed,
        limit=refresh_request.limit,
    )


@router.get("/ticket-states", response_model=list[TicketAIStateResponse])
async def list_ai_ticket_states(
    include_closed: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """List persisted AI ticket states for the current tenant."""
    service = AIStateService(db)
    return await service.list_ticket_states(
        tenant_id=UUID(session.tenant_id),
        include_closed=include_closed,
        limit=limit,
        offset=offset,
    )


@router.get("/ticket-states/my-primary", response_model=list[TicketAIStateResponse])
async def list_my_primary_ticket_states(
    include_closed: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """List persisted AI ticket states where the current user is the primary resource."""
    service = AIStateService(db)
    return await service.list_profile_ticket_states(
        tenant_id=UUID(session.tenant_id),
        profile_id=UUID(session.profile_id),
        assignment_role="primary",
        include_closed=include_closed,
        limit=limit,
        offset=offset,
    )


@router.get("/ticket-states/my-secondary", response_model=list[TicketAIStateResponse])
async def list_my_secondary_ticket_states(
    include_closed: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """List persisted AI ticket states where the current user is the secondary resource."""
    service = AIStateService(db)
    return await service.list_profile_ticket_states(
        tenant_id=UUID(session.tenant_id),
        profile_id=UUID(session.profile_id),
        assignment_role="secondary",
        include_closed=include_closed,
        limit=limit,
        offset=offset,
    )


@router.get("/ticket-states/my-assigned", response_model=list[TicketAIStateResponse])
async def list_my_assigned_ticket_states(
    include_closed: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """List persisted AI ticket states where the current user is primary or secondary."""
    service = AIStateService(db)
    return await service.list_profile_ticket_states(
        tenant_id=UUID(session.tenant_id),
        profile_id=UUID(session.profile_id),
        assignment_role="assigned",
        include_closed=include_closed,
        limit=limit,
        offset=offset,
    )


@router.get("/ticket-states/team", response_model=list[TicketAIStateResponse])
async def list_team_ticket_states(
    queue: str = Query("MS - SecOps"),
    include_closed: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """List persisted AI ticket states for the SecOps queue."""
    service = AIStateService(db)
    return await service.list_queue_ticket_states(
        tenant_id=UUID(session.tenant_id),
        queue=queue,
        include_closed=include_closed,
        limit=limit,
        offset=offset,
    )


@router.get("/ticket-states/{autotask_ticket_id}", response_model=TicketAIStateResponse)
async def get_ai_ticket_state(
    autotask_ticket_id: int,
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """Get one persisted AI ticket state for the current tenant."""
    service = AIStateService(db)
    state = await service.get_ticket_state(UUID(session.tenant_id), autotask_ticket_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI ticket state not found for autotask_ticket_id={autotask_ticket_id}",
        )
    return state

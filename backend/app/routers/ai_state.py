"""API routes for AI operational state."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthenticatedSession, get_current_session
from ..database import get_ai_db, get_profile_db
from ..schemas.ai_state import (
    AIOversightRunResponse,
    TicketAssignmentOverrideRequest,
    TicketAssignmentRecommendationResponse,
    TicketCategoryOverrideRequest,
    TicketAIRefreshRequest,
    TicketAIRefreshResponse,
    TicketAIStateCloseRequest,
    TicketAIStateResponse,
    TicketAIStateUpdateRequest,
)
from ..services.ai import list_available_categories
from ..services.ai_assignment_service import AIAssignmentService
from ..services.ai_oversight_service import AIOversightService
from ..services.ai_state_service import AIStateService
from ..services.log_writer import LogContext, LogWriter

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
log_writer = LogWriter()


def _log_context(
    request: Request,
    session: AuthenticatedSession,
    *,
    autotask_ticket_id: int | None = None,
) -> LogContext:
    return LogContext.from_request(
        request,
        session=session,
        autotask_ticket_id=autotask_ticket_id,
        logger_name=__name__,
    )


async def _write_ai_event(
    *,
    context: LogContext,
    action: str,
    message: str,
    outcome: str = "success",
    entity_id: str | None = None,
    details: dict | None = None,
) -> None:
    await log_writer.write_application_log(
        context=context,
        log_type="ai_state",
        subsystem="ai",
        action=action,
        level="info",
        message=message,
        outcome=outcome,
        entity_type="ticket_ai_state" if entity_id else None,
        entity_id=entity_id,
        details=details,
    )


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
    request: Request,
    refresh_request: TicketAIRefreshRequest,
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """Refresh persisted AI state from the ticket provider for the current tenant."""
    service = AIStateService(ai_db, profile_db)
    result = await service.refresh_ticket_states(
        tenant_id=UUID(session.tenant_id),
        include_closed=refresh_request.include_closed,
        limit=refresh_request.limit,
        apply_oversight=refresh_request.apply_oversight,
        oversight_queue=refresh_request.oversight_queue,
    )
    await _write_ai_event(
        context=_log_context(request, session),
        action="ticket_states_refreshed",
        message="AI ticket states refreshed",
        details=result.model_dump(mode="json"),
    )
    return result


@router.post("/oversight/run", response_model=AIOversightRunResponse)
async def run_ai_oversight(
    request: Request,
    queue: str = Query("MS - SecOps"),
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """Run AI oversight once for the current tenant queue."""
    service = AIOversightService(ai_db, profile_db)
    result = await service.run_for_tenant(
        tenant_id=UUID(session.tenant_id),
        queue=queue,
    )
    await _write_ai_event(
        context=_log_context(request, session),
        action="oversight_run_completed",
        message="AI oversight run completed",
        details=result.model_dump(mode="json"),
    )
    return result


@router.get("/ticket-states", response_model=list[TicketAIStateResponse])
async def list_ai_ticket_states(
    include_closed: bool = Query(False),
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """List persisted AI ticket states for the current tenant."""
    service = AIStateService(ai_db, profile_db)
    return await service.list_ticket_states(
        tenant_id=UUID(session.tenant_id),
        include_closed=include_closed,
        limit=limit,
        offset=offset,
    )


@router.get("/ticket-states/my-primary", response_model=list[TicketAIStateResponse])
async def list_my_primary_ticket_states(
    include_closed: bool = Query(False),
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """List persisted AI ticket states where the current user is the primary resource."""
    service = AIStateService(ai_db, profile_db)
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
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """List persisted AI ticket states where the current user is the secondary resource."""
    service = AIStateService(ai_db, profile_db)
    return await service.list_profile_ticket_states(
        tenant_id=UUID(session.tenant_id),
        profile_id=UUID(session.profile_id),
        assignment_role="secondary",
        include_closed=include_closed,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/ticket-states/my-primary/closed",
    response_model=list[TicketAIStateResponse],
)
@router.get(
    "/ticket-states/primary/closed",
    response_model=list[TicketAIStateResponse],
)
async def list_my_closed_primary_ticket_states(
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """List closed AI ticket states where the current user is the primary resource."""
    service = AIStateService(ai_db, profile_db)
    return await service.list_profile_ticket_states(
        tenant_id=UUID(session.tenant_id),
        profile_id=UUID(session.profile_id),
        assignment_role="primary",
        closed_only=True,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/ticket-states/my-secondary/closed",
    response_model=list[TicketAIStateResponse],
)
@router.get(
    "/ticket-states/secondary/closed",
    response_model=list[TicketAIStateResponse],
)
async def list_my_closed_secondary_ticket_states(
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """List closed AI ticket states where the current user is the secondary resource."""
    service = AIStateService(ai_db, profile_db)
    return await service.list_profile_ticket_states(
        tenant_id=UUID(session.tenant_id),
        profile_id=UUID(session.profile_id),
        assignment_role="secondary",
        closed_only=True,
        limit=limit,
        offset=offset,
    )


@router.get("/ticket-states/my-assigned", response_model=list[TicketAIStateResponse])
async def list_my_assigned_ticket_states(
    include_closed: bool = Query(False),
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """List persisted AI ticket states where the current user is primary or secondary."""
    service = AIStateService(ai_db, profile_db)
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
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """List persisted AI ticket states for the SecOps queue."""
    service = AIStateService(ai_db, profile_db)
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
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """Get one persisted AI ticket state for the current tenant."""
    service = AIStateService(ai_db, profile_db)
    state = await service.get_ticket_state(UUID(session.tenant_id), autotask_ticket_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI ticket state not found for autotask_ticket_id={autotask_ticket_id}",
        )
    return state


@router.patch(
    "/ticket-states/{autotask_ticket_id}/close",
    response_model=TicketAIStateResponse,
)
async def close_ai_ticket_state(
    request: Request,
    autotask_ticket_id: int,
    close_request: TicketAIStateCloseRequest,
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """Mark one persisted AI ticket state as closed with a user-provided reason."""
    service = AIStateService(ai_db, profile_db)
    try:
        state = await service.close_ticket_state(
            UUID(session.tenant_id),
            autotask_ticket_id,
            close_request,
            UUID(session.profile_id),
        )
    except ValueError as exc:
        await log_writer.write_error_log(
            context=_log_context(request, session, autotask_ticket_id=autotask_ticket_id),
            service_name="ai",
            severity="medium",
            message="Failed to close AI ticket state",
            error=exc,
            action="ticket_state_close",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"reason_provided": bool(close_request.reason_closed)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI ticket state not found for autotask_ticket_id={autotask_ticket_id}",
        )
    await _write_ai_event(
        context=_log_context(request, session, autotask_ticket_id=autotask_ticket_id),
        action="ticket_state_closed",
        message="AI ticket state closed",
        entity_id=str(autotask_ticket_id),
        details={"reason_provided": bool(close_request.reason_closed)},
    )
    return state


@router.patch(
    "/ticket-states/{autotask_ticket_id}/category-override",
    response_model=TicketAIStateResponse,
)
async def override_ai_ticket_category(
    request: Request,
    autotask_ticket_id: int,
    override_request: TicketCategoryOverrideRequest,
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """Manually reassign a ticket category with a user-provided reason."""
    service = AIStateService(ai_db, profile_db)
    try:
        state = await service.override_ticket_category(
            UUID(session.tenant_id),
            autotask_ticket_id,
            override_request,
            UUID(session.profile_id),
        )
    except ValueError as exc:
        await log_writer.write_error_log(
            context=_log_context(request, session, autotask_ticket_id=autotask_ticket_id),
            service_name="ai",
            severity="medium",
            message="Failed to override ticket category",
            error=exc,
            action="ticket_category_override",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "category": override_request.category,
                "reason_provided": bool(override_request.category_override_reason),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI ticket state not found for autotask_ticket_id={autotask_ticket_id}",
        )
    await _write_ai_event(
        context=_log_context(request, session, autotask_ticket_id=autotask_ticket_id),
        action="ticket_category_overridden",
        message="Ticket category manually overridden",
        entity_id=str(autotask_ticket_id),
        details={
            "category": override_request.category,
            "reason_provided": bool(override_request.category_override_reason),
        },
    )
    return state


@router.patch("/ticket-states/{autotask_ticket_id}", response_model=TicketAIStateResponse)
async def update_ai_ticket_state(
    request: Request,
    autotask_ticket_id: int,
    update_request: TicketAIStateUpdateRequest,
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """Update editable fields on the persisted AI ticket state for the current tenant."""
    service = AIStateService(ai_db, profile_db)
    try:
        state = await service.update_ticket_state(
            UUID(session.tenant_id),
            autotask_ticket_id,
            update_request,
            UUID(session.profile_id),
        )
    except ValueError as exc:
        await log_writer.write_error_log(
            context=_log_context(request, session, autotask_ticket_id=autotask_ticket_id),
            service_name="ai",
            severity="medium",
            message="Failed to update AI ticket state",
            error=exc,
            action="ticket_state_update",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"updated_fields": update_request.model_fields_set},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI ticket state not found for autotask_ticket_id={autotask_ticket_id}",
        )
    await _write_ai_event(
        context=_log_context(request, session, autotask_ticket_id=autotask_ticket_id),
        action="ticket_state_updated",
        message="AI ticket state updated",
        entity_id=str(autotask_ticket_id),
        details={"updated_fields": sorted(update_request.model_fields_set)},
    )
    return state


@router.get(
    "/ticket-states/{autotask_ticket_id}/assignment-recommendation",
    response_model=TicketAssignmentRecommendationResponse,
)
async def get_ticket_assignment_recommendation(
    autotask_ticket_id: int,
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """Recommend an assignee based on stored profile specialisms for this ticket category."""
    service = AIAssignmentService(ai_db, profile_db)
    recommendation = await service.recommend_for_ticket(
        UUID(session.tenant_id), autotask_ticket_id
    )
    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI ticket state not found for autotask_ticket_id={autotask_ticket_id}",
        )
    return recommendation


@router.put(
    "/ticket-states/{autotask_ticket_id}/assignment-override",
    response_model=TicketAssignmentRecommendationResponse,
)
async def set_ticket_assignment_override(
    request: Request,
    autotask_ticket_id: int,
    override_request: TicketAssignmentOverrideRequest,
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """Persist a manual assignment override for a ticket."""
    state_service = AIStateService(ai_db, profile_db)
    try:
        updated = await state_service.set_manual_override(
            tenant_id=UUID(session.tenant_id),
            autotask_ticket_id=autotask_ticket_id,
            override_profile_id=override_request.profile_id,
            set_by_profile_id=UUID(session.profile_id),
            reason=override_request.reason,
        )
    except ValueError as exc:
        await log_writer.write_error_log(
            context=_log_context(request, session, autotask_ticket_id=autotask_ticket_id),
            service_name="ai",
            severity="medium",
            message="Failed to set assignment override",
            error=exc,
            action="assignment_override_set",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "override_profile_id": str(override_request.profile_id),
                "reason_provided": bool(override_request.reason),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI ticket state not found for autotask_ticket_id={autotask_ticket_id}",
        )

    service = AIAssignmentService(ai_db, profile_db)
    recommendation = await service.recommend_for_ticket(
        UUID(session.tenant_id), autotask_ticket_id
    )
    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI ticket state not found for autotask_ticket_id={autotask_ticket_id}",
        )
    await _write_ai_event(
        context=_log_context(request, session, autotask_ticket_id=autotask_ticket_id),
        action="assignment_override_set",
        message="Manual assignment override set",
        entity_id=str(autotask_ticket_id),
        details={
            "override_profile_id": str(override_request.profile_id),
            "reason_provided": bool(override_request.reason),
        },
    )
    return recommendation


@router.delete(
    "/ticket-states/{autotask_ticket_id}/assignment-override",
    response_model=TicketAssignmentRecommendationResponse,
)
async def clear_ticket_assignment_override(
    request: Request,
    autotask_ticket_id: int,
    session: AuthenticatedSession = Depends(get_current_session),
    ai_db: AsyncSession = Depends(get_ai_db),
    profile_db: AsyncSession = Depends(get_profile_db),
):
    """Clear any persisted manual assignment override for a ticket."""
    state_service = AIStateService(ai_db, profile_db)
    try:
        updated = await state_service.clear_manual_override(
            tenant_id=UUID(session.tenant_id),
            autotask_ticket_id=autotask_ticket_id,
        )
    except ValueError as exc:
        await log_writer.write_error_log(
            context=_log_context(request, session, autotask_ticket_id=autotask_ticket_id),
            service_name="ai",
            severity="medium",
            message="Failed to clear assignment override",
            error=exc,
            action="assignment_override_clear",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI ticket state not found for autotask_ticket_id={autotask_ticket_id}",
        )

    service = AIAssignmentService(ai_db, profile_db)
    recommendation = await service.recommend_for_ticket(
        UUID(session.tenant_id), autotask_ticket_id
    )
    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI ticket state not found for autotask_ticket_id={autotask_ticket_id}",
        )
    await _write_ai_event(
        context=_log_context(request, session, autotask_ticket_id=autotask_ticket_id),
        action="assignment_override_cleared",
        message="Manual assignment override cleared",
        entity_id=str(autotask_ticket_id),
    )
    return recommendation

"""Durable logging ingestion routes."""

from fastapi import APIRouter, Depends, Request, Response, status

from ..auth import AuthenticatedSession, get_current_session
from ..schemas.logs import UIClickLogCreate
from ..services.log_writer import LogContext, LogWriter

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])
log_writer = LogWriter()


@router.post("/ui-clicks", status_code=status.HTTP_204_NO_CONTENT)
async def create_ui_click_log(
    request: Request,
    event: UIClickLogCreate,
    session: AuthenticatedSession = Depends(get_current_session),
) -> Response:
    """Persist one authenticated frontend interaction event."""
    context = LogContext.from_request(
        request,
        source="frontend",
        session=session,
        component=event.element_id,
        logger_name=__name__,
    )
    await log_writer.write_ui_click_log(
        context=context,
        action_type=event.action_type,
        component=event.component,
        page_path=event.page_path,
        duration_ms=event.duration_ms,
        details=event.details,
        occurred_at=event.occurred_at,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

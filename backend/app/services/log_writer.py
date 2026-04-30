"""
Centralized log persistence service.

Why this file exists:
- The rest of the application should describe what happened.
- This service should decide how that event is stored in the logging database.
- Keeping all DB log writes here prevents ad hoc inserts scattered across routers,
  providers, AI modules, and frontend-ingest endpoints.

Design choices:
- Methods are async because the logging database uses async SQLAlchemy.
- Each write opens its own short-lived logging session.
- Failures inside the log writer never crash the caller; they fall back to
  standard Python logging instead.
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Mapping
from uuid import UUID, uuid4

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import settings
from ..log_database import LogSessionLocal
from ..models.logs import (
    ApplicationLog,
    ErrorLog,
    PerformanceLog,
    RequestTrace,
    UIClickAnalyticsLog,
)

fallback_logger = logging.getLogger(__name__)

# Helper functions below for data conversion, normalisation and timestamping.

def utcnow() -> datetime:
    """Return a timezone-aware UTC datetime for all logging timestamps."""
    return datetime.now(timezone.utc)


def uuid_converter(value: str | UUID | None) -> UUID | None:
    """Helper function used for converting incoming string/UUID values to UUID objects."""

    if value in (None, ""):
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        fallback_logger.warning("Dropping invalid UUID value from durable log context")
        return None


def normalise_details(details: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Convert details to a JSON format for the JSONB details attribute of the log tables."""

    if not details:
        return None
    return jsonable_encoder(details)


@dataclass(slots=True)
class LogContext:
    """Small shared context object passed between middleware, routers, and services."""
    
    request_id: str
    source: str
    endpoint: str | None = None
    method: str | None = None
    tenant_id: str | UUID | None = None
    profile_id: str | UUID | None = None
    autotask_ticket_id: int | None = None
    page_path: str | None = None
    component: str | None = None
    logger_name: str | None = None
    
    @classmethod
    def from_request(
        cls, 
        request: Request, 
        *,
        source: str = "backend",
        session: Any | None = None,
        autotask_ticket_id: int | None = None,
        component: str | None = None,
        logger_name: str | None = None,
    ) -> "LogContext":
        """Build a context from the FastAPI request state."""

        request_id = getattr(request.state, "request_id", None) or str(uuid4())
        return cls(
            request_id=request_id,
            source=source,
            endpoint=request.url.path,
            method=request.method,
            tenant_id=getattr(session, "tenant_id", None),
            profile_id=getattr(session, "profile_id", None),
            autotask_ticket_id=autotask_ticket_id,
            page_path=request.url.path,
            component=component,
            logger_name=logger_name,
        )

    @classmethod
    def from_Request(cls, request: Request, **kwargs: Any) -> "LogContext":
        """Backward-compatible alias for older call sites."""
        return cls.from_request(request, **kwargs)
        
class LogWriter:
    """
    Central API for writing all durable logs.

    Public methods map directly to the table families:
    - ensure_trace / finalize_trace -> RequestTrace
    - write_application_log -> ApplicationLog
    - write_performance_log -> PerformanceLog
    - write_error_log -> ErrorLog
    - write_ui_click_log -> UIClickAnalyticsLog
    """
    
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = LogSessionLocal,
        *,
        environment: str = settings.ENVIRONMENT,
    ) -> None:
        self.session_factory = session_factory
        self.environment = environment

    async def _run(
        self,
        operation_name: str,
        work: Callable[[AsyncSession], Awaitable[None]],
    ) -> None:
        """
        Execute one logging DB operation in an isolated session.

        Logging failures should never bring down the real request path, so exceptions
        are swallowed after being emitted to fallback_logger.
        """
        async with self.session_factory() as session:
            try:
                await work(session)
                await session.commit()
            except Exception:
                fallback_logger.exception(
                    "Failed during log writer operation '%s'", operation_name
                )
                try:
                    await session.rollback()
                except Exception:
                    fallback_logger.exception(
                        "Failed to roll back log writer operation '%s'",
                        operation_name,
                    )

    async def _ensure_trace_row(
        self,
        session: AsyncSession,
        *,
        request_id: str,
        source: str,
        seen_at: datetime,
    ) -> None:
        """
        Create the request-trace row on first use, or touch the existing one.

        first_seen_at is written once.
        last_seen_at is advanced on every related event.
        """
        statement = (
            insert(RequestTrace)
            .values(
                request_id=request_id,
                first_seen_at=seen_at,
                last_seen_at=seen_at,
                source=source,
                environment=self.environment,
            )
            .on_conflict_do_update(
                index_elements=[RequestTrace.request_id],
                set_={
                    "last_seen_at": seen_at,
                    "source": func.coalesce(RequestTrace.source, source),
                    "environment": func.coalesce(
                        RequestTrace.environment, self.environment
                    ),
                },
            )
        )
        await session.execute(statement)
    
    async def ensure_trace(
        self, context: LogContext, *, seen_at: datetime | None = None
    ) -> None:
        """Create or touch the RequestTrace row for the current request context."""
        event_time = seen_at or utcnow()

        async def work(session: AsyncSession) -> None:
            await self._ensure_trace_row(
                session,
                request_id=context.request_id,
                source=context.source,
                seen_at=event_time,
            )

        await self._run("ensure_trace", work)

    async def write_application_log(
        self,
        *,
        context: LogContext,
        log_type: str,
        subsystem: str,
        action: str,
        level: str,
        message: str,
        outcome: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        status_code: int | None = None,
        duration_ms: float | None = None,
        details: Mapping[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        """Write one general structured event row."""
        event_time = occurred_at or utcnow()

        async def work(session: AsyncSession) -> None:
            await self._ensure_trace_row(
                session,
                request_id=context.request_id,
                source=context.source,
                seen_at=event_time,
            )
            session.add(
                ApplicationLog(
                    occurred_at=event_time,
                    log_type=log_type,
                    source=context.source,
                    subsystem=subsystem,
                    action=action,
                    logger_name=context.logger_name,
                    environment=self.environment,
                    request_id=context.request_id,
                    tenant_id=uuid_converter(context.tenant_id),
                    profile_id=uuid_converter(context.profile_id),
                    entity_type=entity_type,
                    entity_id=entity_id,
                    autotask_ticket_id=context.autotask_ticket_id,
                    endpoint=context.endpoint,
                    method=context.method,
                    status_code=status_code,
                    level=level,
                    outcome=outcome,
                    duration_ms=duration_ms,
                    message=message,
                    details=normalise_details(details),
                )
            )

        await self._run("write_application_log", work)

    async def write_performance_log(
        self,
        *,
        context: LogContext,
        operation_name: str,
        service_name: str,
        total_duration_ms: float,
        db_latency_ms: float | None = None,
        external_api_latency_ms: float | None = None,
        app_logic_ms: float | None = None,
        memory_used_mb: float | None = None,
        payload_size_kb: float | None = None,
        status_code: int | None = None,
        details: Mapping[str, Any] | None = None,
        is_slow: bool = False,
        occurred_at: datetime | None = None,
    ) -> None:
        """Write one performance event row."""
        event_time = occurred_at or utcnow()

        async def work(session: AsyncSession) -> None:
            await self._ensure_trace_row(
                session,
                request_id=context.request_id,
                source=context.source,
                seen_at=event_time,
            )
            session.add(
                PerformanceLog(
                    occurred_at=event_time,
                    request_id=context.request_id,
                    operation_name=operation_name,
                    service_name=service_name,
                    source=context.source,
                    logger_name=context.logger_name,
                    environment=self.environment,
                    total_duration_ms=total_duration_ms,
                    db_latency_ms=db_latency_ms,
                    external_api_latency_ms=external_api_latency_ms,
                    app_logic_ms=app_logic_ms,
                    memory_used_mb=memory_used_mb,
                    payload_size_kb=payload_size_kb,
                    is_slow=1 if is_slow else 0,
                    endpoint=context.endpoint,
                    method=context.method,
                    status_code=status_code,
                    tenant_id=uuid_converter(context.tenant_id),
                    profile_id=uuid_converter(context.profile_id),
                    autotask_ticket_id=context.autotask_ticket_id,
                    details=normalise_details(details),
                )
            )

        await self._run("write_performance_log", work)

    async def write_error_log(
        self,
        *,
        context: LogContext,
        service_name: str,
        severity: str,
        message: str,
        error: Exception | None = None,
        error_type: str | None = None,
        action: str | None = None,
        status_code: int | None = None,
        details: Mapping[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        
        """Write one error event row."""
        event_time = occurred_at or utcnow()
        resolved_error_type = error_type or (
            type(error).__name__ if error else "UnknownError"
        )
        stack_trace = None
        if error is not None:
            stack_trace = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )

        async def work(session: AsyncSession) -> None:
            await self._ensure_trace_row(
                session,
                request_id=context.request_id,
                source=context.source,
                seen_at=event_time,
            )
            session.add(
                ErrorLog(
                    occurred_at=event_time,
                    error_type=resolved_error_type,
                    service_name=service_name,
                    subsystem=action,
                    logger_name=context.logger_name,
                    environment=self.environment,
                    message=message,
                    action=action,
                    stack_trace=stack_trace,
                    endpoint=context.endpoint,
                    method=context.method,
                    status_code=status_code,
                    request_id=context.request_id,
                    tenant_id=uuid_converter(context.tenant_id),
                    profile_id=uuid_converter(context.profile_id),
                    autotask_ticket_id=context.autotask_ticket_id,
                    severity=severity,
                    error_resolution="unresolved",
                    details=normalise_details(details),
                )
            )

        await self._run("write_error_log", work)

    async def write_ui_click_log(
        self,
        *,
        context: LogContext,
        action_type: str,
        component: str,
        page_path: str,
        duration_ms: float | None = None,
        details: Mapping[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        """Write one frontend interaction row."""
        event_time = occurred_at or utcnow()

        async def work(session: AsyncSession) -> None:
            await self._ensure_trace_row(
                session,
                request_id=context.request_id,
                source="frontend",
                seen_at=event_time,
            )
            session.add(
                UIClickAnalyticsLog(
                    occurred_at=event_time,
                    request_id=context.request_id,
                    tenant_id=uuid_converter(context.tenant_id),
                    profile_id=uuid_converter(context.profile_id),
                    environment=self.environment,
                    page_path=page_path,
                    component=component,
                    action_type=action_type,
                    element_id=context.component,
                    duration_ms=duration_ms,
                    details=normalise_details(details),
                )
            )

        await self._run("write_ui_click_log", work)

    async def log_request_started(
        self,
        *,
        context: LogContext,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        """Convenience helper for middleware request-start events."""
        await self.write_application_log(
            context=context,
            log_type="backend_request",
            subsystem="http",
            action="request_started",
            level="info",
            message=f"{context.method} {context.endpoint} started",
            outcome="started",
            details=details,
        )

    async def log_request_completed(
        self,
        *,
        context: LogContext,
        status_code: int,
        duration_ms: float,
        app_logic_ms: float | None = None,
        memory_used_mb: float | None = None,
        payload_size_kb: float | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        """
        Convenience helper for middleware request-end events.

        This writes both the summary application event and the request-level performance row.
        """
        outcome = "success" if status_code < 400 else "failure"

        await self.write_application_log(
            context=context,
            log_type="backend_request",
            subsystem="http",
            action="request_completed",
            level="info" if status_code < 400 else "warning",
            message=f"{context.method} {context.endpoint} completed with {status_code}",
            outcome=outcome,
            status_code=status_code,
            duration_ms=duration_ms,
            details=details,
        )

        await self.write_performance_log(
            context=context,
            operation_name="http_request_total",
            service_name="http",
            total_duration_ms=duration_ms,
            app_logic_ms=app_logic_ms,
            memory_used_mb=memory_used_mb,
            payload_size_kb=payload_size_kb,
            status_code=status_code,
            details={"outcome": outcome, **(details or {})},
            is_slow=duration_ms >= 1000,
        )

"""SQLAlchemy models for a dedicated durable logging database."""

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..log_database import LogBase


class RequestTrace(LogBase):
    """Correlation root shared by request-linked log tables."""

    __tablename__ = "request_trace"

    # Request identification fields for tracing and correlation across logs
    request_id = Column(
        String(100), primary_key=True, nullable=False
    )  # trcae ID across logs
    first_seen_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # when the request was first captured
    last_seen_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # most recent log event for this request, gets updated with each new log entry for this request
    source = Column(
        String(50), nullable=True
    )  # originating service or component that initiated the request
    environment = Column(String(50), nullable=True)

    # Defining relationships to log tables for easy access to all logs related to this request trace
    application_logs = relationship("ApplicationLog", back_populates="request_trace")
    performance_logs = relationship("PerformanceLog", back_populates="request_trace")
    error_logs = relationship("ErrorLog", back_populates="request_trace")
    ui_click_logs = relationship("UIClickAnalyticsLog", back_populates="request_trace")


class ApplicationLog(LogBase):
    """Main structured application event table."""

    __tablename__ = "application_logs"

    # ID fields
    log_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    occurred_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Context and categorisation fields
    log_type = Column(String(50), nullable=False, index=True)  # type of log
    source = Column(
        String(50), nullable=False, index=True
    )  # originating service or component that generated the log
    subsystem = Column(
        String(100), nullable=False, index=True
    )  # specific subsystem or module within the source that generated the log
    action = Column(
        String(200), nullable=False, index=True
    )  # specific action or event being logged, useful for categorization and filtering
    logger_name = Column(
        String(150), nullable=True, index=True
    )  # trace the event back to the exact code logger that produced it
    environment = Column(String(50), nullable=True, index=True)

    request_id = Column(
        String(100),
        ForeignKey("request_trace.request_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Tenant and profile association for multi-tenant context and user-level filtering (if applicable)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    profile_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    entity_type = Column(String(50), nullable=True, index=True)
    entity_id = Column(String(100), nullable=True, index=True)
    autotask_ticket_id = Column(
        Integer, nullable=True, index=True
    )  # in case log is related to a certain ticket

    # For API endpoints
    endpoint = Column(String(255), nullable=True, index=True)
    method = Column(String(10), nullable=True, index=True)
    status_code = Column(SmallInteger, nullable=True, index=True)

    # Log content fields
    level = Column(String(20), nullable=False, index=True)
    outcome = Column(String(50), nullable=True, index=True)
    duration_ms = Column(Numeric(precision=10, scale=2), nullable=True)
    message = Column(Text, nullable=False)  # log message or event description
    details = Column(JSONB, nullable=True)  # log details in JSON format

    # Relationships
    request_trace = relationship("RequestTrace", back_populates="application_logs")

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_app_log_occurred", "created_at", "occurred_at"),
        Index("idx_app_log_type", "log_type"),
        Index("idx_app_log_request_id", "request_id"),
        Index("idx_app_log_tenant_id", "tenant_id"),
        Index("idx_app_log_profile_id", "profile_id"),
        Index("idx_app_log_entity", "entity_type", "entity_id"),
        Index("idx_app_log_level", "level"),
        Index("idx_app_log_endpoint_method", "endpoint", "method"),
    )


class PerformanceLog(LogBase):
    """Dedicated table for specialized performance metrics."""

    __tablename__ = "performance_logs"

    # ID fields
    perf_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    occurred_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    request_id = Column(
        String(100),
        ForeignKey("request_trace.request_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Context and categorisation fields
    operation_name = Column(String(150), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    logger_name = Column(String(150), nullable=True, index=True)
    environment = Column(String(50), nullable=True, index=True)

    # Performance metrics -- consideration given to cloud-hosting environments where resource usage and latency can be critical for cost management and user experience
    total_duration_ms = Column(Numeric(10, 2), nullable=False)
    db_latency_ms = Column(Numeric(10, 2), nullable=True)
    external_api_latency_ms = Column(Numeric(10, 2), nullable=True)
    app_logic_ms = Column(Numeric(10, 2), nullable=True)
    memory_used_mb = Column(Float, nullable=True, index=True)
    payload_size_kb = Column(Numeric(10, 2), nullable=True)
    is_slow = Column(SmallInteger, nullable=False, default=0)

    # Performance metrics for backend API calls
    endpoint = Column(String(255), nullable=True, index=True)
    method = Column(String(10), nullable=True, index=True)
    status_code = Column(SmallInteger, nullable=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    profile_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    autotask_ticket_id = Column(Integer, nullable=True, index=True)
    details = Column(JSONB, nullable=True)

    # Relationships
    request_trace = relationship("RequestTrace", back_populates="performance_logs")

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_perf_log_operation", "operation_name"),
        Index("idx_perf_log_service", "service_name"),
        Index("idx_perf_log_endpoint", "endpoint"),
        Index("idx_perf_log_duration", "total_duration_ms"),
        Index("idx_perf_log_memory", "memory_used_mb"),
        Index("idx_perf_log_tenant", "tenant_id"),
        Index("idx_perf_log_request_id", "request_id"),
    )


class ErrorLog(LogBase):
    """Dedicated table for error logs with detailed context."""

    __tablename__ = "error_logs"

    # ID fields
    error_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    occurred_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Error context and categorisation fields for error analysis and debugging
    error_type = Column(String(100), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    subsystem = Column(String(100), nullable=True, index=True)
    logger_name = Column(String(150), nullable=True, index=True)
    environment = Column(String(50), nullable=True, index=True)

    # Error details
    message = Column(Text, nullable=False)
    action = Column(String(200), nullable=True, index=True)
    stack_trace = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True, index=True)
    method = Column(String(10), nullable=True, index=True)
    status_code = Column(SmallInteger, nullable=True, index=True)

    request_id = Column(
        String(100),
        ForeignKey("request_trace.request_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )  # trace IDs across requests

    # Relation to tenant, profile and ticket for filtering through multi-tenancy system (if applicable)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    profile_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    autotask_ticket_id = Column(Integer, nullable=True, index=True)

    # Error severity and resolution
    severity = Column(
        String(20), nullable=False, index=True
    )  # i.e. critical, high, medium, low
    error_resolution = Column(
        Text, nullable=True
    )  # error resolution details, can be updated after the error is resolved for future reference
    details = Column(JSONB, nullable=True)

    # Relationships
    request_trace = relationship("RequestTrace", back_populates="error_logs")

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_error_log_type", "error_type"),
        Index("idx_error_log_service", "service_name"),
        Index("idx_error_log_request_id", "request_id"),
        Index("idx_error_log_tenant_id", "tenant_id"),
        Index("idx_error_log_profile_id", "profile_id"),
        Index("idx_error_log_severity", "severity"),
        Index("idx_error_log_resolution", "error_resolution"),
        Index("idx_error_log_occurred", "occurred_at"),
    )


class UIClickAnalyticsLog(LogBase):
    """Dedicated table for frontend user interaction logs. This captures user interactions in the UI for analytics and software insights."""

    __tablename__ = "ui_click_analytics_logs"

    # ID fields
    ui_click_log_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    occurred_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    request_id = Column(
        String(100),
        ForeignKey("request_trace.request_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )  # trace request ID across logs for correlation between frontend interactions and backend processing

    # Isolation of frontend interaction context (user and tenant-specific)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    profile_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Interaction details, isolating clicks to specific components for focused insights on user behavior and UI performance
    environment = Column(String(50), nullable=True, index=True)
    page_path = Column(
        String(255), nullable=True, index=True
    )  # i.e. 'Dashboard', 'TicketDetails' etc.
    component = Column(
        String(100), nullable=False, index=True
    )  # i.e. 'ticket-card', 'tickets-list-container' etc.
    action_type = Column(
        String(100), nullable=False, index=True
    )  # action type i.e. 'view', 'edit' , 'reassign category' etc.
    element_id = Column(
        String(150), nullable=True, index=True
    )  # specific element ID in the UI, useful for tracing interactions with specific UI elements
    duration_ms = Column(
        Numeric(10, 2), nullable=True
    )  # time take for intercation if applicable
    details = Column(JSONB, nullable=True)

    # Relationships
    request_trace = relationship("RequestTrace", back_populates="ui_click_logs")

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_ui_click_log_action", "action_type"),
        Index("idx_ui_click_log_component", "component"),
        Index("idx_ui_click_log_request_id", "request_id"),
        Index("idx_ui_click_log_tenant_id", "tenant_id"),
        Index("idx_ui_click_log_profile_id", "profile_id"),
        Index("idx_ui_click_log_occurred", "occurred_at"),
        Index("idx_ui_click_log_created", "created_at"),
        Index("idx_ui_click_log_page_component", "page_path", "component"),
    )

"""SQLAlchemy models for a dedicated durable logging database."""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..log_database import LogBase


class RequestTrace(LogBase):
    """Correlation root shared by request-linked log tables."""

    __tablename__ = "request_trace"

    request_id = Column(String(100), primary_key=True, nullable=False)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source = Column(String(50), nullable=True)
    environment = Column(String(50), nullable=True)

    application_logs = relationship("ApplicationLog", back_populates="request_trace")
    performance_logs = relationship("PerformanceLog", back_populates="request_trace")
    error_logs = relationship("ErrorLog", back_populates="request_trace")
    ui_click_logs = relationship("UIClickAnalyticsLog", back_populates="request_trace")


class ApplicationLog(LogBase):
    """Main structured application event table."""

    __tablename__ = "application_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    log_type = Column(String(50), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    subsystem = Column(String(100), nullable=False, index=True)
    action = Column(String(200), nullable=False, index=True)
    logger_name = Column(String(150), nullable=True, index=True)
    environment = Column(String(50), nullable=True, index=True)

    request_id = Column(
        String(100),
        ForeignKey("request_trace.request_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    profile_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    entity_type = Column(String(50), nullable=True, index=True)
    entity_id = Column(String(100), nullable=True, index=True)
    autotask_ticket_id = Column(Integer, nullable=True, index=True)

    endpoint = Column(String(255), nullable=True, index=True)
    method = Column(String(10), nullable=True, index=True)
    status_code = Column(SmallInteger, nullable=True, index=True)

    level = Column(String(20), nullable=False, index=True)
    outcome = Column(String(50), nullable=True, index=True)
    duration_ms = Column(Numeric(precision=10, scale=2), nullable=True)

    message = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)

    request_trace = relationship("RequestTrace", back_populates="application_logs")

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

    perf_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    request_id = Column(
        String(100),
        ForeignKey("request_trace.request_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    operation_name = Column(String(150), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    logger_name = Column(String(150), nullable=True, index=True)
    environment = Column(String(50), nullable=True, index=True)

    total_duration_ms = Column(Numeric(10, 2), nullable=False)
    db_latency_ms = Column(Numeric(10, 2), nullable=True)
    external_api_latency_ms = Column(Numeric(10, 2), nullable=True)
    app_logic_ms = Column(Numeric(10, 2), nullable=True)
    memory_used_mb = Column(Float, nullable=True, index=True)
    payload_size_kb = Column(Numeric(10, 2), nullable=True)
    is_slow = Column(SmallInteger, nullable=False, default=0)

    endpoint = Column(String(255), nullable=True, index=True)
    method = Column(String(10), nullable=True, index=True)
    status_code = Column(SmallInteger, nullable=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    profile_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    autotask_ticket_id = Column(Integer, nullable=True, index=True)
    details = Column(JSONB, nullable=True)

    request_trace = relationship("RequestTrace", back_populates="performance_logs")

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

    error_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    error_type = Column(String(100), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    subsystem = Column(String(100), nullable=True, index=True)
    logger_name = Column(String(150), nullable=True, index=True)
    environment = Column(String(50), nullable=True, index=True)
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
    ) # trace IDs across requests

    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    profile_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    autotask_ticket_id = Column(Integer, nullable=True, index=True)

    severity = Column(String(20), nullable=False, index=True)
    error_resolution = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)

    request_trace = relationship("RequestTrace", back_populates="error_logs")

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

    ui_click_log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    request_id = Column(
        String(100),
        ForeignKey("request_trace.request_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    profile_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    environment = Column(String(50), nullable=True, index=True)
    page_path = Column(String(255), nullable=True, index=True)
    component = Column(String(100), nullable=False, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    element_id = Column(String(150), nullable=True, index=True)
    duration_ms = Column(Numeric(10, 2), nullable=True)
    details = Column(JSONB, nullable=True)

    request_trace = relationship("RequestTrace", back_populates="ui_click_logs")

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
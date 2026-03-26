"""SQLAlchemy models for persisted AI operational ticket state."""

import uuid

from sqlalchemy import Column, Integer, Text, Index, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from ..database import Base


class TicketAIState(Base):
    """Persisted AI state for active or recently refreshed tickets."""

    __tablename__ = "ticket_ai_state"

    ticket_ai_state_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    autotask_ticket_id = Column(Integer, nullable=False)
    ticket_number = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    created = Column(Text, nullable=False)
    company = Column(Text, nullable=False)
    contact = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    issue_type = Column(Text, nullable=False)
    sub_issue_type = Column(Text, nullable=False)
    queue = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    due_date = Column(Text, nullable=False)
    primary_resource = Column(Text, nullable=True)
    secondary_resource = Column(Text, nullable=True)
    primary_profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profile.profile_id", ondelete="SET NULL"),
        nullable=True,
    )
    secondary_profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profile.profile_id", ondelete="SET NULL"),
        nullable=True,
    )
    category = Column(Text, nullable=False)
    confidence = Column(Integer, nullable=False)
    priority_label = Column(Text, nullable=False)
    priority_score = Column(Integer, nullable=False)
    classification_method = Column(Text, nullable=False)
    is_closed = Column(Boolean, nullable=False, default=False, server_default="false")
    refreshed_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_ticket_ai_state_tenant_ticket", "tenant_id", "autotask_ticket_id", unique=True),
        Index("ix_ticket_ai_state_tenant_status", "tenant_id", "status"),
        Index("ix_ticket_ai_state_tenant_company", "tenant_id", "company"),
        Index("ix_ticket_ai_state_tenant_category", "tenant_id", "category"),
        Index("ix_ticket_ai_state_tenant_closed", "tenant_id", "is_closed"),
        Index("ix_ticket_ai_state_tenant_primary_profile", "tenant_id", "primary_profile_id"),
        Index("ix_ticket_ai_state_tenant_secondary_profile", "tenant_id", "secondary_profile_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<TicketAIState(tenant_id={self.tenant_id}, autotask_ticket_id={self.autotask_ticket_id}, "
            f"category='{self.category}', priority='{self.priority_label}')>"
        )

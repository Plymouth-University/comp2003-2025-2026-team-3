"""Pydantic schemas for AI operational state endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TicketAIStateResponse(BaseModel):
    ticket_ai_state_id: UUID
    tenant_id: UUID
    autotask_ticket_id: int
    ticket_number: str
    status: str
    created: str
    company: str
    contact: str
    title: str
    description: str
    issue_type: str
    sub_issue_type: str
    queue: str
    source: str
    due_date: str
    primary_resource: Optional[str] = None
    secondary_resource: Optional[str] = None
    primary_profile_id: Optional[UUID] = None
    secondary_profile_id: Optional[UUID] = None
    category: str
    confidence: int
    priority_label: str
    priority_score: int
    classification_method: str
    is_closed: bool
    refreshed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketAIRefreshRequest(BaseModel):
    include_closed: bool = Field(
        default=False,
        description="Whether closed tickets should be retained in AI operational state.",
    )
    limit: int = Field(default=250, ge=1, le=1000)


class TicketAIRefreshResponse(BaseModel):
    refreshed_count: int
    removed_count: int
    mapped_primary_count: int
    mapped_secondary_count: int
    include_closed: bool
    refreshed_at: datetime

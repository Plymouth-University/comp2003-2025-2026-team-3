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
    manual_override_profile_id: Optional[UUID] = None
    manual_override_set_by_profile_id: Optional[UUID] = None
    manual_override_reason: Optional[str] = None
    manual_override_set_at: Optional[datetime] = None
    manual_override_display_name: Optional[str] = None
    ai_managed_profile_id: Optional[UUID] = None
    ai_managed_reason: Optional[str] = None
    ai_managed_set_at: Optional[datetime] = None
    ai_managed_display_name: Optional[str] = None
    effective_assignee_display_name: Optional[str] = None
    manual_edit_fields: list[str] = Field(default_factory=list)
    manual_edit_set_by_profile_id: Optional[UUID] = None
    manual_edit_set_at: Optional[datetime] = None
    category: str
    category_override_reason: Optional[str] = None
    category_override_set_at: Optional[datetime] = None
    confidence: int
    priority_label: str
    priority_score: int
    classification_method: str
    is_closed: bool
    reason_closed: Optional[str] = None
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
    apply_oversight: bool = Field(
        default=True,
        description="Whether to run AI oversight auto-assignment rules after refresh.",
    )
    oversight_queue: str = Field(
        default="MS - SecOps",
        description="Queue name used for oversight evaluation.",
    )


class TicketAIRefreshResponse(BaseModel):
    refreshed_count: int
    removed_count: int
    mapped_primary_count: int
    mapped_secondary_count: int
    include_closed: bool
    refreshed_at: datetime


class TicketAIStateUpdateRequest(BaseModel):
    ticket_number: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=100)
    created: Optional[str] = Field(default=None, max_length=100)
    company: Optional[str] = Field(default=None, max_length=500)
    contact: Optional[str] = Field(default=None, max_length=500)
    title: Optional[str] = Field(default=None, max_length=1000)
    description: Optional[str] = None
    issue_type: Optional[str] = Field(default=None, max_length=500)
    sub_issue_type: Optional[str] = Field(default=None, max_length=500)
    queue: Optional[str] = Field(default=None, max_length=500)
    source: Optional[str] = Field(default=None, max_length=500)
    due_date: Optional[str] = Field(default=None, max_length=100)
    primary_resource: Optional[str] = Field(default=None, max_length=500)
    secondary_resource: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = Field(default=None, max_length=500)
    confidence: Optional[int] = Field(default=None, ge=0, le=100)
    priority_label: Optional[str] = Field(default=None, max_length=100)
    priority_score: Optional[int] = Field(default=None, ge=0)
    classification_method: Optional[str] = Field(default=None, max_length=500)


class TicketAIStateCloseRequest(BaseModel):
    reason_closed: str = Field(min_length=1, max_length=1000)


class TicketCategoryOverrideRequest(BaseModel):
    category: str = Field(min_length=1, max_length=500)
    category_override_reason: str = Field(min_length=1, max_length=1000)


class AIOversightRunResponse(BaseModel):
    tenant_id: UUID
    queue: str
    evaluated_count: int
    auto_assigned_count: int
    auto_moved_count: int
    protected_in_progress_count: int
    unchanged_count: int
    run_at: datetime


class AssignmentRecommendationCandidateResponse(BaseModel):
    profile_id: UUID
    display_name: str
    matched_specialism_keys: list[str]
    score: int
    reasons: list[str]
    is_current_primary: bool
    is_current_secondary: bool
    open_primary_ticket_count: int
    open_secondary_ticket_count: int
    high_priority_ticket_count: int
    weighted_open_load: float


class TicketAssignmentRecommendationResponse(BaseModel):
    autotask_ticket_id: int
    category: str
    category_label: str
    recommended_profile_id: Optional[UUID] = None
    recommended_display_name: Optional[str] = None
    effective_profile_id: Optional[UUID] = None
    effective_display_name: Optional[str] = None
    has_manual_override: bool = False
    manual_override_profile_id: Optional[UUID] = None
    manual_override_display_name: Optional[str] = None
    manual_override_reason: Optional[str] = None
    manual_override_set_at: Optional[datetime] = None
    recommendation_summary: str
    candidates: list[AssignmentRecommendationCandidateResponse]


class TicketAssignmentOverrideRequest(BaseModel):
    profile_id: UUID
    reason: Optional[str] = Field(default=None, max_length=1000)

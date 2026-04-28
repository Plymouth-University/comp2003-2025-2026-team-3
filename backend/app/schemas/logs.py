"""Schemas for durable log ingestion endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UIClickLogCreate(BaseModel):
    """Frontend interaction event sent to the durable logging API."""

    action_type: str = Field(min_length=1, max_length=100)
    component: str = Field(min_length=1, max_length=100)
    page_path: str = Field(min_length=1, max_length=255)
    element_id: str | None = Field(default=None, max_length=150)
    duration_ms: float | None = Field(default=None, ge=0)
    details: dict[str, Any] | None = None
    occurred_at: datetime | None = None

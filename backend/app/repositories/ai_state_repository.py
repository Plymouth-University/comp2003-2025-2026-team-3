"""Repository layer for persisted AI ticket state."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Optional
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.ai_state import TicketAIState


class TicketAIStateRepository:
    """Data access layer for AI ticket state."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_ticket_id(
        self,
        tenant_id: UUID,
        autotask_ticket_id: int,
    ) -> Optional[TicketAIState]:
        query = select(TicketAIState).where(
            and_(
                TicketAIState.tenant_id == tenant_id,
                TicketAIState.autotask_ticket_id == autotask_ticket_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_for_tenant(
        self,
        tenant_id: UUID,
        include_closed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TicketAIState]:
        query = (
            select(TicketAIState)
            .where(TicketAIState.tenant_id == tenant_id)
            .order_by(TicketAIState.priority_score.desc(), TicketAIState.refreshed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if not include_closed:
            query = query.where(TicketAIState.is_closed.is_(False))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_for_queue(
        self,
        tenant_id: UUID,
        queue: str,
        include_closed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TicketAIState]:
        query = (
            select(TicketAIState)
            .where(
                and_(
                    TicketAIState.tenant_id == tenant_id,
                    TicketAIState.queue == queue,
                )
            )
            .order_by(TicketAIState.priority_score.desc(), TicketAIState.refreshed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if not include_closed:
            query = query.where(TicketAIState.is_closed.is_(False))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_for_profile_assignment(
        self,
        tenant_id: UUID,
        profile_id: UUID,
        assignment_role: str,
        include_closed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TicketAIState]:
        query = select(TicketAIState).where(TicketAIState.tenant_id == tenant_id)

        if assignment_role == "primary":
            query = query.where(TicketAIState.primary_profile_id == profile_id)
        elif assignment_role == "secondary":
            query = query.where(TicketAIState.secondary_profile_id == profile_id)
        elif assignment_role == "assigned":
            query = query.where(
                or_(
                    TicketAIState.primary_profile_id == profile_id,
                    TicketAIState.secondary_profile_id == profile_id,
                )
            )
        else:
            raise ValueError(f"Unsupported assignment role: {assignment_role}")

        if not include_closed:
            query = query.where(TicketAIState.is_closed.is_(False))

        query = (
            query.order_by(TicketAIState.priority_score.desc(), TicketAIState.refreshed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def upsert_ticket_state(
        self,
        tenant_id: UUID,
        ticket_payload: dict,
        ai_payload: dict,
        primary_profile_id: UUID | None = None,
        secondary_profile_id: UUID | None = None,
    ) -> TicketAIState:
        existing = await self.get_by_ticket_id(tenant_id, ticket_payload["autotask_ticket_id"])
        now = datetime.now(timezone.utc)

        mapped_fields = {
            "tenant_id": tenant_id,
            "autotask_ticket_id": ticket_payload["autotask_ticket_id"],
            "ticket_number": ticket_payload["ticket_number"],
            "status": ticket_payload["status"],
            "company": ticket_payload["company"],
            "contact": ticket_payload["contact"],
            "title": ticket_payload["title"],
            "description": ticket_payload["description"],
            "issue_type": ticket_payload["issue_type"],
            "sub_issue_type": ticket_payload["sub_issue_type"],
            "queue": ticket_payload["queue"],
            "source": ticket_payload["source"],
            "due_date": ticket_payload["due_date"],
            "primary_resource": ticket_payload.get("primary_resource"),
            "secondary_resource": ticket_payload.get("secondary_resource"),
            "primary_profile_id": primary_profile_id,
            "secondary_profile_id": secondary_profile_id,
            "category": ai_payload["category"],
            "confidence": int(ai_payload["confidence"]),
            "priority_label": ai_payload["priority"],
            "priority_score": int(ai_payload["priority_score"]),
            "classification_method": ai_payload["method"],
            "is_closed": str(ticket_payload["status"]).lower() == "closed",
            "refreshed_at": now,
        }

        if existing:
            for key, value in mapped_fields.items():
                setattr(existing, key, value)
            await self.db.flush()
            return existing

        state = TicketAIState(**mapped_fields)
        self.db.add(state)
        await self.db.flush()
        return state

    async def delete_missing_active_tickets(
        self,
        tenant_id: UUID,
        retained_autotask_ticket_ids: Iterable[int],
    ) -> int:
        retained_ids = list(retained_autotask_ticket_ids)
        query = delete(TicketAIState).where(TicketAIState.tenant_id == tenant_id)
        if retained_ids:
            query = query.where(TicketAIState.autotask_ticket_id.not_in(retained_ids))
        result = await self.db.execute(query)
        return result.rowcount or 0

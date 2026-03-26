"""Business logic for persisted AI ticket state and refresh operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..providers.fake_autotask import FakeAutotaskProvider
from ..repositories.ai_state_repository import TicketAIStateRepository
from ..schemas.ai_state import (
    TicketAIRefreshResponse,
    TicketAIStateResponse,
)
from .ai import categorise_ticket


class AIStateService:
    """Service layer for AI operational state."""

    def __init__(
        self,
        db: AsyncSession,
        provider: Optional[FakeAutotaskProvider] = None,
    ):
        self.db = db
        self.provider = provider or FakeAutotaskProvider()
        self.repository = TicketAIStateRepository(db)

    async def refresh_ticket_states(
        self,
        tenant_id: UUID,
        include_closed: bool = False,
        limit: int = 250,
    ) -> TicketAIRefreshResponse:
        tickets = self.provider.get_tickets()[:limit]
        if not include_closed:
            tickets = [ticket for ticket in tickets if str(ticket.status).lower() != "closed"]

        retained_ids: list[int] = []
        for ticket in tickets:
            ticket_payload = ticket.model_dump()
            ai_payload = categorise_ticket(ticket_payload)
            await self.repository.upsert_ticket_state(tenant_id, ticket_payload, ai_payload)
            retained_ids.append(ticket.autotask_ticket_id)

        removed_count = await self.repository.delete_missing_active_tickets(tenant_id, retained_ids)

        return TicketAIRefreshResponse(
            refreshed_count=len(retained_ids),
            removed_count=removed_count,
            include_closed=include_closed,
            refreshed_at=datetime.now(timezone.utc),
        )

    async def list_ticket_states(
        self,
        tenant_id: UUID,
        include_closed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TicketAIStateResponse]:
        states = await self.repository.list_for_tenant(
            tenant_id=tenant_id,
            include_closed=include_closed,
            limit=limit,
            offset=offset,
        )
        return [TicketAIStateResponse.model_validate(state) for state in states]

    async def get_ticket_state(
        self,
        tenant_id: UUID,
        autotask_ticket_id: int,
    ) -> Optional[TicketAIStateResponse]:
        state = await self.repository.get_by_ticket_id(tenant_id, autotask_ticket_id)
        if not state:
            return None
        return TicketAIStateResponse.model_validate(state)

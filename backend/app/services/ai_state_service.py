"""Business logic for persisted AI ticket state and refresh operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..providers.fake_autotask import FakeAutotaskProvider
from ..repositories.ai_state_repository import TicketAIStateRepository
from ..repositories.profile_repository import ProfileRepository
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
        self.profile_repository = ProfileRepository(db)

    async def refresh_ticket_states(
        self,
        tenant_id: UUID,
        include_closed: bool = False,
        limit: int = 250,
    ) -> TicketAIRefreshResponse:
        tickets = self.provider.get_tickets()[:limit]
        if not include_closed:
            tickets = [ticket for ticket in tickets if str(ticket.status).lower() != "closed"]

        resource_names = {
            resource_name
            for ticket in tickets
            for resource_name in (ticket.primary_resource, ticket.secondary_resource)
            if resource_name
        }
        profiles = await self.profile_repository.get_profiles_by_display_names(
            tenant_id,
            sorted(resource_names),
        )
        profile_map = {
            profile.display.display_name.strip().lower(): profile.profile_id
            for profile in profiles
            if profile.display and profile.display.display_name
        }

        retained_ids: list[int] = []
        mapped_primary_count = 0
        mapped_secondary_count = 0
        for ticket in tickets:
            ticket_payload = ticket.model_dump()
            ai_payload = categorise_ticket(ticket_payload)
            primary_profile_id = None
            secondary_profile_id = None

            if ticket.primary_resource:
                primary_profile_id = profile_map.get(ticket.primary_resource.strip().lower())
                mapped_primary_count += int(primary_profile_id is not None)
            if ticket.secondary_resource:
                secondary_profile_id = profile_map.get(ticket.secondary_resource.strip().lower())
                mapped_secondary_count += int(secondary_profile_id is not None)

            await self.repository.upsert_ticket_state(
                tenant_id,
                ticket_payload,
                ai_payload,
                primary_profile_id=primary_profile_id,
                secondary_profile_id=secondary_profile_id,
            )
            retained_ids.append(ticket.autotask_ticket_id)

        removed_count = await self.repository.delete_missing_active_tickets(tenant_id, retained_ids)

        return TicketAIRefreshResponse(
            refreshed_count=len(retained_ids),
            removed_count=removed_count,
            mapped_primary_count=mapped_primary_count,
            mapped_secondary_count=mapped_secondary_count,
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

    async def list_queue_ticket_states(
        self,
        tenant_id: UUID,
        queue: str,
        include_closed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TicketAIStateResponse]:
        states = await self.repository.list_for_queue(
            tenant_id=tenant_id,
            queue=queue,
            include_closed=include_closed,
            limit=limit,
            offset=offset,
        )
        return [TicketAIStateResponse.model_validate(state) for state in states]

    async def list_profile_ticket_states(
        self,
        tenant_id: UUID,
        profile_id: UUID,
        assignment_role: str,
        include_closed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TicketAIStateResponse]:
        states = await self.repository.list_for_profile_assignment(
            tenant_id=tenant_id,
            profile_id=profile_id,
            assignment_role=assignment_role,
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

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
    TicketAIStateUpdateRequest,
)
from .ai import categorise_ticket
from .ai_oversight_service import AIOversightService


class AIStateService:
    """Service layer for AI operational state."""

    def __init__(
        self,
        ai_db: AsyncSession,
        profile_db: AsyncSession,
        provider: Optional[FakeAutotaskProvider] = None,
    ):
        self.ai_db = ai_db
        self.profile_db = profile_db
        self.provider = provider or FakeAutotaskProvider()
        self.repository = TicketAIStateRepository(ai_db)
        self.profile_repository = ProfileRepository(profile_db)

    async def apply_primary_assignment(
        self,
        tenant_id: UUID,
        autotask_ticket_id: int,
        profile_id: UUID,
    ) -> TicketAIStateResponse | None:
        """Persist a primary assignment to provider source and mirrored AI-state row."""
        profile_rows = await self.profile_repository.get_profiles_by_ids(
            tenant_id, [profile_id]
        )
        if not profile_rows:
            raise ValueError(f"Profile not found for tenant: {profile_id}")

        profile = profile_rows[0]
        if profile.display is None or not profile.display.display_name:
            raise ValueError(f"Profile has no display name: {profile_id}")

        display_name = profile.display.display_name
        self.provider.set_primary_resource(autotask_ticket_id, display_name)

        updated = await self.repository.set_primary_assignment(
            tenant_id=tenant_id,
            autotask_ticket_id=autotask_ticket_id,
            primary_resource=display_name,
            primary_profile_id=profile_id,
        )
        if updated is None:
            return None

        responses = await self._build_ticket_state_responses(tenant_id, [updated])
        return responses[0] if responses else None

    async def refresh_ticket_states(
        self,
        tenant_id: UUID,
        include_closed: bool = False,
        limit: int = 250,
        apply_oversight: bool = True,
        oversight_queue: str = "MS - SecOps",
    ) -> TicketAIRefreshResponse:
        tickets = self.provider.get_tickets()[:limit]
        if not include_closed:
            tickets = [
                ticket for ticket in tickets if str(ticket.status).lower() != "closed"
            ]

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
                primary_profile_id = profile_map.get(
                    ticket.primary_resource.strip().lower()
                )
                mapped_primary_count += int(primary_profile_id is not None)
            if ticket.secondary_resource:
                secondary_profile_id = profile_map.get(
                    ticket.secondary_resource.strip().lower()
                )
                mapped_secondary_count += int(secondary_profile_id is not None)

            await self.repository.upsert_ticket_state(
                tenant_id,
                ticket_payload,
                ai_payload,
                primary_profile_id=primary_profile_id,
                secondary_profile_id=secondary_profile_id,
            )
            retained_ids.append(ticket.autotask_ticket_id)

        removed_count = await self.repository.delete_missing_active_tickets(
            tenant_id, retained_ids
        )

        if apply_oversight:
            oversight_service = AIOversightService(self.ai_db, self.profile_db)
            await oversight_service.run_for_tenant(
                tenant_id=tenant_id,
                queue=oversight_queue,
            )

        return TicketAIRefreshResponse(
            refreshed_count=len(retained_ids),
            removed_count=removed_count,
            mapped_primary_count=mapped_primary_count,
            mapped_secondary_count=mapped_secondary_count,
            include_closed=include_closed,
            refreshed_at=datetime.now(timezone.utc),
        )

    async def _build_ticket_state_responses(
        self,
        tenant_id: UUID,
        states,
    ) -> list[TicketAIStateResponse]:
        override_profile_ids = [
            state.manual_override_profile_id
            for state in states
            if state.manual_override_profile_id is not None
        ]
        ai_managed_profile_ids = [
            state.ai_managed_profile_id
            for state in states
            if state.ai_managed_profile_id is not None
        ]
        profiles = await self.profile_repository.get_profiles_by_ids(
            tenant_id,
            list({*override_profile_ids, *ai_managed_profile_ids}),
        )
        display_name_by_profile_id = {
            profile.profile_id: profile.display.display_name
            for profile in profiles
            if profile.display is not None
        }

        responses: list[TicketAIStateResponse] = []
        for state in states:
            payload = TicketAIStateResponse.model_validate(state).model_dump()
            manual_override_display_name = display_name_by_profile_id.get(
                state.manual_override_profile_id
            )
            ai_managed_display_name = display_name_by_profile_id.get(
                state.ai_managed_profile_id
            )
            payload["manual_override_display_name"] = manual_override_display_name
            payload["ai_managed_display_name"] = ai_managed_display_name
            payload["effective_assignee_display_name"] = (
                manual_override_display_name
                or ai_managed_display_name
                or state.primary_resource
                or state.secondary_resource
            )
            responses.append(TicketAIStateResponse(**payload))
        return responses

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
        return await self._build_ticket_state_responses(tenant_id, states)

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
        return await self._build_ticket_state_responses(tenant_id, states)

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
        return await self._build_ticket_state_responses(tenant_id, states)

    async def get_ticket_state(
        self,
        tenant_id: UUID,
        autotask_ticket_id: int,
    ) -> Optional[TicketAIStateResponse]:
        state = await self.repository.get_by_ticket_id(tenant_id, autotask_ticket_id)
        if not state:
            return None
        responses = await self._build_ticket_state_responses(tenant_id, [state])
        return responses[0] if responses else None

    async def update_ticket_state(
        self,
        tenant_id: UUID,
        autotask_ticket_id: int,
        update_request: TicketAIStateUpdateRequest,
        set_by_profile_id: UUID,
    ) -> Optional[TicketAIStateResponse]:
        updates = update_request.model_dump(exclude_unset=True)
        if not updates:
            return await self.get_ticket_state(tenant_id, autotask_ticket_id)

        nullable_fields = {"primary_resource", "secondary_resource"}
        null_fields = [
            field for field, value in updates.items()
            if value is None and field not in nullable_fields
        ]
        if null_fields:
            raise ValueError(f"Fields cannot be null: {', '.join(null_fields)}")

        updated = await self.repository.update_ticket_state(
            tenant_id=tenant_id,
            autotask_ticket_id=autotask_ticket_id,
            updates=updates,
            set_by_profile_id=set_by_profile_id,
        )
        if updated is None:
            return None

        responses = await self._build_ticket_state_responses(tenant_id, [updated])
        return responses[0] if responses else None

    async def set_manual_override(
        self,
        tenant_id: UUID,
        autotask_ticket_id: int,
        override_profile_id: UUID,
        set_by_profile_id: UUID,
        reason: str | None = None,
    ):
        updated = await self.repository.set_manual_override(
            tenant_id=tenant_id,
            autotask_ticket_id=autotask_ticket_id,
            override_profile_id=override_profile_id,
            set_by_profile_id=set_by_profile_id,
            reason=reason,
        )
        if updated is None:
            return None

        await self.apply_primary_assignment(
            tenant_id=tenant_id,
            autotask_ticket_id=autotask_ticket_id,
            profile_id=override_profile_id,
        )
        return updated

    async def clear_manual_override(
        self,
        tenant_id: UUID,
        autotask_ticket_id: int,
    ):
        return await self.repository.clear_manual_override(
            tenant_id=tenant_id,
            autotask_ticket_id=autotask_ticket_id,
        )

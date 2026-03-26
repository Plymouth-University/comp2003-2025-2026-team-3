"""Continuous AI oversight rules for queue-level ticket assignment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..providers.fake_autotask import FakeAutotaskProvider
from ..repositories.ai_state_repository import TicketAIStateRepository
from ..repositories.profile_repository import ProfileRepository
from ..schemas.ai_state import AIOversightRunResponse
from .ai_assignment_service import AIAssignmentService


UNSTARTED_STATUSES = {
    "new",
    "immediate review rqd",
    "technician response rqd",
}


@dataclass
class _Decision:
    action: str
    reason: str


class AIOversightService:
    """Runs queue-wide recommendation enforcement with explicit safety rules."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = FakeAutotaskProvider()
        self.ai_state_repository = TicketAIStateRepository(db)
        self.profile_repository = ProfileRepository(db)
        self.assignment_service = AIAssignmentService(db)

    async def run_for_tenant(
        self,
        tenant_id: UUID,
        queue: str,
    ) -> AIOversightRunResponse:
        states = await self.ai_state_repository.list_for_queue(
            tenant_id=tenant_id,
            queue=queue,
            include_closed=False,
            limit=1000,
            offset=0,
        )

        auto_assigned_count = 0
        auto_moved_count = 0
        protected_in_progress_count = 0
        unchanged_count = 0

        for state in states:
            decision = await self._decide_for_ticket(tenant_id, state.autotask_ticket_id)
            if decision.action == "auto_assign":
                auto_assigned_count += 1
            elif decision.action == "auto_move":
                auto_moved_count += 1
            elif decision.action == "protected":
                protected_in_progress_count += 1
            else:
                unchanged_count += 1

        return AIOversightRunResponse(
            tenant_id=tenant_id,
            queue=queue,
            evaluated_count=len(states),
            auto_assigned_count=auto_assigned_count,
            auto_moved_count=auto_moved_count,
            protected_in_progress_count=protected_in_progress_count,
            unchanged_count=unchanged_count,
            run_at=datetime.now(timezone.utc),
        )

    async def _decide_for_ticket(
        self,
        tenant_id: UUID,
        autotask_ticket_id: int,
    ) -> _Decision:
        state = await self.ai_state_repository.get_by_ticket_id(tenant_id, autotask_ticket_id)
        if state is None or state.is_closed:
            return _Decision(action="unchanged", reason="Ticket unavailable or closed.")

        if state.manual_override_profile_id is not None:
            await self.ai_state_repository.clear_ai_managed_assignment(tenant_id, autotask_ticket_id)
            return _Decision(action="unchanged", reason="Manual override present.")

        recommendation = await self.assignment_service.recommend_for_ticket(tenant_id, autotask_ticket_id)
        recommended_profile_id = recommendation.recommended_profile_id if recommendation is not None else None
        recommended_display_name = recommendation.recommended_display_name if recommendation is not None else None

        if recommended_profile_id is None:
            fallback_profile_id, fallback_display_name = await self._fallback_profile_for_unassigned(tenant_id)
            recommended_profile_id = fallback_profile_id
            recommended_display_name = fallback_display_name

        if recommended_profile_id is None:
            await self.ai_state_repository.clear_ai_managed_assignment(tenant_id, autotask_ticket_id)
            return _Decision(action="unchanged", reason="No active profile candidates available.")

        status_normalized = (state.status or "").strip().lower()
        is_started = status_normalized not in UNSTARTED_STATUSES

        # Hard requirement: never leave a ticket without a primary owner.
        if state.primary_profile_id is None:
            await self._apply_primary_assignment(
                tenant_id=tenant_id,
                autotask_ticket_id=autotask_ticket_id,
                profile_id=recommended_profile_id,
                display_name_hint=recommended_display_name,
            )
            await self.ai_state_repository.set_ai_managed_assignment(
                tenant_id=tenant_id,
                autotask_ticket_id=autotask_ticket_id,
                profile_id=recommended_profile_id,
                reason=(
                    "AI auto-assigned because the ticket has no primary resource. "
                    f"Selected {recommended_display_name or 'best candidate'} by specialism/workload scoring."
                ),
            )
            return _Decision(action="auto_assign", reason="No primary resource present.")

        if is_started:
            await self.ai_state_repository.clear_ai_managed_assignment(tenant_id, autotask_ticket_id)
            return _Decision(action="protected", reason="Ticket already started; auto-move blocked.")

        incumbent_profile_id = state.primary_profile_id
        if incumbent_profile_id == recommended_profile_id:
            await self.ai_state_repository.clear_ai_managed_assignment(tenant_id, autotask_ticket_id)
            return _Decision(action="unchanged", reason="Current assignment matches recommendation.")

        if recommendation is None:
            await self.ai_state_repository.clear_ai_managed_assignment(tenant_id, autotask_ticket_id)
            return _Decision(action="unchanged", reason="No recommendation payload to compare.")

        top_score = recommendation.candidates[0].score if recommendation.candidates else 0
        incumbent_score = next(
            (candidate.score for candidate in recommendation.candidates if candidate.profile_id == incumbent_profile_id),
            -1,
        )

        # Move only when recommendation materially outranks incumbent.
        if top_score <= incumbent_score:
            await self.ai_state_repository.clear_ai_managed_assignment(tenant_id, autotask_ticket_id)
            return _Decision(action="unchanged", reason="Incumbent score is not lower than recommended.")

        await self.ai_state_repository.set_ai_managed_assignment(
            tenant_id=tenant_id,
            autotask_ticket_id=autotask_ticket_id,
            profile_id=recommended_profile_id,
            reason=(
                "AI auto-moved assignment before work started because another analyst scored higher "
                "for this ticket's category/company/workload profile."
            ),
        )
        await self._apply_primary_assignment(
            tenant_id=tenant_id,
            autotask_ticket_id=autotask_ticket_id,
            profile_id=recommended_profile_id,
            display_name_hint=recommended_display_name,
        )
        return _Decision(action="auto_move", reason="Moved to better-scored candidate before start.")

    async def _fallback_profile_for_unassigned(
        self,
        tenant_id: UUID,
    ) -> tuple[UUID | None, str | None]:
        profiles = await self.profile_repository.get_profiles_by_tenant_with_specialisms(
            tenant_id=tenant_id,
            status="active",
        )
        profiles = [profile for profile in profiles if profile.display is not None]
        if not profiles:
            return None, None

        active_tickets = await self.ai_state_repository.list_active_tickets_for_tenant(tenant_id)
        load_by_profile: dict[UUID, float] = {profile.profile_id: 0.0 for profile in profiles}

        for ticket in active_tickets:
            if ticket.primary_profile_id in load_by_profile:
                load_by_profile[ticket.primary_profile_id] += 1.0
                if ticket.priority_label in {"High", "Critical"}:
                    load_by_profile[ticket.primary_profile_id] += 0.75
            if ticket.secondary_profile_id in load_by_profile:
                load_by_profile[ticket.secondary_profile_id] += 0.5
                if ticket.priority_label in {"High", "Critical"}:
                    load_by_profile[ticket.secondary_profile_id] += 0.25

        least_loaded = min(
            profiles,
            key=lambda profile: (load_by_profile.get(profile.profile_id, 0.0), profile.display.display_name.lower()),
        )
        return least_loaded.profile_id, least_loaded.display.display_name

    async def _apply_primary_assignment(
        self,
        tenant_id: UUID,
        autotask_ticket_id: int,
        profile_id: UUID,
        display_name_hint: str | None = None,
    ) -> None:
        display_name = display_name_hint
        if not display_name:
            profile_rows = await self.profile_repository.get_profiles_by_ids(tenant_id, [profile_id])
            if not profile_rows or profile_rows[0].display is None:
                raise ValueError(f"Cannot resolve display name for profile {profile_id}")
            display_name = profile_rows[0].display.display_name

        self.provider.set_primary_resource(autotask_ticket_id, display_name)
        await self.ai_state_repository.set_primary_assignment(
            tenant_id=tenant_id,
            autotask_ticket_id=autotask_ticket_id,
            primary_resource=display_name,
            primary_profile_id=profile_id,
        )

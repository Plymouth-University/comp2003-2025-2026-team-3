"""Recommendation logic for specialism-aware ticket assignment."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.ai_state_repository import TicketAIStateRepository
from ..repositories.profile_repository import ProfileRepository
from ..schemas.ai_state import (
    AssignmentRecommendationCandidateResponse,
    TicketAssignmentRecommendationResponse,
)
from .ai import list_available_categories


class AIAssignmentService:
    """Provide explainable assignment recommendations from persisted AI ticket state."""

    def __init__(self, ai_db: AsyncSession, profile_db: AsyncSession):
        self.ai_db = ai_db
        self.profile_db = profile_db
        self.ai_state_repository = TicketAIStateRepository(ai_db)
        self.profile_repository = ProfileRepository(profile_db)

    async def recommend_for_ticket(
        self,
        tenant_id: UUID,
        autotask_ticket_id: int,
    ) -> TicketAssignmentRecommendationResponse | None:
        ticket_state = await self.ai_state_repository.get_by_ticket_id(tenant_id, autotask_ticket_id)
        if ticket_state is None:
            return None

        categories = {item["key"]: item["label"] for item in list_available_categories()}
        category_label = categories.get(ticket_state.category, ticket_state.category)
        same_company_tickets = await self.ai_state_repository.list_active_company_tickets(
            tenant_id=tenant_id,
            company=ticket_state.company,
            exclude_autotask_ticket_id=ticket_state.autotask_ticket_id,
        )
        active_tickets = await self.ai_state_repository.list_active_tickets_for_tenant(tenant_id)

        profiles = await self.profile_repository.get_profiles_by_tenant_with_specialisms(
            tenant_id=tenant_id,
            status="active",
        )
        active_profile_ids = {profile.profile_id for profile in profiles}

        open_primary_counts: dict[UUID, int] = defaultdict(int)
        open_secondary_counts: dict[UUID, int] = defaultdict(int)
        high_priority_counts: dict[UUID, int] = defaultdict(int)
        weighted_loads: dict[UUID, float] = defaultdict(float)

        for active_ticket in active_tickets:
            is_high_priority = active_ticket.priority_label in {"High", "Critical"}
            if active_ticket.primary_profile_id in active_profile_ids:
                primary_profile_id = active_ticket.primary_profile_id
                open_primary_counts[primary_profile_id] += 1
                weighted_loads[primary_profile_id] += 1.0
                if is_high_priority:
                    high_priority_counts[primary_profile_id] += 1
                    weighted_loads[primary_profile_id] += 0.75
            if active_ticket.secondary_profile_id in active_profile_ids:
                secondary_profile_id = active_ticket.secondary_profile_id
                open_secondary_counts[secondary_profile_id] += 1
                weighted_loads[secondary_profile_id] += 0.5
                if is_high_priority:
                    high_priority_counts[secondary_profile_id] += 1
                    weighted_loads[secondary_profile_id] += 0.25

        average_weighted_load = (
            sum(weighted_loads.get(profile.profile_id, 0.0) for profile in profiles) / len(profiles)
            if profiles
            else 0.0
        )

        candidates: list[AssignmentRecommendationCandidateResponse] = []
        for profile in profiles:
            if profile.display is None:
                continue

            matched_specialism_keys: list[str] = []
            reasons: list[str] = []
            score = 0
            same_company_primary_count = 0
            same_company_secondary_count = 0
            open_primary_ticket_count = open_primary_counts.get(profile.profile_id, 0)
            open_secondary_ticket_count = open_secondary_counts.get(profile.profile_id, 0)
            high_priority_ticket_count = high_priority_counts.get(profile.profile_id, 0)
            weighted_open_load = weighted_loads.get(profile.profile_id, 0.0)

            for profile_specialism in profile.specialisms:
                specialism = profile_specialism.specialism
                if specialism is None or not specialism.is_active:
                    continue
                if profile_specialism.unassigned_at is not None:
                    continue

                if specialism.specialism_key == ticket_state.category:
                    matched_specialism_keys.append(specialism.specialism_key)
                    score += 100
                    reasons.append(
                        f"Matched ticket category '{category_label}' to specialism '{specialism.specialism_name}'."
                    )

            for company_ticket in same_company_tickets:
                if company_ticket.primary_profile_id == profile.profile_id:
                    same_company_primary_count += 1
                if company_ticket.secondary_profile_id == profile.profile_id:
                    same_company_secondary_count += 1

            if same_company_primary_count:
                continuity_score = min(60, 20 + (same_company_primary_count * 10))
                score += continuity_score
                reasons.append(
                    f"Already primary on {same_company_primary_count} other open ticket(s) for {ticket_state.company}."
                )

            if same_company_secondary_count:
                continuity_score = min(25, 5 + (same_company_secondary_count * 5))
                score += continuity_score
                reasons.append(
                    f"Already secondary on {same_company_secondary_count} other open ticket(s) for {ticket_state.company}."
                )

            if profile.profile_id == ticket_state.primary_profile_id:
                score += 30
                reasons.append("Already the current primary resource on this ticket.")
            elif profile.profile_id == ticket_state.secondary_profile_id:
                score += 15
                reasons.append("Already the current secondary resource on this ticket.")

            load_delta = weighted_open_load - average_weighted_load
            if load_delta > 0.5:
                workload_penalty = min(45, round(load_delta * 12))
                score -= workload_penalty
                reasons.append(
                    f"Workload penalty: {open_primary_ticket_count} primary, {open_secondary_ticket_count} secondary, "
                    f"and {high_priority_ticket_count} high-priority open ticket(s), which is above the current team average."
                )
            elif load_delta < -0.5:
                workload_bonus = min(20, round(abs(load_delta) * 8))
                score += workload_bonus
                reasons.append(
                    f"Workload bonus: {open_primary_ticket_count} primary, {open_secondary_ticket_count} secondary, "
                    f"and {high_priority_ticket_count} high-priority open ticket(s), which is below the current team average."
                )

            if score <= 0:
                continue

            candidates.append(
                AssignmentRecommendationCandidateResponse(
                    profile_id=profile.profile_id,
                    display_name=profile.display.display_name,
                    matched_specialism_keys=sorted(set(matched_specialism_keys)),
                    score=score,
                    reasons=reasons,
                    is_current_primary=profile.profile_id == ticket_state.primary_profile_id,
                    is_current_secondary=profile.profile_id == ticket_state.secondary_profile_id,
                    open_primary_ticket_count=open_primary_ticket_count,
                    open_secondary_ticket_count=open_secondary_ticket_count,
                    high_priority_ticket_count=high_priority_ticket_count,
                    weighted_open_load=round(weighted_open_load, 2),
                )
            )

        candidates.sort(
            key=lambda candidate: (
                -candidate.score,
                candidate.display_name.lower(),
            )
        )

        manual_override_profile_id = ticket_state.manual_override_profile_id
        manual_override_reason = ticket_state.manual_override_reason
        manual_override_set_at: datetime | None = ticket_state.manual_override_set_at
        manual_override_display_name: str | None = None

        if manual_override_profile_id is not None:
            manual_override_profile = next(
                (profile for profile in profiles if profile.profile_id == manual_override_profile_id and profile.display is not None),
                None,
            )
            if manual_override_profile is not None and manual_override_profile.display is not None:
                manual_override_display_name = manual_override_profile.display.display_name

        if not candidates:
            return TicketAssignmentRecommendationResponse(
                autotask_ticket_id=ticket_state.autotask_ticket_id,
                category=ticket_state.category,
                category_label=category_label,
                effective_profile_id=manual_override_profile_id,
                effective_display_name=manual_override_display_name,
                has_manual_override=manual_override_profile_id is not None,
                manual_override_profile_id=manual_override_profile_id,
                manual_override_display_name=manual_override_display_name,
                manual_override_reason=manual_override_reason,
                manual_override_set_at=manual_override_set_at,
                recommendation_summary=(
                    "No active profiles currently have a stored specialism match or same-company continuity signal for this ticket."
                ),
                candidates=[],
            )

        top_candidate = candidates[0]
        summary_reasons: list[str] = []
        if top_candidate.matched_specialism_keys:
            summary_reasons.append("their stored specialisms match the ticket category")
        if any("other open ticket" in reason for reason in top_candidate.reasons):
            summary_reasons.append(f"they are already handling {ticket_state.company} tickets")
        if top_candidate.is_current_primary:
            summary_reasons.append("they are already the current primary resource")
        elif top_candidate.is_current_secondary:
            summary_reasons.append("they are already the current secondary resource")
        if any("Workload bonus" in reason for reason in top_candidate.reasons):
            summary_reasons.append("their active workload is lighter than the current team average")
        elif any("Workload penalty" in reason for reason in top_candidate.reasons):
            summary_reasons.append("they still outranked others despite a heavier active workload")

        summary_text = ", and ".join(summary_reasons) if summary_reasons else "they received the highest recommendation score"
        effective_profile_id = manual_override_profile_id or top_candidate.profile_id
        effective_display_name = manual_override_display_name or top_candidate.display_name
        summary = f"Recommended {top_candidate.display_name} because {summary_text}."
        if manual_override_profile_id is not None and manual_override_display_name is not None:
            summary = (
                f"Manual override active for {manual_override_display_name}. "
                f"AI would otherwise recommend {top_candidate.display_name} because {summary_text}."
            )
        return TicketAssignmentRecommendationResponse(
            autotask_ticket_id=ticket_state.autotask_ticket_id,
            category=ticket_state.category,
            category_label=category_label,
            recommended_profile_id=top_candidate.profile_id,
            recommended_display_name=top_candidate.display_name,
            effective_profile_id=effective_profile_id,
            effective_display_name=effective_display_name,
            has_manual_override=manual_override_profile_id is not None,
            manual_override_profile_id=manual_override_profile_id,
            manual_override_display_name=manual_override_display_name,
            manual_override_reason=manual_override_reason,
            manual_override_set_at=manual_override_set_at,
            recommendation_summary=summary,
            candidates=candidates,
        )

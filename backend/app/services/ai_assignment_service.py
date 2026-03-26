"""Recommendation logic for specialism-aware ticket assignment."""

from __future__ import annotations

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

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_state_repository = TicketAIStateRepository(db)
        self.profile_repository = ProfileRepository(db)

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

        profiles = await self.profile_repository.get_profiles_by_tenant_with_specialisms(
            tenant_id=tenant_id,
            status="active",
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
                )
            )

        candidates.sort(
            key=lambda candidate: (
                -candidate.score,
                candidate.display_name.lower(),
            )
        )

        if not candidates:
            return TicketAssignmentRecommendationResponse(
                autotask_ticket_id=ticket_state.autotask_ticket_id,
                category=ticket_state.category,
                category_label=category_label,
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

        summary_text = ", and ".join(summary_reasons) if summary_reasons else "they received the highest recommendation score"
        return TicketAssignmentRecommendationResponse(
            autotask_ticket_id=ticket_state.autotask_ticket_id,
            category=ticket_state.category,
            category_label=category_label,
            recommended_profile_id=top_candidate.profile_id,
            recommended_display_name=top_candidate.display_name,
            recommendation_summary=(
                f"Recommended {top_candidate.display_name} because {summary_text}."
            ),
            candidates=candidates,
        )

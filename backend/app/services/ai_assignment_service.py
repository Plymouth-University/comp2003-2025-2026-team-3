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
                    "No active profiles currently have a stored specialism matching this ticket category."
                ),
                candidates=[],
            )

        top_candidate = candidates[0]
        return TicketAssignmentRecommendationResponse(
            autotask_ticket_id=ticket_state.autotask_ticket_id,
            category=ticket_state.category,
            category_label=category_label,
            recommended_profile_id=top_candidate.profile_id,
            recommended_display_name=top_candidate.display_name,
            recommendation_summary=(
                f"Recommended {top_candidate.display_name} because their stored specialisms match "
                f"the '{category_label}' category."
            ),
            candidates=candidates,
        )

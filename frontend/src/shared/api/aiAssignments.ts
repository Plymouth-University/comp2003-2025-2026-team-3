import { API_BASE_URL } from "../auth.js";

export type AssignmentRecommendationCandidate = {
  profile_id: string;
  display_name: string;
  matched_specialism_keys: string[];
  score: number;
  reasons: string[];
  is_current_primary: boolean;
  is_current_secondary: boolean;
  open_primary_ticket_count: number;
  open_secondary_ticket_count: number;
  high_priority_ticket_count: number;
  weighted_open_load: number;
};

export type TicketAssignmentRecommendation = {
  autotask_ticket_id: number;
  category: string;
  category_label: string;
  recommended_profile_id: string | null;
  recommended_display_name: string | null;
  effective_profile_id: string | null;
  effective_display_name: string | null;
  has_manual_override: boolean;
  manual_override_profile_id: string | null;
  manual_override_display_name: string | null;
  manual_override_reason: string | null;
  manual_override_set_at: string | null;
  recommendation_summary: string;
  candidates: AssignmentRecommendationCandidate[];
};

export async function fetchAssignmentRecommendation(
  autotaskTicketId: number,
): Promise<TicketAssignmentRecommendation> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/ai/ticket-states/${autotaskTicketId}/assignment-recommendation`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new Error(`Failed to load assignment recommendation (${response.status})`);
  }

  return (await response.json()) as TicketAssignmentRecommendation;
}

export async function setAssignmentOverride(
  autotaskTicketId: number,
  profileId: string,
  reason: string | null,
): Promise<TicketAssignmentRecommendation> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/ai/ticket-states/${autotaskTicketId}/assignment-override`,
    {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile_id: profileId, reason }),
    },
  );
  if (!response.ok) {
    throw new Error(`Failed to save assignment override (${response.status})`);
  }

  return (await response.json()) as TicketAssignmentRecommendation;
}

export async function clearAssignmentOverride(
  autotaskTicketId: number,
): Promise<TicketAssignmentRecommendation> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/ai/ticket-states/${autotaskTicketId}/assignment-override`,
    {
      method: "DELETE",
      credentials: "include",
    },
  );
  if (!response.ok) {
    throw new Error(`Failed to clear assignment override (${response.status})`);
  }

  return (await response.json()) as TicketAssignmentRecommendation;
}

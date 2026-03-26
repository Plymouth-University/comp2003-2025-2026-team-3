import { API_BASE_URL } from "../auth.js";

export type AssignmentRecommendationCandidate = {
  profile_id: string;
  display_name: string;
  matched_specialism_keys: string[];
  score: number;
  reasons: string[];
  is_current_primary: boolean;
  is_current_secondary: boolean;
};

export type TicketAssignmentRecommendation = {
  autotask_ticket_id: number;
  category: string;
  category_label: string;
  recommended_profile_id: string | null;
  recommended_display_name: string | null;
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

import { API_BASE_URL } from "../auth.js";
import type { BackendTicket } from "../types.js";

type TicketAIState = {
  autotask_ticket_id: number;
  ticket_number: string;
  status: string;
  created: string;
  company: string;
  contact: string;
  title: string;
  description: string;
  issue_type: string;
  sub_issue_type: string;
  queue: string;
  source: string;
  due_date: string;
  primary_resource: string | null;
  secondary_resource: string | null;
  manual_override_display_name: string | null;
  effective_assignee_display_name: string | null;
  manual_override_reason: string | null;
  manual_override_set_at: string | null;
  category: string;
  confidence: number;
  priority_label: string;
  priority_score: number;
  classification_method: string;
};

export type TicketViewKey = "my-assigned" | "my-primary" | "my-secondary" | "team";

const VIEW_ENDPOINTS: Record<TicketViewKey, string> = {
  "my-assigned": "/api/v1/ai/ticket-states/my-assigned",
  "my-primary": "/api/v1/ai/ticket-states/my-primary",
  "my-secondary": "/api/v1/ai/ticket-states/my-secondary",
  team: "/api/v1/ai/ticket-states/team",
};

function toBackendTicket(ticket: TicketAIState): BackendTicket {
  return {
    autotask_ticket_id: ticket.autotask_ticket_id,
    ticket_number: ticket.ticket_number,
    company: ticket.company,
    contact: ticket.contact,
    status: ticket.status,
    priority: ticket.priority_label,
    created: ticket.created,
    title: ticket.title,
    description: ticket.description,
    strike_level: "",
    due_date: ticket.due_date,
    source: ticket.source,
    issue_type: ticket.issue_type,
    sub_issue_type: ticket.sub_issue_type,
    location: "",
    additional_contacts: [],
    work_type: "",
    primary_resource: ticket.primary_resource ?? "",
    secondary_resource: ticket.secondary_resource ?? "",
    effective_assignee_display_name: ticket.effective_assignee_display_name ?? ticket.primary_resource ?? ticket.secondary_resource ?? "",
    manual_override_display_name: ticket.manual_override_display_name,
    manual_override_reason: ticket.manual_override_reason,
    manual_override_set_at: ticket.manual_override_set_at,
    queue: ticket.queue,
    ai: {
      category: ticket.category,
      confidence: ticket.confidence,
      priority: ticket.priority_label,
      priority_score: ticket.priority_score,
      method: ticket.classification_method,
    },
  };
}

export async function fetchAITickets(view: TicketViewKey): Promise<BackendTicket[]> {
  const endpoint = VIEW_ENDPOINTS[view];
  const response = await fetch(`${API_BASE_URL}${endpoint}`, { credentials: "include" });
  if (!response.ok) {
    throw new Error(`Failed to load AI tickets from ${endpoint} (${response.status})`);
  }

  const payload = (await response.json()) as TicketAIState[];
  return payload.map(toBackendTicket);
}

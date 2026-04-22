import { API_BASE_URL } from "../auth.js";
import type { BackendTicket } from "../types.js";

export type TicketAIState = {
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
  is_closed: boolean;
  reason_closed: string | null;
};

export type TicketAIStateUpdate = Partial<{
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
  category: string;
  confidence: number;
  priority_label: string;
  priority_score: number;
  classification_method: string;
}>;

export type TicketViewKey = "my-assigned" | "my-primary" | "my-secondary" | "team";
export type ClosedTicketViewKey = "my-primary" | "my-secondary";

const VIEW_ENDPOINTS: Record<TicketViewKey, string> = {
  "my-assigned": "/api/v1/ai/ticket-states/my-assigned",
  "my-primary": "/api/v1/ai/ticket-states/my-primary",
  "my-secondary": "/api/v1/ai/ticket-states/my-secondary",
  team: "/api/v1/ai/ticket-states/team",
};

const CLOSED_VIEW_ENDPOINTS: Record<ClosedTicketViewKey, string> = {
  "my-primary": "/api/v1/ai/ticket-states/my-primary/closed",
  "my-secondary": "/api/v1/ai/ticket-states/my-secondary/closed",
};

export class TicketApiError extends Error {
  status: number;
  statusText: string;
  detail: string;

  constructor(status: number, statusText: string, detail: string) {
    super(`${status} ${statusText}: ${friendlyStatusMessage(status)}`);
    this.name = "TicketApiError";
    this.status = status;
    this.statusText = statusText;
    this.detail = detail;
  }
}

function friendlyStatusMessage(status: number): string {
  if (status === 400) return "The server rejected the change because the request was invalid.";
  if (status === 401) return "Your session has expired. Please sign in again.";
  if (status === 403) return "You do not have permission to save this ticket.";
  if (status === 404) return "The ticket could not be found.";
  if (status === 405) return "This server does not support that save action yet.";
  if (status === 422) return "One or more fields are not in the expected format.";
  if (status >= 500) return "The server hit an internal error while saving.";
  return "The ticket could not be saved.";
}

async function readErrorDetail(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";

  try {
    if (contentType.includes("application/json")) {
      const payload = await response.json();
      if (typeof payload?.detail === "string") {
        return payload.detail;
      }
      if (Array.isArray(payload?.detail)) {
        return payload.detail
          .map((item: { loc?: unknown; msg?: string }) => {
            const location = Array.isArray(item.loc) ? item.loc.join(".") : "";
            return `${location ? `${location}: ` : ""}${item.msg ?? JSON.stringify(item)}`;
          })
          .join("; ");
      }
      return JSON.stringify(payload);
    }

    const text = await response.text();
    return text || response.statusText;
  } catch {
    return response.statusText;
  }
}

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
    is_closed: ticket.is_closed,
    reason_closed: ticket.reason_closed,
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
  return payload.filter((ticket) => !ticket.is_closed).map(toBackendTicket);
}

async function fetchClosedTicketStates(view: ClosedTicketViewKey): Promise<TicketAIState[]> {
  const endpoint = CLOSED_VIEW_ENDPOINTS[view];
  const response = await fetch(`${API_BASE_URL}${endpoint}`, { credentials: "include" });
  if (!response.ok) {
    throw new Error(`Failed to load closed AI tickets from ${endpoint} (${response.status})`);
  }

  return (await response.json()) as TicketAIState[];
}

export async function fetchClosedAITickets(view: ClosedTicketViewKey): Promise<BackendTicket[]> {
  const payload = await fetchClosedTicketStates(view);
  return payload.filter((ticket) => ticket.is_closed).map(toBackendTicket);
}

export async function updateAITicketState(
  autotaskTicketId: number,
  changes: TicketAIStateUpdate,
): Promise<BackendTicket> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai/ticket-states/${autotaskTicketId}`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(changes),
  });
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new TicketApiError(response.status, response.statusText, detail);
  }

  return toBackendTicket((await response.json()) as TicketAIState);
}

export async function closeAITicketState(
  autotaskTicketId: number,
  reasonClosed: string,
): Promise<BackendTicket> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai/ticket-states/${autotaskTicketId}/close`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason_closed: reasonClosed }),
  });
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new TicketApiError(response.status, response.statusText, detail);
  }

  return toBackendTicket((await response.json()) as TicketAIState);
}

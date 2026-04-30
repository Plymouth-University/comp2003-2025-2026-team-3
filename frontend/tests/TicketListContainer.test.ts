// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TicketListContainer } from "../src/components/TicketListContainer.js";
import type { BackendTicket } from "../src/shared/types.js";

const mocks = vi.hoisted(() => ({
  fetchAITicketsMock: vi.fn(),
  openTicketEditModalMock: vi.fn(),
}));

vi.mock("../src/shared/api/aiTickets.js", async () => {
  const actual = await vi.importActual<typeof import("../src/shared/api/aiTickets.js")>(
    "../src/shared/api/aiTickets.js",
  );

  return {
    ...actual,
    fetchAITickets: mocks.fetchAITicketsMock,
  };
});

vi.mock("../src/components/TicketEditModal.js", () => ({
  openTicketEditModal: mocks.openTicketEditModalMock,
}));

vi.mock("../src/components/TicketCategoryReassignModal.js", () => ({
  openTicketCategoryReassignModal: vi.fn(),
}));

vi.mock("../src/components/TicketCloseModal.js", () => ({
  openTicketCloseModal: vi.fn(),
}));

vi.mock("../src/components/EllipsisMenu.js", () => ({
  EllipsisMenu: (): HTMLElement => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Edit ticket";
    button.setAttribute("data-testid", "edit-ticket");
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      button.dispatchEvent(new CustomEvent("edit", { bubbles: true }));
    });
    return button;
  },
}));

function buildTicket(overrides: Partial<BackendTicket> = {}): BackendTicket {
  return {
    autotask_ticket_id: 1001,
    ticket_number: "T-1001",
    company: "Acme Corp",
    contact: "Alex Doe",
    status: "Open",
    priority: "High",
    created: "2026-04-27T09:00:00Z",
    title: "Original printer outage",
    description: "Printer is offline in the main office.",
    strike_level: "",
    due_date: "2026-04-28",
    source: "Portal",
    issue_type: "Hardware",
    sub_issue_type: "Printer",
    location: "London",
    additional_contacts: [],
    work_type: "Support",
    primary_resource: "Jamie Smith",
    secondary_resource: "",
    effective_assignee_display_name: "Jamie Smith",
    manual_override_display_name: null,
    manual_override_reason: null,
    manual_override_set_at: null,
    category_override_reason: null,
    category_override_set_at: null,
    is_closed: false,
    reason_closed: null,
    queue: "Service Desk",
    ai: {
      category: "hardware",
      confidence: 88,
      priority: "High",
      priority_score: 90,
      method: "model",
    },
    ...overrides,
  };
}

describe("TicketListContainer", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    mocks.fetchAITicketsMock.mockReset();
    mocks.openTicketEditModalMock.mockReset();
    vi.spyOn(console, "log").mockImplementation(() => {});
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  it("updates the rendered ticket after an edit is saved", async () => {
    const originalTicket = buildTicket();
    const updatedTicket = buildTicket({
      title: "Updated printer outage",
      effective_assignee_display_name: "Morgan Lee",
      manual_override_display_name: "Morgan Lee",
    });

    mocks.fetchAITicketsMock.mockResolvedValue([originalTicket]);
    mocks.openTicketEditModalMock.mockImplementation(
      (_ticket: BackendTicket, onSaved: (updatedTicket: BackendTicket) => void) => {
        onSaved(updatedTicket);
      },
    );

    const onOpenTicket = vi.fn();
    const container = TicketListContainer(onOpenTicket);
    document.body.append(container);

    await vi.waitFor(() => {
      expect(mocks.fetchAITicketsMock).toHaveBeenCalledWith("my-assigned");
      expect(container.textContent).toContain("Original printer outage");
    });

    const editButton = container.querySelector('[data-testid="edit-ticket"]');
    expect(editButton).not.toBeNull();

    (editButton as HTMLButtonElement).click();

    await vi.waitFor(() => {
      expect(mocks.openTicketEditModalMock).toHaveBeenCalledWith(
        originalTicket,
        expect.any(Function),
      );
      expect(container.textContent).toContain("Updated printer outage");
      expect(container.textContent).toContain("Manual Override: Morgan Lee");
    });

    expect(container.textContent).not.toContain("Original printer outage");
    expect(onOpenTicket).not.toHaveBeenCalled();
  });
});

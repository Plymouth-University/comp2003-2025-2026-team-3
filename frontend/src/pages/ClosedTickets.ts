import { fetchClosedAITickets, type ClosedTicketViewKey } from "../shared/api/aiTickets.js";
import { el } from "../shared/lib/dom.js";
import type { BackendTicket } from "../shared/types.js";

type ClosedTicketsOptions = {
  initialView?: ClosedTicketViewKey;
  onViewChange?: (view: ClosedTicketViewKey) => void;
};

const VIEW_LABELS: Record<ClosedTicketViewKey, string> = {
  "my-primary": "My Primary",
  "my-secondary": "My Secondary",
};

type AssignmentStateFilter = "all" | "recommended" | "override";
type AssignmentSortMode = "default" | "override_first" | "recommended_first";

export function ClosedTicketsPage(
  onOpenTicket: (ticket: BackendTicket) => void,
  options?: ClosedTicketsOptions,
): HTMLElement {
  let ticketsState: BackendTicket[] = [];
  let activeView: ClosedTicketViewKey = options?.initialView ?? "my-primary";
  let searchQuery = "";
  let selectedCompany = "";
  let selectedQueue = "";
  let selectedEffectiveAssignee = "";
  let selectedAssignmentState: AssignmentStateFilter = "all";
  let assignmentStateSortMode: AssignmentSortMode = "default";

  const mainContainer = el("div", { className: "w-full" });
  const viewSwitcher = el("div", { className: "mb-4 flex flex-wrap gap-2" });

  const searchBar = el("input", {
    className:
      "w-full mb-6 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
    attrs: {
      type: "text",
      placeholder: "Search closed tickets by title, ID, company, or contact...",
    },
  });

  const filterContainer = el("div", { className: "mb-6 flex flex-wrap gap-4" });
  const companySelect = el("select", {
    className:
      "px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
  }) as HTMLSelectElement;
  companySelect.append(el("option", { attrs: { value: "" }, text: "Company Name" }));

  const queueSelect = el("select", {
    className:
      "px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
  }) as HTMLSelectElement;
  queueSelect.append(el("option", { attrs: { value: "" }, text: "Queue" }));

  const effectiveAssigneeSelect = el("select", {
    className:
      "px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
  }) as HTMLSelectElement;
  effectiveAssigneeSelect.append(
    el("option", { attrs: { value: "" }, text: "Effective Assignee" }),
  );

  const assignmentStateSelect = el("select", {
    className:
      "px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
  }) as HTMLSelectElement;
  assignmentStateSelect.append(
    el("option", { attrs: { value: "all" }, text: "All Tickets" }),
    el("option", { attrs: { value: "recommended" }, text: "Recommended Only" }),
    el("option", { attrs: { value: "override" }, text: "Manual Override Only" }),
  );

  const assignmentSortSelect = el("select", {
    className:
      "px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
  }) as HTMLSelectElement;
  assignmentSortSelect.append(
    el("option", { attrs: { value: "default" }, text: "Sort: Default" }),
    el("option", { attrs: { value: "override_first" }, text: "Sort: Override First" }),
    el("option", { attrs: { value: "recommended_first" }, text: "Sort: Recommended First" }),
  );

  const listSection = el("div", {
    className: "bg-white rounded-lg shadow border border-slate-200 p-6 mt-6",
  });
  const listHeader = el("div", { className: "flex items-center justify-between mb-4" }, [
    el("h1", { className: "text-xl font-bold text-slate-900", text: "Closed Tickets" }),
  ]);
  const ticketsWrap = el("div", { className: "divide-y divide-slate-100" });

  filterContainer.append(
    companySelect,
    queueSelect,
    effectiveAssigneeSelect,
    assignmentStateSelect,
    assignmentSortSelect,
  );
  listSection.append(listHeader, ticketsWrap);
  mainContainer.append(viewSwitcher, searchBar, filterContainer, listSection);

  const assignmentStateOf = (ticket: BackendTicket): "recommended" | "override" =>
    ticket.manual_override_display_name ? "override" : "recommended";

  const normalizeAssignee = (displayName: string | null | undefined): string =>
    displayName && displayName.trim().length > 0 ? displayName : "Unassigned";

  const populateSelectFromValues = (
    select: HTMLSelectElement,
    placeholder: string,
    values: string[],
    selectedValue: string,
  ): void => {
    select.innerHTML = "";
    select.append(el("option", { attrs: { value: "" }, text: placeholder }));
    values.forEach((value) => {
      select.append(el("option", { attrs: { value }, text: value }));
    });
    select.value = selectedValue;
    if (select.value !== selectedValue) {
      select.value = "";
    }
  };

  const populateFilterOptions = (): void => {
    const companyValues = Array.from(
      new Set(ticketsState.map((ticket) => ticket.company).filter(Boolean)),
    ).sort((a, b) => a.localeCompare(b));
    populateSelectFromValues(companySelect, "Company Name", companyValues, selectedCompany);
    selectedCompany = companySelect.value;

    const queueValues = Array.from(
      new Set(ticketsState.map((ticket) => ticket.queue).filter(Boolean)),
    ).sort((a, b) => a.localeCompare(b));
    populateSelectFromValues(queueSelect, "Queue", queueValues, selectedQueue);
    selectedQueue = queueSelect.value;

    const assigneeValues = Array.from(
      new Set(ticketsState.map((ticket) => normalizeAssignee(ticket.effective_assignee_display_name))),
    ).sort((a, b) => a.localeCompare(b));
    populateSelectFromValues(
      effectiveAssigneeSelect,
      "Effective Assignee",
      assigneeValues,
      selectedEffectiveAssignee,
    );
    selectedEffectiveAssignee = effectiveAssigneeSelect.value;
  };

  const updateViewButtons = (): void => {
    viewSwitcher.innerHTML = "";
    (Object.keys(VIEW_LABELS) as ClosedTicketViewKey[]).forEach((viewKey) => {
      const isActive = activeView === viewKey;
      const button = el("button", {
        className: isActive
          ? "rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          : "rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50",
        attrs: { type: "button" },
        text: VIEW_LABELS[viewKey],
      });
      button.addEventListener("click", () => {
        if (activeView === viewKey) return;
        activeView = viewKey;
        options?.onViewChange?.(viewKey);
        void loadTickets();
      });
      viewSwitcher.append(button);
    });
  };

  const renderTicketCard = (ticket: BackendTicket): HTMLElement => {
    const ticketCard = el("div", {
      className: "p-4 hover:bg-slate-50 cursor-pointer transition relative",
      attrs: { role: "button" },
    });

    const viewButton = el("button", {
      className:
        "rounded-lg border border-slate-300 px-3 py-1 text-sm font-semibold text-slate-700 hover:bg-slate-100",
      attrs: { type: "button" },
      text: "View",
    });
    viewButton.addEventListener("click", (event) => {
      event.stopPropagation();
      onOpenTicket(ticket);
    });

    const topRow = el("div", { className: "flex justify-between items-start gap-3 mb-3" }, [
      el("div", {
        className: "font-semibold text-slate-900 truncate flex-1",
        text: ticket.title,
      }),
      viewButton,
    ]);

    const reasonClosed = ticket.reason_closed?.trim();
    const displayStatus = ticket.is_closed ? "Closed" : ticket.status;
    const infoItems = [
      el("div", {
        className: "text-xs text-slate-500",
        text: `ID: ${ticket.autotask_ticket_id}`,
      }),
      el("div", { className: "text-xs text-slate-500 mt-2 flex flex-wrap gap-2" }, [
        el("span", { text: `Priority: ${ticket.priority}` }),
        el("span", { text: `Confidence: ${ticket.ai.confidence.toFixed(0)}%` }),
        el("span", { text: `Status: ${displayStatus}` }),
      ]),
      el("div", {
        className: "text-xs text-slate-500 mt-2",
        text: `Effective Assignee: ${ticket.effective_assignee_display_name || "Unassigned"}`,
      }),
      ...(ticket.manual_override_display_name
        ? [
            el("div", {
              className:
                "mt-2 inline-flex rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-900",
              text: `Manual Override: ${ticket.manual_override_display_name}`,
            }),
          ]
        : []),
      ...(reasonClosed
        ? [
            el("div", {
              className: "text-xs text-slate-500 mt-2",
              text: `Closure Reason: ${reasonClosed}`,
            }),
          ]
        : []),
      el("div", { className: "text-xs text-slate-500 mt-2", text: `Due: ${ticket.due_date}` }),
    ];

    const infoRow = el("div", { className: "flex justify-between items-start gap-3" }, [
      el("div", { className: "min-w-0 flex-1" }, infoItems),
    ]);

    ticketCard.append(topRow, infoRow);
    ticketCard.addEventListener("click", () => onOpenTicket(ticket));
    return ticketCard;
  };

  const render = (): void => {
    ticketsWrap.innerHTML = "";
    let filteredTickets = ticketsState;

    if (searchQuery) {
      filteredTickets = filteredTickets.filter((ticket) => {
        const searchableText =
          `${ticket.title} ${ticket.autotask_ticket_id} ${ticket.company} ${ticket.contact}`.toLowerCase();
        return searchableText.includes(searchQuery);
      });
    }
    if (selectedCompany) {
      filteredTickets = filteredTickets.filter((ticket) => ticket.company === selectedCompany);
    }
    if (selectedQueue) {
      filteredTickets = filteredTickets.filter((ticket) => ticket.queue === selectedQueue);
    }
    if (selectedEffectiveAssignee) {
      filteredTickets = filteredTickets.filter(
        (ticket) =>
          normalizeAssignee(ticket.effective_assignee_display_name) === selectedEffectiveAssignee,
      );
    }
    if (selectedAssignmentState !== "all") {
      filteredTickets = filteredTickets.filter(
        (ticket) => assignmentStateOf(ticket) === selectedAssignmentState,
      );
    }

    if (assignmentStateSortMode !== "default") {
      const prioritizedState = assignmentStateSortMode === "override_first" ? "override" : "recommended";
      filteredTickets = [...filteredTickets].sort((a, b) => {
        const aScore = assignmentStateOf(a) === prioritizedState ? 0 : 1;
        const bScore = assignmentStateOf(b) === prioritizedState ? 0 : 1;
        if (aScore !== bScore) return aScore - bScore;
        return a.autotask_ticket_id - b.autotask_ticket_id;
      });
    }

    if (filteredTickets.length === 0) {
      ticketsWrap.append(
        el("div", {
          className: "text-center py-8 text-slate-500",
          text:
            searchQuery ||
            selectedCompany ||
            selectedQueue ||
            selectedEffectiveAssignee ||
            selectedAssignmentState !== "all"
              ? "No closed tickets found matching your filters"
              : `No closed tickets found for ${VIEW_LABELS[activeView]}`,
        }),
      );
      return;
    }

    filteredTickets.forEach((ticket) => {
      ticketsWrap.append(renderTicketCard(ticket));
    });
  };

  async function loadTickets(): Promise<void> {
    updateViewButtons();
    ticketsWrap.innerHTML = "";
    ticketsWrap.append(
      el("div", {
        className: "text-center py-8 text-slate-500",
        text: `Loading ${VIEW_LABELS[activeView]} closed tickets...`,
      }),
    );

    try {
      ticketsState = await fetchClosedAITickets(activeView);
      populateFilterOptions();
      render();
    } catch (error) {
      console.error("Closed ticket fetch failed", error);
      ticketsWrap.innerHTML = "";
      ticketsWrap.append(
        el("div", {
          className: "text-center py-8 text-red-600",
          text: "Failed to load closed tickets for this view.",
        }),
      );
    }
  }

  searchBar.addEventListener("input", (event) => {
    searchQuery = (event.target as HTMLInputElement).value.toLowerCase();
    render();
  });

  companySelect.addEventListener("change", (event) => {
    selectedCompany = (event.target as HTMLSelectElement).value;
    render();
  });

  queueSelect.addEventListener("change", (event) => {
    selectedQueue = (event.target as HTMLSelectElement).value;
    render();
  });

  effectiveAssigneeSelect.addEventListener("change", (event) => {
    selectedEffectiveAssignee = (event.target as HTMLSelectElement).value;
    render();
  });

  assignmentStateSelect.addEventListener("change", (event) => {
    selectedAssignmentState = (event.target as HTMLSelectElement).value as AssignmentStateFilter;
    render();
  });

  assignmentSortSelect.addEventListener("change", (event) => {
    assignmentStateSortMode = (event.target as HTMLSelectElement).value as AssignmentSortMode;
    render();
  });

  updateViewButtons();
  void loadTickets();

  return mainContainer;
}

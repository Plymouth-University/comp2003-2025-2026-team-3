import { el } from "../shared/lib/dom.js";
import { API_BASE_URL } from "../shared/auth.js";
import { fetchAITickets, type TicketViewKey } from "../shared/api/aiTickets.js";
import type { BackendTicket } from "../shared/types.js";
import { EllipsisMenu } from "./EllipsisMenu.js";

function getTimeStamp(): string {
  const now = new Date();
  return now.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    fractionalSecondDigits: 3,
  });
}

type TicketListContainerOptions = {
  initialView?: TicketViewKey;
  onViewChange?: (view: TicketViewKey) => void;
};

const VIEW_LABELS: Record<TicketViewKey, string> = {
  "my-assigned": "My Assigned",
  "my-primary": "My Primary",
  "my-secondary": "My Secondary",
  team: "Team Queue",
};

export function TicketListContainer(
  onOpenTicket: (ticket: BackendTicket) => void,
  options?: TicketListContainerOptions,
): HTMLElement {
  let ticketsState: BackendTicket[] = [];
  let searchQuery = "";
  let selectedCompany = "";
  let selectedQueue = "";
  let collapsedCategories: Set<string> = new Set();
  let activeView: TicketViewKey = options?.initialView ?? "my-assigned";

  const categorySortState = new Map<
    string,
    {
      sortMode: "priority" | "due_date";
      sortByPriority: "asc" | "desc";
      sortByDate: "asc" | "desc";
    }
  >();

  const mainContainer = el("div", { className: "w-full" });
  const viewSwitcher = el("div", { className: "mb-4 flex flex-wrap gap-2" });

  const searchBar = el("input", {
    className:
      "w-full mb-6 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
    attrs: {
      type: "text",
      placeholder: "Search tickets by title, ID, or contact...",
    },
  });

  const filterContainer = el("div", { className: "mb-6 flex gap-4" });
  const companySelect = el("select", {
    className:
      "px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
  }) as HTMLSelectElement;
  companySelect.append(el("option", { attrs: { value: "" }, text: "Company Name" }));
  for (let i = 1; i <= 20; i += 1) {
    companySelect.append(el("option", { attrs: { value: `Company ${i}` }, text: `Company ${i}` }));
  }

  const queueSelect = el("select", {
    className:
      "px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
  }) as HTMLSelectElement;
  queueSelect.append(el("option", { attrs: { value: "" }, text: "Queue" }));
  queueSelect.append(el("option", { attrs: { value: "MS - SecOps" }, text: "MS - SecOps" }));

  const ticketsContainer = el("div", {
    className: "w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-start",
  });

  const loadingMsg = el("div", {
    className: "text-center py-8 text-slate-500 col-span-full",
    text: "Loading tickets...",
  });
  ticketsContainer.append(loadingMsg);

  function updateViewButtons(): void {
    viewSwitcher.innerHTML = "";
    (Object.keys(VIEW_LABELS) as TicketViewKey[]).forEach((viewKey) => {
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
        updateViewButtons();
        options?.onViewChange?.(viewKey);
        void loadTickets();
      });
      viewSwitcher.append(button);
    });
  }

  async function loadTickets(): Promise<void> {
    updateViewButtons();
    const startTime = getTimeStamp();
    console.log(`[${startTime}] Loading AI tickets for view ${activeView}...`);
    ticketsContainer.innerHTML = "";
    ticketsContainer.append(
      el("div", {
        className: "text-center py-8 text-slate-500 col-span-full",
        text: `Loading ${VIEW_LABELS[activeView]} tickets...`,
      }),
    );

    try {
      ticketsState = await fetchAITickets(activeView);
      console.log(
        `[${getTimeStamp()}] Loaded ${ticketsState.length} AI tickets from ${API_BASE_URL} for ${activeView}`,
      );
      render();
    } catch (error) {
      console.error(`[${getTimeStamp()}] AI ticket fetch failed`, error);
      ticketsContainer.innerHTML = "";
      ticketsContainer.append(
        el("div", {
          className: "text-center py-8 text-red-600 col-span-full",
          text: "Failed to load tickets for this view.",
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

  filterContainer.append(companySelect, queueSelect);
  mainContainer.append(viewSwitcher, searchBar, filterContainer, ticketsContainer);

  const sortTickets = (tickets: BackendTicket[], category: string): BackendTicket[] => {
    if (!categorySortState.has(category)) {
      categorySortState.set(category, {
        sortMode: "due_date",
        sortByPriority: "desc",
        sortByDate: "asc",
      });
    }

    const state = categorySortState.get(category)!;
    const priorityOrder = { Critical: 4, High: 3, Medium: 2, Low: 1 } as const;

    const priorityCmp = (a: BackendTicket, b: BackendTicket) =>
      (state.sortByPriority === "asc" ? 1 : -1) *
      ((priorityOrder[a.priority as keyof typeof priorityOrder] || 0) -
        (priorityOrder[b.priority as keyof typeof priorityOrder] || 0));

    const dateCmp = (a: BackendTicket, b: BackendTicket) =>
      (state.sortByDate === "asc" ? 1 : -1) *
      (new Date(a.due_date).getTime() - new Date(b.due_date).getTime());

    return [...tickets].sort((a, b) => {
      const primary = state.sortMode === "priority" ? priorityCmp(a, b) : dateCmp(a, b);
      if (primary !== 0) return primary;
      return state.sortMode === "priority" ? dateCmp(a, b) : priorityCmp(a, b);
    });
  };

  const renderCategorySection = (category: string, tickets: BackendTicket[]) => {
    const isCollapsed = collapsedCategories.has(category);
    if (!categorySortState.has(category)) {
      categorySortState.set(category, {
        sortMode: "due_date",
        sortByPriority: "desc",
        sortByDate: "asc",
      });
    }

    const section = el("div", {
      className: "bg-white rounded-lg shadow border border-blue-100 max-h-96 overflow-y-auto",
    });
    const header = el("div", {
      className: "flex items-center justify-between p-4 border-b border-slate-100 hover:bg-blue-50",
    });
    const titleWrap = el("div", { className: "flex items-center gap-2 flex-1" });
    titleWrap.append(
      el("span", { className: "font-bold text-lg capitalize text-slate-900", text: category }),
      el("span", { className: "text-sm text-slate-500", text: `(${tickets.length})` }),
    );

    const btnRow = el("div", { className: "flex gap-2" });
    const dateBtn = el("button", {
      className: "p-1 hover:bg-slate-200 rounded transition",
      attrs: { type: "button" },
    });
    dateBtn.append(
      el("img", {
        className: "w-5 h-5",
        attrs: { src: "./public/sort-by-icon/sortIcon.png", alt: "Sort by Date" },
      }),
    );

    const priorityBtn = el("button", {
      className: "p-1 hover:bg-slate-200 rounded transition",
      attrs: { type: "button" },
    });
    priorityBtn.append(
      el("img", {
        className: "w-5 h-5",
        attrs: { src: "./public/priority-icon/danger.png", alt: "Sort by Priority" },
      }),
    );
    btnRow.append(dateBtn, priorityBtn);

    const icon = el("span", {
      className: `text-slate-400 text-lg transition-transform ${isCollapsed ? "" : "rotate-180"}`,
      text: "▼",
    });
    header.append(titleWrap, btnRow, icon);

    const ticketsWrap = el("div", { className: "divide-y divide-slate-100" });
    if (!isCollapsed) {
      for (const ticket of sortTickets(tickets, category)) {
        const ticketCard = el("div", {
          className: "p-4 hover:bg-emerald-200 cursor-pointer transition relative",
          attrs: { role: "button" },
        });
        const menu = EllipsisMenu();
        menu.addEventListener("view", () => onOpenTicket(ticket));

        const topRow = el("div", { className: "flex justify-between items-start gap-3 mb-3" }, [
          el("div", {
            className: "font-semibold text-slate-900 truncate flex-1",
            text: ticket.title,
          }),
          menu,
        ]);

        const infoRow = el("div", { className: "flex justify-between items-start gap-3" }, [
          el("div", { className: "min-w-0 flex-1" }, [
            el("div", {
              className: "text-xs text-slate-500",
              text: `ID: ${ticket.autotask_ticket_id}`,
            }),
            el("div", { className: "text-xs text-slate-500 mt-2 flex gap-2" }, [
              el("span", { text: `Priority: ${ticket.priority}` }),
              el("span", { text: `Confidence: ${ticket.ai.confidence.toFixed(0)}%` }),
            ]),
            el("div", {
              className: "text-xs text-slate-500 mt-2",
              text: `Effective Assignee: ${ticket.effective_assignee_display_name || "Unassigned"}`,
            }),
            ...(ticket.manual_override_display_name ? [
              el("div", {
                className: "mt-2 inline-flex rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-900",
                text: `Manual Override: ${ticket.manual_override_display_name}`,
              }),
            ] : []),
            el("div", { className: "text-xs text-slate-500 mt-2", text: `Due: ${ticket.due_date}` }),
          ]),
        ]);

        ticketCard.append(topRow, infoRow);
        ticketCard.addEventListener("click", (event) => {
          if ((event.target as HTMLElement).closest(".relative")) return;
          onOpenTicket(ticket);
        });
        ticketsWrap.append(ticketCard);
      }
    }

    const sortCategory = category;
    dateBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      const state = categorySortState.get(sortCategory)!;
      state.sortMode = "due_date";
      state.sortByDate = state.sortByDate === "asc" ? "desc" : "asc";
      render();
    });

    priorityBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      const state = categorySortState.get(sortCategory)!;
      state.sortMode = "priority";
      state.sortByPriority = state.sortByPriority === "asc" ? "desc" : "asc";
      render();
    });

    header.addEventListener("click", (event) => {
      if ((event.target as HTMLElement).closest("button")) {
        event.stopPropagation();
        return;
      }
      if (collapsedCategories.has(sortCategory)) {
        collapsedCategories.delete(sortCategory);
      } else {
        collapsedCategories.add(sortCategory);
      }
      render();
    });

    section.append(header, ticketsWrap);
    return section;
  };

  const render = (): void => {
    ticketsContainer.innerHTML = "";
    let filteredTickets = ticketsState;

    if (searchQuery) {
      filteredTickets = filteredTickets.filter((ticket) => {
        const searchableText = `${ticket.title} ${ticket.autotask_ticket_id} ${ticket.company} ${ticket.contact}`.toLowerCase();
        return searchableText.includes(searchQuery);
      });
    }
    if (selectedCompany) {
      filteredTickets = filteredTickets.filter((ticket) => ticket.company === selectedCompany);
    }
    if (selectedQueue) {
      filteredTickets = filteredTickets.filter((ticket) => ticket.queue === selectedQueue);
    }

    if (filteredTickets.length === 0) {
      ticketsContainer.append(
        el("div", {
          className: "text-center py-8 text-slate-500 col-span-full",
          text:
            searchQuery || selectedCompany || selectedQueue
              ? "No tickets found matching your filters"
              : `No tickets found for ${VIEW_LABELS[activeView]}`,
        }),
      );
      return;
    }

    const categorized = new Map<string, BackendTicket[]>();
    for (const ticket of filteredTickets) {
      const category = ticket.ai?.category || "uncategorized";
      if (!categorized.has(category)) categorized.set(category, []);
      categorized.get(category)!.push(ticket);
    }

    for (const category of Array.from(categorized.keys()).sort()) {
      ticketsContainer.append(renderCategorySection(category, categorized.get(category) || []));
    }
  };

  updateViewButtons();
  void loadTickets();

  return mainContainer;
}

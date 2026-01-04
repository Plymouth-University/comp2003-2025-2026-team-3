type BackendTicket = {
  autotask_ticket_id: number;
  title: string;
  description: string;
  created_at: string;
  priority: number;
  ai: {
    category: string;
    confidence: number;
  };
};

async function fetchTickets(): Promise<BackendTicket[]> {
  try {
    console.log("Fetching tickets from API...");
    const res = await fetch("http://127.0.0.1:8000/api/tickets");
    console.log("Response status:", res.status);
    if (!res.ok) {
      console.error("API returned status:", res.status);
      return [];
    }
    const json = await res.json();
    console.log("Fetched tickets:", json);
    return json.items || [];
  } catch (error) {
    console.error("Failed to fetch tickets:", error);
    return [];
  }
}

import { el } from "../lib/dom.js";

export function TicketListContainer(onOpenTicket: (id: string) => void): HTMLElement {
  let ticketsState: BackendTicket[] = [];
  let collapsedCategories: Set<string> = new Set();

  const mainContainer = el("div", { className: "w-full space-y-6" });

  const loadingMsg = el("div", { 
    className: "text-center py-8 text-slate-500",
    text: "Loading tickets..." 
  });
  mainContainer.append(loadingMsg);

  const renderCategorySection = (category: string, tickets: BackendTicket[]) => {
    const isCollapsed = collapsedCategories.has(category);
    
    const section = el("div", {
      className: "bg-white rounded-lg shadow border border-slate-200",
    });

    const header = el("div", { className: "flex items-center justify-between p-4 border-b border-slate-100 cursor-pointer hover:bg-slate-50" });
    
    const titleWrap = el("div", { className: "flex items-center gap-2" });
    titleWrap.append(
      el("span", { className: "font-semibold capitalize text-slate-900", text: category }),
      el("span", { className: "text-sm text-slate-500", text: `(${tickets.length})` })
    );

    const icon = el("span", { 
      className: `text-slate-400 text-lg transition-transform ${isCollapsed ? "" : "rotate-180"}`,
      text: "▼"
    });

    header.append(titleWrap, icon);

    const ticketsWrap = el("div", { className: "divide-y divide-slate-100" });

    if (!isCollapsed) {
      for (const ticket of tickets) {
        const ticketCard = el("div", {
          className: "p-4 hover:bg-slate-50 cursor-pointer transition",
          attrs: { role: "button" }
        });

        ticketCard.append(
          el("div", { className: "flex justify-between items-start gap-3" }, [
            el("div", { className: "min-w-0 flex-1" }, [
              el("div", { className: "text-xs text-slate-500", text: `ID: ${ticket.autotask_ticket_id}` }),
              el("div", { className: "font-semibold text-slate-900 truncate", text: ticket.title }),
              el("div", { className: "text-sm text-slate-600 mt-1 line-clamp-2", text: ticket.description }),
              el("div", { className: "text-xs text-slate-500 mt-2 flex gap-2" }, [
                el("span", { text: `Priority: ${ticket.priority}` }),
                el("span", { text: `Confidence: ${(ticket.ai.confidence * 100).toFixed(0)}%` })
              ])
            ])
          ])
        );

        ticketCard.addEventListener("click", () => {
          onOpenTicket(String(ticket.autotask_ticket_id));
        });

        ticketsWrap.append(ticketCard);
      }
    }

    header.addEventListener("click", () => {
      if (collapsedCategories.has(category)) {
        collapsedCategories.delete(category);
      } else {
        collapsedCategories.add(category);
      }
      render();
    });

    section.append(header, ticketsWrap);
    return section;
  };

  const render = () => {
    mainContainer.innerHTML = "";
    
    if (ticketsState.length === 0) {
      mainContainer.append(
        el("div", { 
          className: "text-center py-8 text-slate-500",
          text: "No tickets found" 
        })
      );
      return;
    }

    // Group tickets by category
    const categorized = new Map<string, BackendTicket[]>();
    for (const ticket of ticketsState) {
      const cat = ticket.ai?.category || "uncategorized";
      if (!categorized.has(cat)) {
        categorized.set(cat, []);
      }
      categorized.get(cat)!.push(ticket);
    }

    // Sort categories and render sections
    const sortedCategories = Array.from(categorized.keys()).sort();
    for (const category of sortedCategories) {
      const tickets = categorized.get(category) || [];
      mainContainer.append(renderCategorySection(category, tickets));
    }
  };

  // Fetch tickets and render
  fetchTickets().then(t => {
    ticketsState = t;
    render();
  });

  return mainContainer;
}

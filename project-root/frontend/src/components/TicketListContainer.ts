type BackendTicket = {
  autotask_ticket_id: number;
  ticket_number: string;
  company: string;
  contact: string;
  status: string;
  priority: string;
  created: string;
  title: string;
  description: string;
  due_date: string;
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
    console.log("Response headers:", res.headers);
    
    if (!res.ok) {
      console.error("API returned status:", res.status);
      return [];
    }
    
    const text = await res.text();
    console.log("Raw response text:", text);
    
    const json = JSON.parse(text);
    console.log("Parsed JSON:", json);
    console.log("Items count:", json.items ? json.items.length : 0);
    
    if (!json.items || json.items.length === 0) {
      console.warn("No items returned from API");
      return [];
    }
    
    //log first ticket to verify structure
    if (json.items.length > 0) {
      console.log("First ticket structure:", json.items[0]);
    }
    
    return json.items || [];
  } catch (error) {
    console.error("Failed to fetch tickets:", error);
    return [];
  }
}

import { el } from "../lib/dom.js";
import { EllipsisMenu } from "./EllipsisMenu.js";

export function TicketListContainer(onOpenTicket: (ticket: BackendTicket) => void): HTMLElement {
  let ticketsState: BackendTicket[] = [];
  let collapsedCategories: Set<string> = new Set();
  
  //track sort state for each category
  const categorySortState = new Map<string, {
    sortMode: "priority" | "due_date";
    sortByPriority: "asc" | "desc";
    sortByDate: "asc" | "desc";
  }>();

  const mainContainer = el("div", { className: "w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-start" });

  const loadingMsg = el("div", { 
    className: "text-center py-8 text-slate-500 col-span-full",
    text: "Loading tickets..." 
  });
  mainContainer.append(loadingMsg);

  //sort tickets within a specific category
  const sortTickets = (tickets: BackendTicket[], category: string): BackendTicket[] => {
    
    //get or initialize sort state for this category
    if (!categorySortState.has(category)) {
      categorySortState.set(category, {
        sortMode: "due_date",
        sortByPriority: "desc",
        sortByDate: "asc"
      });
    }
    
    const state = categorySortState.get(category)!;
    const priorityOrder = { Critical: 4, High: 3, Medium: 2, Low: 1 } as const; //priority hierarchy
    
    const priorityCmp = (a: BackendTicket, b: BackendTicket) => //compare priorities
      (state.sortByPriority === "asc" ? 1 : -1) *
      ((priorityOrder[a.priority as keyof typeof priorityOrder] || 0) - (priorityOrder[b.priority as keyof typeof priorityOrder] || 0));
    
    const dateCmp = (a: BackendTicket, b: BackendTicket) => //compare due dates
      (state.sortByDate === "asc" ? 1 : -1) *
      (new Date(a.due_date).getTime() - new Date(b.due_date).getTime());

    return [...tickets].sort((a, b) => {
      const primary = state.sortMode === "priority" ? priorityCmp(a, b) : dateCmp(a, b);
      if (primary !== 0) return primary;
      return state.sortMode === "priority" ? dateCmp(a, b) : priorityCmp(a, b);
    });
  };

  //make ticket category UI section
  const renderCategorySection = (category: string, tickets: BackendTicket[]) => {
    const isCollapsed = collapsedCategories.has(category);
    
    //initialize sort state for this category if it doesn't exist
    if (!categorySortState.has(category)) {
      categorySortState.set(category, {
        sortMode: "due_date",
        sortByPriority: "desc",
        sortByDate: "asc"
      });
    }
    
    const section = el("div", {
      className: "bg-white rounded-lg shadow border border-blue-100",
    });

    const header = el("div", { className: "flex items-center justify-between p-4 border-b border-slate-100 hover:bg-blue-50" });
    
    const titleWrap = el("div", { className: "flex items-center gap-2 flex-1" });
    titleWrap.append(
      el("span", { className: "font-bold text-lg capitalize text-slate-900", text: category }),
      el("span", { className: "text-sm text-slate-500", text: `(${tickets.length})` })
    );

    //create button row for sort buttons
    const btnRow = el("div", { className: "flex gap-2" });

    //create sort by date button
    const dateBtn = el("button", { 
      className: "p-1 hover:bg-slate-200 rounded transition",
      attrs: { type: "button" } 
    });
    dateBtn.append(
      el("img", {
        className: "w-5 h-5",
        attrs: { src: "./assets/sort-by-icon/sortIcon.png", alt: "Sort by Date" },
      })
    );

    //create sort by priority button
    const priorityBtn = el("button", { 
      className: "p-1 hover:bg-slate-200 rounded transition",
      attrs: { type: "button" } 
    });
    priorityBtn.append(
      el("img", {
        className: "w-5 h-5",
        attrs: { src: "./assets/priority-icon/danger.png", alt: "Sort by Priority" },
      })
    );

    btnRow.append(dateBtn, priorityBtn);

    const icon = el("span", { 
      className: `text-slate-400 text-lg transition-transform ${isCollapsed ? "" : "rotate-180"}`,
      text: "▼"
    });

    header.append(titleWrap, btnRow, icon); //add title, icon and buttons to category container header

    //tickets container element
    const ticketsWrap = el("div", { className: "divide-y divide-slate-100" });

    if (!isCollapsed) {
      //sort tickets for this category
      const sortedTickets = sortTickets(tickets, category);
      
      for (const ticket of sortedTickets) {
        const ticketCard = el("div", {
          className: "p-4 hover:bg-blue-300 cursor-pointer transition relative",
          attrs: { role: "button" }
        });

        //create an ellipsis menu for each ticket
        const menu = EllipsisMenu();
        menu.addEventListener("view", () => onOpenTicket(ticket)); // on view, open ticket

        //ticket title row
        const topRow = el("div", { className: "flex justify-between items-start gap-3 mb-3" }, [
          el("div", { className: "font-semibold text-slate-900 truncate flex-1", text: ticket.title }), //add title
          menu
        ]);

        //ticket info row
        const infoRow = el("div", { className: "flex justify-between items-start gap-3" }, [
          el("div", { className: "min-w-0 flex-1" }, [
            el("div", { className: "text-xs text-slate-500", text: `ID: ${ticket.autotask_ticket_id}` }), //show id
            el("div", { className: "text-xs text-slate-500 mt-2 flex gap-2" }, [
              el("span", { text: `Priority: ${ticket.priority}` }), //show priority
              el("span", { text: `Confidence: ${(ticket.ai.confidence * 100).toFixed(0)}%` }) //show ai confidence
            ]),
            el("div", { className: "text-xs text-slate-500 mt-2", text: `Due: ${ticket.due_date}` }) // show the due date
          ])
        ]);

        ticketCard.append(topRow, infoRow);

        ticketCard.addEventListener("click", (e) => {
          //dont complete navigation if clicking on menu
          if ((e.target as HTMLElement).closest('.relative')) {
            return;
          }
          onOpenTicket(ticket);
        });

        ticketsWrap.append(ticketCard);
      }
    }

    //button event listeners - using stored category reference
    const sortCategory = category;
    
    dateBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const state = categorySortState.get(sortCategory)!;
      state.sortMode = "due_date";
      state.sortByDate = state.sortByDate === "asc" ? "desc" : "asc";
      render();
    });

    priorityBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const state = categorySortState.get(sortCategory)!;
      state.sortMode = "priority";
      state.sortByPriority = state.sortByPriority === "asc" ? "desc" : "asc";
      render();
    });

    //toggle collapse of category container
    header.addEventListener("click", (e) => {
      //don't collapse if clicking on buttons
      if ((e.target as HTMLElement).closest('button')) {
        e.stopPropagation();
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

  const render = () => {
    mainContainer.innerHTML = "";
    
    if (ticketsState.length === 0) { //if there are no tickets, display message
      mainContainer.append(
        el("div", { 
          className: "text-center py-8 text-slate-500 col-span-full", 
          text: "No tickets found" 
        })
      );
      return;
    }

    //group tickets by the category
    const categorized = new Map<string, BackendTicket[]>();
    for (const ticket of ticketsState) {
      const cat = ticket.ai?.category || "uncategorized";
      if (!categorized.has(cat)) {
        categorized.set(cat, []);
      }
      categorized.get(cat)!.push(ticket);
    }

    //sort the categories and render UI sections
    const sortedCategories = Array.from(categorized.keys()).sort();
    for (const category of sortedCategories) {
      const tickets = categorized.get(category) || [];
      mainContainer.append(renderCategorySection(category, tickets));
    }
  };

  //fetch tickets and render UI
  fetchTickets().then(t => {
    ticketsState = t;
    render();
  });

  return mainContainer;
}

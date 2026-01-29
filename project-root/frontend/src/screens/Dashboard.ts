import { el } from "../lib/dom.js";
import { EllipsisMenu } from "../components/EllipsisMenu.js";
import type { BackendTicket } from "../types.js";

async function fetchTickets(): Promise<BackendTicket[]> {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/tickets");
    if (!res.ok) {
      return [];
    }
    const json = await res.json();
    return json.items || [];
  } catch (error) {
    console.error("Failed to fetch tickets:", error);
    return [];
  }
}

export function Dashboard(onOpenTicket?: (ticket: BackendTicket) => void): HTMLElement {
  const container = el("div", { className: "w-full" });

  // Create stat card number elements with references for updates
  const criticalCountElem = el("div", { className: "text-3xl font-bold text-blue-900 mt-2", text: "-" });
  const newTicketsCountElem = el("div", { className: "text-3xl font-bold text-green-900 mt-2", text: "-" });
  const mostCommonCategoryElem = el("div", { className: "text-3xl font-bold text-purple-900 mt-2", text: "-" });
  const activeCountElem = el("div", { className: "text-3xl font-bold text-yellow-900 mt-2", text: "-" });

  container.append(
    //welcome header and subtitle
    el("div", { className: "bg-white rounded-lg shadow border border-slate-200 p-6 mb-6" }, [
      el("h1", { className: "text-3xl font-bold mb-2", text: "Welcome to Global 4 Ticket Interface" }),
      el("p", { className: "text-slate-600", text: "Manage and track your support tickets efficiently." })
    ]),
    
    //stat card elements below
    el("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-4" }, [ //critical priority stat card
      el("div", { className: "bg-blue-50 rounded-lg border border-blue-200 p-4" }, [
        el("div", { className: "text-blue-600 font-semibold", text: "Critical Priority" }),
        criticalCountElem,
        el("p", { className: "text-sm text-blue-700 mt-2", text: "Tickets awaiting resolution" })
      ]),

      el("div", { className: "bg-green-50 rounded-lg border border-green-200 p-4" }, [
        el("div", { className: "text-green-600 font-semibold", text: "New Tickets" }), //new tickets stat card
        newTicketsCountElem,
        el("p", { className: "text-sm text-green-700 mt-2", text: "Recent influx of tickets" })
      ]),

      el("div", { className: "bg-purple-50 rounded-lg border border-purple-200 p-4" }, [
        el("div", { className: "text-purple-600 font-semibold", text: "Today's Most Common Issue" }), //most common issue stat card
        mostCommonCategoryElem,
        el("p", { className: "text-sm text-purple-700 mt-2", text: "Category with most tickets today" })
      ]),
      el("div", { className: "bg-yellow-50 rounded-lg border border-yellow-200 p-4" }, [
        el("div", { className: "text-yellow-600 font-semibold", text: "Active Tickets" }), //active tickets stat card
        activeCountElem,
        el("p", { className: "text-sm text-yellow-700 mt-2", text: "All tickets awaiting resolution" })
      ])

    ])
  );

  //display all tickets with critical priority and close due date:
  const criticalSection = el("div", { className: "bg-white rounded-lg shadow border border-slate-200 p-6 mt-6" });
  
  const criticalHeader = el("div", { className: "flex items-center justify-between mb-4" }, [
    el("h2", { className: "text-red-600 text-xl font-bold", text: "Tickets Requiring Immediate Attention" })
  ]);
  criticalSection.append(criticalHeader);

  //add the loading message otherwise it looks as if tickets are not loading
  const loadingMsg = el("div", { 
    className: "text-center py-8 text-slate-500",
    text: "Loading tickets..." 
  });
  criticalSection.append(loadingMsg);

  const criticalTicketsWrap = el("div", { className: "divide-y divide-slate-100" });
  criticalSection.append(criticalTicketsWrap);

  //fetch the tickets then filter based on pririty being critical
  fetchTickets().then(allTickets => {
    //remove loading message once tickets are loaded
    loadingMsg.remove();
    
    //calculate number of critical priority tickets
    const criticalCount = allTickets.filter(t => t.priority === "Critical").length;
    
    //calculate new tickets (created in last 24 hours)
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const newTicketsCount = allTickets.filter(t => {
      const createdDate = new Date(t.created);
      return createdDate >= yesterday && createdDate <= now;
    }).length;
    
    //calculate most common category
    const categoryCount: { [key: string]: number } = {};
    for (const ticket of allTickets) {
      const category = ticket.ai.category;
      categoryCount[category] = (categoryCount[category] || 0) + 1;
    }
    const mostCommonCategory = Object.keys(categoryCount).length > 0
      ? Object.entries(categoryCount).reduce((a, b) => b[1] > a[1] ? b : a)[0]
      : "N/A";
    
    //active tickets count (all tickets)
    const activeCount = allTickets.length;
    
    // Update stat card elements
    criticalCountElem.textContent = criticalCount.toString();
    newTicketsCountElem.textContent = newTicketsCount.toString();
    mostCommonCategoryElem.textContent = mostCommonCategory;
    activeCountElem.textContent = activeCount.toString();
    
    const criticalTickets = allTickets.filter(t => t.priority === "Critical");
    
    if (criticalTickets.length === 0) {
      criticalTicketsWrap.innerHTML = '<div class="text-center py-8 text-slate-500">No critical priority tickets</div>';
      return;
    }
    
    //populate the section with the filtered tickets
    for (const ticket of criticalTickets) {
      const ticketCard = el("div", {
        className: "p-4 hover:bg-red-400 cursor-pointer transition relative",
        attrs: { role: "button" }
      });

      //create an ellipsis menu for each ticket, as with active tickets
      const menu = EllipsisMenu();
      if (onOpenTicket) {
        menu.addEventListener("view", () => onOpenTicket(ticket)); // on view, open ticket
      }

      //ticket title row
      const topRow = el("div", { className: "flex justify-between items-start gap-3 mb-3" }, [
        el("div", { className: "font-semibold text-slate-900 truncate flex-1", text: ticket.title }),
        menu
      ]);

      const infoRow = el("div", { className: "flex justify-between items-start gap-3" }, [
        el("div", { className: "min-w-0 flex-1" }, [
          el("div", { className: "text-xs text-slate-500", text: `ID: ${ticket.autotask_ticket_id}` }),
          el("div", { className: "text-xs text-slate-500 mt-2 flex gap-2" }, [
            el("span", { text: `Priority: ${ticket.priority}` }),
            el("span", { text: `Confidence: ${(ticket.ai.confidence * 100).toFixed(0)}%` })
          ]),
          el("div", { className: "text-xs text-slate-500 mt-2", text: `Due: ${ticket.due_date}` })
        ])
      ]);

      ticketCard.append(topRow, infoRow);
      criticalTicketsWrap.append(ticketCard);
    }
  });

  container.append(criticalSection);

  return container;
}

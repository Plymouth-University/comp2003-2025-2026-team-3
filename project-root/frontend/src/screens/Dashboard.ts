import { el } from "../lib/dom.js";
import { EllipsisMenu } from "../components/EllipsisMenu.js";

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

export function Dashboard(): HTMLElement {
  const container = el("div", { className: "w-full" });

  container.append(
    //welcome header and subtitle
    el("div", { className: "bg-white rounded-lg shadow border border-slate-200 p-6 mb-6" }, [
      el("h1", { className: "text-3xl font-bold mb-2", text: "Welcome to Global 4 Ticket Interface" }),
      el("p", { className: "text-slate-600", text: "Manage and track your support tickets efficiently." })
    ]),
    
    //stat card elements below
    el("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-4" }, [
      el("div", { className: "bg-blue-50 rounded-lg border border-blue-200 p-4" }, [
        el("div", { className: "text-blue-600 font-semibold", text: "Critical Priority" }),
        el("div", { className: "text-3xl font-bold text-blue-900 mt-2", text: "25" }),
        el("p", { className: "text-sm text-blue-700 mt-2", text: "Tickets awaiting resolution" })
      ]),

      el("div", { className: "bg-green-50 rounded-lg border border-green-200 p-4" }, [
        el("div", { className: "text-green-600 font-semibold", text: "New Tickets" }),
        el("div", { className: "text-3xl font-bold text-green-900 mt-2", text: "16" }),
        el("p", { className: "text-sm text-green-700 mt-2", text: "Recent influx of tickets" })
      ]),

      el("div", { className: "bg-purple-50 rounded-lg border border-purple-200 p-4" }, [
        el("div", { className: "text-purple-600 font-semibold", text: "Today's Most Common Issue" }),
        el("div", { className: "text-3xl font-bold text-purple-900 mt-2", text: "Malware" }),
        el("p", { className: "text-sm text-purple-700 mt-2", text: "Category with most tickets today" })
      ]),
      el("div", { className: "bg-yellow-50 rounded-lg border border-yellow-200 p-4" }, [
        el("div", { className: "text-yellow-600 font-semibold", text: "Active Tickets" }),
        el("div", { className: "text-3xl font-bold text-yellow-900 mt-2", text: "103" }),
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
    const criticalTickets = allTickets.filter(t => t.priority === "Critical");
    
    if (criticalTickets.length === 0) {
      criticalTicketsWrap.innerHTML = '<div class="text-center py-8 text-slate-500">No critical priority tickets</div>';
      return;
    }
    
    //populate the section with the filtered tickets
    for (const ticket of criticalTickets) {
      const ticketCard = el("div", {
        className: "p-4 hover:bg-red-50 cursor-pointer transition relative",
        attrs: { role: "button" }
      });

      //create an ellipsis menu for each ticket, as with active tickets
      const menu = EllipsisMenu();

      //ticket title row
      const topRow = el("div", { className: "flex justify-between items-start gap-3 mb-3" }, [
        el("div", { className: "font-semibold text-slate-900 truncate flex-1", text: ticket.title }),
        menu
      ]);

      const infoRow = el("div", { className: "flex justify-between items-start gap-3" }, [
        el("div", { className: "min-w-0 flex-1" }, [
          el("div", { className: "text-xs text-slate-500", text: `ID: ${ticket.autotask_ticket_id}` }),
          el("div", { className: "text-sm text-slate-600 mt-1 line-clamp-2", text: ticket.description }),
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

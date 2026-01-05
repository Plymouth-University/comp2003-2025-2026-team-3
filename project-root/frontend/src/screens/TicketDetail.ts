import { el } from "../lib/dom.js";

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

export function TicketDetail(ticket: BackendTicket, onBack: () => void): HTMLElement {
  const wrap = el("div", { className: "bg-white rounded-xl shadow p-6 border border-slate-200" });

  //header with back button
  wrap.append(
    el("div", { className: "flex items-center justify-between gap-3 mb-6 border-b border-slate-200 pb-4" }, [
      el("div", {}, [
        el("div", { className: "text-xs text-slate-500", text: `ID: ${ticket.autotask_ticket_id}` }),
        el("h2", { className: "text-2xl font-bold mt-1", text: ticket.title }),
      ]),
      el("button", {
        className: "px-3 py-2 rounded bg-slate-900 text-white hover:bg-slate-800 transition",
        attrs: { type: "button" },
        text: "Back",
      }),
    ])
  );

  //two-column layout -- left panel shows attributes, right panel shows description
  const contentWrap = el("div", { className: "grid grid-cols-3 gap-6" });

  //left column - attributes
  const leftColumn = el("div", { className: "col-span-1 space-y-4 border-r border-slate-200 pr-6" });
  
  //ticket attributes to display with correlating values
  const attributes = [
    { label: "Ticket Number", value: ticket.ticket_number },
    { label: "Company", value: ticket.company },
    { label: "Contact", value: ticket.contact },
    { label: "Status", value: ticket.status },
    { label: "Priority", value: ticket.priority },
    { label: "Created", value: ticket.created },
    { label: "Due Date", value: ticket.due_date },
    { label: "Category", value: ticket.ai.category },
    { label: "Confidence", value: `${(ticket.ai.confidence * 100).toFixed(0)}%` },
  ];

  //add attribute + value to left panel
  for (const attr of attributes) {
    leftColumn.append(
      el("div", { className: "space-y-1" }, [
        el("div", { className: "text-xs font-semibold text-slate-600 uppercase", text: attr.label }),
        el("div", { className: "text-sm text-slate-900", text: attr.value }),
      ])
    );
  }

  //right column - description (wider)
  const rightColumn = el("div", { className: "col-span-2 space-y-2 pl-6" }, [
    el("h3", { className: "text-lg font-bold text-slate-900", text: "Ticket Description" }),
    el("div", { className: "text-sm text-slate-700 whitespace-pre-wrap", text: ticket.description }),
  ]);

  contentWrap.append(leftColumn, rightColumn);
  wrap.append(contentWrap);

  //add click event to back button
  (wrap.querySelector("button") as HTMLButtonElement).addEventListener("click", onBack);

  return wrap;
}

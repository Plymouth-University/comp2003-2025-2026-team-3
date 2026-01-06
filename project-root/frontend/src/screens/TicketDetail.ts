import { el } from "../lib/dom.js";
import type { BackendTicket } from "../types.js";

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
    { label: "Source", value: ticket.source },
    { label: "Issue Type", value: ticket.issue_type },
    { label: "Sub Issue Type", value: ticket.sub_issue_type },
    { label: "Location", value: ticket.location },
    { label: "Work Type", value: ticket.work_type },
    { label: "Primary Resource", value: ticket.primary_resource },
    { label: "Secondary Resource", value: ticket.secondary_resource },
    { label: "Queue", value: ticket.queue },
    { label: "Category", value: ticket.ai.category },
    { label: "Confidence", value: `${(ticket.ai.confidence * 100).toFixed(0)}%` },
    { label: "Priority Score", value: String(ticket.ai.priority_score) },
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

  //divider line for progress updates section
  wrap.append(el("div", { className: "border-t border-slate-200 my-6" }));

  //progress Updates section
  const progressSection = el("div", { className: "space-y-4" }); //div element
  
  const progressHeader = el("div", { className: "flex items-center justify-between" }, [
    el("h3", { className: "text-lg font-bold text-slate-900", text: "Progress Updates" }),
    el("button", {
      className: "text-xl font-bold text-slate-900 hover:text-slate-600 transition",
      attrs: { type: "button" },
      text: "+", //add button for adding new updates
    }),
  ]);
  progressSection.append(progressHeader);

  //progress update box with staff member -- currently hardcoded dummy example, will be replaced in sem 2
  const updateBox = el("div", { className: "border border-slate-200 rounded-lg p-4 space-y-3 bg-orange-50" }, [
    el("div", { className: "flex items-start gap-3" }, [
      el("div", { className: "w-10 h-10 rounded-full bg-slate-300 flex items-center justify-center flex-shrink-0", text: "👤" }),
      el("div", { className: "flex-1 min-w-0" }, [
        el("div", { className: "font-semibold text-slate-900", text: "John Smith" }), //staff member name
        el("div", { className: "text-xs text-slate-500 mt-1", text: "Support Technician" }), //staff member role
      ]),
    ]),
    //text content of the update
    el("div", { className: "text-sm text-slate-700", text: "Investigated the issue and identified the root cause. Applied a temporary workaround while we develop a permanent fix. Customer confirmed the workaround is functioning correctly." }), 
    el("div", { className: "text-xs text-slate-500", text: "Updated 2 hours ago" }), //timestamp
  ]);
  progressSection.append(updateBox);

  wrap.append(progressSection);

  //add click event to back button
  const backButton = wrap.querySelector("button") as HTMLButtonElement;
  if (backButton) {
    backButton.addEventListener("click", onBack);
  }

  return wrap;
}

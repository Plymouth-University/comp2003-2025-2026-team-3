import { el } from "../shared/lib/dom.js";
import { fetchAssignmentRecommendation } from "../shared/api/aiAssignments.js";
import type { BackendTicket } from "../shared/types.js";

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
  const leftColumn = el("div", { className: "col-span-1 space-y-6 border-r border-slate-200 pr-6" });
  
  //General section
  const generalSection = el("div", { className: "space-y-3" });
  generalSection.append(
    el("h4", { className: "text-sm font-bold text-slate-700 uppercase tracking-wide", text: "General" })
  );
  const generalAttrs = [
    { label: "Company", value: ticket.company },
    { label: "Contact", value: ticket.contact },
    { label: "Status", value: ticket.status },
    { label: "Priority", value: ticket.priority },
    { label: "Location", value: ticket.location },
  ];
  for (const attr of generalAttrs) {
    generalSection.append(
      el("div", { className: "space-y-1" }, [
        el("div", { className: "text-xs font-semibold text-slate-600 uppercase", text: attr.label }),
        el("div", { className: "text-sm text-slate-900", text: attr.value }),
      ])
    );
  }
  leftColumn.append(generalSection);

  //divider between sections
  leftColumn.append(el("div", { className: "border-t border-slate-200" }));

  //Ticket Info section
  const ticketInfoSection = el("div", { className: "space-y-3" });
  ticketInfoSection.append(
    el("h4", { className: "text-sm font-bold text-slate-700 uppercase tracking-wide", text: "Ticket Info" })
  );
  const ticketInfoAttrs = [
    { label: "Issue Type", value: ticket.issue_type },
    { label: "Sub Issue Type", value: ticket.sub_issue_type },
    { label: "Source", value: ticket.source },
    { label: "Due Date", value: ticket.due_date },
    { label: "Strike Level", value: ticket.strike_level },
    { label: "Queue", value: ticket.queue },
    { label: "Category", value: ticket.ai.category },
    { label: "Confidence", value: `${ticket.ai.confidence.toFixed(0)}%` },
    { label: "Priority Score", value: String(ticket.ai.priority_score) },
  ];
  for (const attr of ticketInfoAttrs) {
    ticketInfoSection.append(
      el("div", { className: "space-y-1" }, [
        el("div", { className: "text-xs font-semibold text-slate-600 uppercase", text: attr.label }),
        el("div", { className: "text-sm text-slate-900", text: attr.value }),
      ])
    );
  }
  leftColumn.append(ticketInfoSection);

  //divider between sections
  leftColumn.append(el("div", { className: "border-t border-slate-200" }));

  //Assignment section
  const assignmentSection = el("div", { className: "space-y-3" });
  assignmentSection.append(
    el("h4", { className: "text-sm font-bold text-slate-700 uppercase tracking-wide", text: "Assignment" })
  );
  const assignmentAttrs = [
    { label: "Primary Resource", value: ticket.primary_resource },
    { label: "Secondary Resource", value: ticket.secondary_resource },
  ];
  for (const attr of assignmentAttrs) {
    assignmentSection.append(
      el("div", { className: "space-y-1" }, [
        el("div", { className: "text-xs font-semibold text-slate-600 uppercase", text: attr.label }),
        el("div", { className: "text-sm text-slate-900", text: attr.value }),
      ])
    );
  }
  const recommendationWrap = el("div", {
    className: "space-y-2 rounded-lg border border-cyan-200 bg-cyan-50 p-3",
  }, [
    el("div", { className: "text-xs font-semibold text-cyan-800 uppercase", text: "AI Recommendation" }),
    el("div", { className: "text-sm text-slate-700", text: "Loading assignment recommendation..." }),
  ]);
  assignmentSection.append(recommendationWrap);
  leftColumn.append(assignmentSection);

  //right column - description (wider)
  const rightColumn = el("div", { className: "col-span-2 space-y-4 pl-6" }, [
    el("div", { className: "text-xs text-slate-500", text: `Ticket #${ticket.ticket_number}` }),
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

  void fetchAssignmentRecommendation(ticket.autotask_ticket_id)
    .then((recommendation) => {
      recommendationWrap.innerHTML = "";
      recommendationWrap.append(
        el("div", { className: "text-xs font-semibold text-cyan-800 uppercase", text: "AI Recommendation" }),
        el("div", {
          className: "text-sm font-semibold text-slate-900",
          text: recommendation.recommended_display_name ?? "No recommended assignee",
        }),
        el("div", {
          className: "text-sm text-slate-700",
          text: recommendation.recommendation_summary,
        }),
      );

      if (recommendation.candidates.length > 0) {
        const candidateList = el("div", { className: "space-y-2 pt-2" });
        recommendation.candidates.slice(0, 3).forEach((candidate) => {
          candidateList.append(
            el("div", { className: "rounded border border-cyan-100 bg-white px-3 py-2" }, [
              el("div", {
                className: "text-sm font-semibold text-slate-900",
                text: `${candidate.display_name} (${candidate.score})`,
              }),
              el("div", {
                className: "text-xs text-slate-600",
                text: candidate.reasons.join(" "),
              }),
            ]),
          );
        });
        recommendationWrap.append(candidateList);
      }
    })
    .catch((error) => {
      console.error("Failed to load assignment recommendation", error);
      recommendationWrap.innerHTML = "";
      recommendationWrap.append(
        el("div", { className: "text-xs font-semibold text-cyan-800 uppercase", text: "AI Recommendation" }),
        el("div", { className: "text-sm text-red-600", text: "Failed to load assignment recommendation." }),
      );
    });

  return wrap;
}

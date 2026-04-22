import { el } from "../shared/lib/dom.js";
import {
  clearAssignmentOverride,
  fetchAssignmentRecommendation,
  setAssignmentOverride,
  type TicketAssignmentRecommendation,
} from "../shared/api/aiAssignments.js";
import type { BackendTicket } from "../shared/types.js";

type TicketDetailOptions = {
  readOnly?: boolean;
};

export function TicketDetail(
  ticket: BackendTicket,
  onBack: () => void,
  options?: TicketDetailOptions,
): HTMLElement {
  const isReadOnly = options?.readOnly ?? ticket.is_closed;
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
    { label: "Status", value: ticket.is_closed ? "Closed" : ticket.status },
    { label: "Priority", value: ticket.priority },
    { label: "Location", value: ticket.location },
    ...(ticket.is_closed && ticket.reason_closed
      ? [{ label: "Closure Reason", value: ticket.reason_closed }]
      : []),
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
    ...(ticket.category_override_reason
      ? [{ label: "Category Override Reason", value: ticket.category_override_reason }]
      : []),
    ...(ticket.category_override_set_at
      ? [{ label: "Category Override Set At", value: ticket.category_override_set_at }]
      : []),
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

  //add click event to back button
  const backButton = wrap.querySelector("button") as HTMLButtonElement;
  if (backButton) {
    backButton.addEventListener("click", onBack);
  }

  async function loadRecommendation(): Promise<void> {
    try {
      const recommendation = await fetchAssignmentRecommendation(ticket.autotask_ticket_id);
      renderRecommendation(recommendation);
    } catch (error) {
      console.error("Failed to load assignment recommendation", error);
      recommendationWrap.innerHTML = "";
      recommendationWrap.append(
        el("div", { className: "text-xs font-semibold text-cyan-800 uppercase", text: "AI Recommendation" }),
        el("div", { className: "text-sm text-red-600", text: "Failed to load assignment recommendation." }),
      );
    }
  }

  function renderRecommendation(recommendation: TicketAssignmentRecommendation): void {
    recommendationWrap.innerHTML = "";
    recommendationWrap.append(
      el("div", { className: "text-xs font-semibold text-cyan-800 uppercase", text: "AI Recommendation" }),
      el("div", {
        className: "text-sm font-semibold text-slate-900",
        text: recommendation.effective_display_name ?? recommendation.recommended_display_name ?? "No effective assignee",
      }),
      el("div", {
        className: "text-sm text-slate-700",
        text: recommendation.recommendation_summary,
      }),
    );

    if (recommendation.has_manual_override) {
      const overrideCard = el("div", {
        className: "rounded border border-amber-300 bg-amber-50 px-3 py-2 space-y-2",
      });
      overrideCard.append(
        el("div", {
          className: "text-xs font-semibold text-amber-800 uppercase",
          text: "Manual Override Active",
        }),
        el("div", {
          className: "text-sm text-slate-900",
          text: `Effective assignee: ${recommendation.manual_override_display_name ?? "Unknown"}`,
        }),
      );
      if (recommendation.manual_override_reason) {
        overrideCard.append(
          el("div", {
            className: "text-xs text-slate-700",
            text: `Reason: ${recommendation.manual_override_reason}`,
          }),
        );
      }
      const clearButton = el("button", {
        className: "rounded bg-amber-600 px-3 py-1 text-sm font-semibold text-white hover:bg-amber-700 transition",
        attrs: { type: "button" },
        text: "Clear Override",
      }) as HTMLButtonElement;
      clearButton.addEventListener("click", async () => {
        clearButton.disabled = true;
        try {
          const updated = await clearAssignmentOverride(ticket.autotask_ticket_id);
          renderRecommendation(updated);
        } catch (error) {
          console.error("Failed to clear override", error);
          clearButton.disabled = false;
        }
      });
      if (!isReadOnly) {
        overrideCard.append(clearButton);
      }
      recommendationWrap.append(overrideCard);
    }

    if (recommendation.candidates.length > 0) {
      const candidateList = el("div", { className: "space-y-2 pt-2" });
      recommendation.candidates.slice(0, 3).forEach((candidate) => {
        const card = el("div", { className: "rounded border border-cyan-100 bg-white px-3 py-2 space-y-2" });
        card.append(
          el("div", {
            className: "text-sm font-semibold text-slate-900",
            text: `${candidate.display_name} (${candidate.score})`,
          }),
          el("div", {
            className: "text-xs text-slate-600",
            text: candidate.reasons.join(" "),
          }),
          el("div", {
            className: "text-xs text-slate-500",
            text: `Load: ${candidate.open_primary_ticket_count} primary, ${candidate.open_secondary_ticket_count} secondary, ${candidate.high_priority_ticket_count} high-priority, weighted ${candidate.weighted_open_load.toFixed(2)}`,
          }),
        );

        if (!isReadOnly) {
          const overrideButton = el("button", {
            className: "rounded bg-slate-900 px-3 py-1 text-sm font-semibold text-white hover:bg-slate-800 transition",
            attrs: { type: "button" },
            text: recommendation.manual_override_profile_id === candidate.profile_id ? "Override Active" : "Set Override",
          }) as HTMLButtonElement;
          overrideButton.disabled = recommendation.manual_override_profile_id === candidate.profile_id;
          overrideButton.addEventListener("click", async () => {
            const reason = window.prompt(
              `Why are you overriding this ticket to ${candidate.display_name}?`,
              recommendation.manual_override_reason ?? "",
            );
            if (reason === null) return;
            overrideButton.disabled = true;
            try {
              const updated = await setAssignmentOverride(
                ticket.autotask_ticket_id,
                candidate.profile_id,
                reason.trim() || null,
              );
              renderRecommendation(updated);
            } catch (error) {
              console.error("Failed to save override", error);
              overrideButton.disabled = false;
            }
          });
          card.append(overrideButton);
        }
        candidateList.append(card);
      });
      recommendationWrap.append(candidateList);
    }
  }

  void loadRecommendation();

  return wrap;
}

import { TicketApiError, updateAITicketState, type TicketAIStateUpdate } from "../shared/api/aiTickets.js";
import { el } from "../shared/lib/dom.js";
import type { BackendTicket } from "../shared/types.js";

type EditableKey = keyof TicketAIStateUpdate;
type EditableControl = HTMLInputElement | HTMLTextAreaElement;

type EditableFieldConfig = {
  label: string;
  key: EditableKey;
  value: string | number | null;
  type?: "text" | "number" | "textarea";
};

type ReadonlyFieldConfig = {
  label: string;
  value: string | number | null | undefined;
};

function displayValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "N/A";
  return String(value);
}

function openConfirm(message: string): boolean {
  return window.confirm(message);
}

export function openTicketEditModal(
  ticket: BackendTicket,
  onSaved: (updatedTicket: BackendTicket) => void,
): void {
  const fields = new Map<EditableKey, EditableControl>();
  const initialValues = new Map<EditableKey, string>();

  const overlay = el("div", {
    className: "fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4",
  });

  const dialog = el("div", {
    className:
      "w-full max-w-6xl max-h-[90vh] overflow-y-auto rounded-lg bg-white shadow-2xl border border-slate-200",
    attrs: {
      role: "dialog",
      "aria-modal": "true",
      "aria-labelledby": `ticket-edit-title-${ticket.autotask_ticket_id}`,
    },
  });

  const errorMessage = el("div", {
    className: "hidden rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700",
  });

  const closeModal = (): void => {
    overlay.remove();
  };

  const editableField = (config: EditableFieldConfig): HTMLElement => {
    const inputClasses =
      "w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-cyan-500";
    const value = config.value === null || config.value === undefined ? "" : String(config.value);
    const control =
      config.type === "textarea"
        ? (el("textarea", {
            className: `${inputClasses} min-h-32 resize-y`,
            attrs: { rows: "6" },
          }) as HTMLTextAreaElement)
        : (el("input", {
            className: inputClasses,
            attrs: { type: config.type === "number" ? "number" : "text" },
          }) as HTMLInputElement);

    control.value = value;
    fields.set(config.key, control);
    initialValues.set(config.key, value.trim());

    return el("label", { className: "block space-y-1" }, [
      el("span", {
        className: "text-xs font-semibold uppercase text-slate-600",
        text: config.label,
      }),
      control,
    ]);
  };

  const readonlyField = (config: ReadonlyFieldConfig): HTMLElement =>
    el("div", { className: "space-y-1" }, [
      el("div", {
        className: "text-xs font-semibold uppercase text-slate-600",
        text: config.label,
      }),
      el("div", {
        className: "rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700",
        text: displayValue(config.value),
      }),
    ]);

  const section = (title: string, children: HTMLElement[]): HTMLElement =>
    el("section", { className: "space-y-3 border-slate-200 md:border-r md:pr-5 last:border-r-0" }, [
      el("h3", {
        className: "text-sm font-bold uppercase tracking-wide text-slate-700",
        text: title,
      }),
      ...children,
    ]);

  const collectChanges = (): TicketAIStateUpdate => {
    const changes: TicketAIStateUpdate = {};
    const numberLabels: Partial<Record<EditableKey, string>> = {
      confidence: "Confidence",
      priority_score: "Priority score",
    };

    for (const [key, control] of fields.entries()) {
      const value = control.value.trim();
      if (value === initialValues.get(key)) continue;

      if (key === "primary_resource" || key === "secondary_resource") {
        changes[key] = value || null;
        continue;
      }

      if (key === "confidence" || key === "priority_score") {
        const parsed = Number(value);
        if (value === "" || Number.isNaN(parsed)) {
          throw new Error(`${numberLabels[key]} must be a number.`);
        }
        if (key === "confidence" && (parsed < 0 || parsed > 100)) {
          throw new Error("Confidence must be between 0 and 100.");
        }
        changes[key] = parsed;
        continue;
      }

      changes[key] = value;
    }

    return changes;
  };

  const saveButton = el("button", {
    className:
      "rounded bg-green-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-green-300",
    attrs: { type: "button" },
    text: "Save Changes",
  }) as HTMLButtonElement;

  const discardButton = el("button", {
    className:
      "rounded bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700",
    attrs: { type: "button" },
    text: "Discard Changes",
  }) as HTMLButtonElement;

  saveButton.addEventListener("click", async () => {
    if (!openConfirm("Are you sure you want to save these ticket changes?")) return;

    errorMessage.classList.add("hidden");
    errorMessage.textContent = "";
    saveButton.disabled = true;

    try {
      const updatedTicket = await updateAITicketState(ticket.autotask_ticket_id, collectChanges());
      onSaved(updatedTicket);
      closeModal();
    } catch (error) {
      console.error("Failed to save ticket changes", error);
      if (error instanceof TicketApiError) {
        console.error("Ticket save error detail", error.detail);
      }
      errorMessage.textContent =
        error instanceof Error ? error.message : "Failed to save ticket changes.";
      errorMessage.classList.remove("hidden");
      saveButton.disabled = false;
    }
  });

  discardButton.addEventListener("click", () => {
    if (openConfirm("Are you sure you want to discard these ticket changes?")) {
      closeModal();
    }
  });

  dialog.append(
    el("div", { className: "sticky top-0 z-10 border-b border-slate-200 bg-white px-6 py-4" }, [
      el("div", {}, [
        el("div", {
          className: "text-xs text-slate-500",
          text: `ID: ${ticket.autotask_ticket_id}`,
        }),
        el("h2", {
          className: "mt-1 text-2xl font-bold text-slate-900",
          attrs: { id: `ticket-edit-title-${ticket.autotask_ticket_id}` },
          text: `Edit ${ticket.title}`,
        }),
      ]),
      errorMessage,
    ]),
    el("div", { className: "grid grid-cols-1 gap-5 px-6 py-5 md:grid-cols-4" }, [
      section("General", [
        readonlyField({ label: "Autotask Ticket ID", value: ticket.autotask_ticket_id }),
        readonlyField({ label: "Ticket Number", value: ticket.ticket_number }),
        editableField({ label: "Company", key: "company", value: ticket.company }),
        editableField({ label: "Contact", key: "contact", value: ticket.contact }),
        editableField({ label: "Status", key: "status", value: ticket.status }),
        editableField({ label: "Created", key: "created", value: ticket.created }),
      ]),
      section("Ticket Info", [
        editableField({ label: "Title", key: "title", value: ticket.title }),
        editableField({ label: "Issue Type", key: "issue_type", value: ticket.issue_type }),
        editableField({ label: "Sub Issue Type", key: "sub_issue_type", value: ticket.sub_issue_type }),
        editableField({ label: "Source", key: "source", value: ticket.source }),
        editableField({ label: "Due Date", key: "due_date", value: ticket.due_date }),
        editableField({ label: "Queue", key: "queue", value: ticket.queue }),
      ]),
      section("Assignment", [
        editableField({ label: "Primary Resource", key: "primary_resource", value: ticket.primary_resource }),
        editableField({ label: "Secondary Resource", key: "secondary_resource", value: ticket.secondary_resource }),
        readonlyField({ label: "Effective Assignee", value: ticket.effective_assignee_display_name }),
        readonlyField({ label: "Manual Override", value: ticket.manual_override_display_name }),
        readonlyField({ label: "Override Reason", value: ticket.manual_override_reason }),
        readonlyField({ label: "Override Set At", value: ticket.manual_override_set_at }),
      ]),
      section("AI State", [
        readonlyField({ label: "Category", value: ticket.ai.category }),
        readonlyField({ label: "Confidence", value: `${ticket.ai.confidence.toFixed(0)}%` }),
        readonlyField({ label: "Priority", value: ticket.priority }),
        readonlyField({ label: "Priority Score", value: ticket.ai.priority_score }),
        readonlyField({ label: "Method", value: ticket.ai.method }),
        readonlyField({ label: "Location", value: ticket.location }),
        readonlyField({ label: "Strike Level", value: ticket.strike_level }),
        readonlyField({ label: "Work Type", value: ticket.work_type }),
      ]),
    ]),
    el("div", { className: "border-t border-slate-200 px-6 py-5" }, [
      editableField({
        label: "Description",
        key: "description",
        value: ticket.description,
        type: "textarea",
      }),
    ]),
    el("div", { className: "sticky bottom-0 flex items-center justify-between gap-4 border-t border-slate-200 bg-white px-6 py-4" }, [
      discardButton,
      saveButton,
    ]),
  );

  overlay.append(dialog);
  document.body.append(overlay);
}

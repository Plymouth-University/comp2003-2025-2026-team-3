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

type StatusOption = {
  status: string;
  iconPath: string;
};

const STATUS_ICON_DIR = "./public/ticketstatus-icons";
const STATUS_ICON_LIST_URL = `${STATUS_ICON_DIR}/icon-status-list.json`;

function displayValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "N/A";
  return String(value);
}

function openConfirm(message: string): boolean {
  return window.confirm(message);
}

function parseStatusIconList(rawText: string): StatusOption[] {
  try {
    const parsed = JSON.parse(rawText) as Record<string, unknown>;
    return Object.entries(parsed)
      .map(([status, iconName]) => {
        if (typeof iconName !== "string" || !status || !iconName) return null;

        return {
          status,
          iconPath: `${STATUS_ICON_DIR}/${iconName}`,
        };
      })
      .filter((option): option is StatusOption => option !== null);
  } catch {
    // Fall back to the old status:icon line format for local/custom lists.
  }

  return rawText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0 && !line.startsWith("#"))
    .map((line) => {
      const separatorIndex = line.indexOf(":");
      if (separatorIndex === -1) return null;

      const status = line.slice(0, separatorIndex).trim();
      const iconName = line
        .slice(separatorIndex + 1)
        .trim()
        .replace(/^["']|["'],?$/g, "");
      if (!status || !iconName) return null;

      return {
        status: status.replace(/^["']|["']$/g, ""),
        iconPath: `${STATUS_ICON_DIR}/${iconName}`,
      };
    })
    .filter((option): option is StatusOption => option !== null);
}

function statusIcon(option: StatusOption): HTMLElement[] {
  if (!option.iconPath) return [];

  const img = el("img", {
    className: "h-4 w-4 object-contain",
    attrs: { src: option.iconPath, alt: "" },
  }) as HTMLImageElement;
  img.addEventListener("error", () => {
    img.remove();
  });
  return [img];
}

async function loadStatusOptions(currentStatus: string): Promise<StatusOption[]> {
  try {
    const response = await fetch(STATUS_ICON_LIST_URL);
    if (!response.ok) throw new Error(`Status icon list returned ${response.status}`);

    const options = parseStatusIconList(await response.text());
    if (options.length > 0) return options;
  } catch (error) {
    console.error("Failed to load status icon list", error);
  }

  return [{ status: currentStatus, iconPath: "" }];
}

export function openTicketEditModal(
  ticket: BackendTicket,
  onSaved: (updatedTicket: BackendTicket) => void,
): void {
  const fields = new Map<EditableKey, EditableControl>();
  const initialValues = new Map<EditableKey, string>();
  const cleanupCallbacks: Array<() => void> = [];

  const overlay = el("div", {
    className: "fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4",
  });

  const dialog = el("div", {
    className:
      "w-full max-w-6xl max-h-[90vh] overflow-y-auto rounded-lg bg-pink-100 shadow-2xl border border-slate-200",
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
    cleanupCallbacks.forEach((cleanup) => cleanup());
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

  const statusDropdownField = (
    label: string,
    key: EditableKey,
    value: string | number | null,
  ): HTMLElement => {
    const currentValue = value === null || value === undefined ? "" : String(value);
    const hiddenInput = el("input", {
      attrs: { type: "hidden" },
    }) as HTMLInputElement;
    hiddenInput.value = currentValue;
    fields.set(key, hiddenInput);
    initialValues.set(key, currentValue.trim());

    let options: StatusOption[] = [{ status: currentValue, iconPath: "" }];
    let isOpen = false;

    const selectedLabel = el("span", { className: "truncate", text: displayValue(currentValue) });
    const selectedIconSlot = el("span", { className: "flex h-5 w-5 shrink-0 items-center justify-center" });
    const list = el("div", {
      className:
        "hidden absolute z-30 mt-1 max-h-56 w-full overflow-y-auto rounded border border-slate-200 bg-white py-1 shadow-lg",
      attrs: { role: "listbox" },
    });
    const trigger = el("button", {
      className:
        "flex w-full items-center justify-between gap-3 rounded border border-slate-300 bg-white px-3 py-2 text-left text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-cyan-500",
      attrs: { type: "button", "aria-haspopup": "listbox", "aria-expanded": "false" },
    }, [
      el("span", { className: "flex min-w-0 items-center gap-2" }, [selectedIconSlot, selectedLabel]),
      el("span", { className: "text-xs text-slate-500", text: "v" }),
    ]) as HTMLButtonElement;

    const setSelected = (option: StatusOption): void => {
      hiddenInput.value = option.status;
      selectedLabel.textContent = option.status;
      selectedIconSlot.innerHTML = "";
      selectedIconSlot.append(...statusIcon(option));
    };

    const closeList = (): void => {
      isOpen = false;
      list.classList.add("hidden");
      trigger.setAttribute("aria-expanded", "false");
    };

    const renderOptions = (): void => {
      list.innerHTML = "";
      for (const option of options) {
        const item = el("button", {
          className:
            "flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-slate-800 hover:bg-slate-50",
          attrs: { type: "button", role: "option", "aria-selected": String(option.status === hiddenInput.value) },
        });
        item.append(
          el("span", { className: "flex h-5 w-5 shrink-0 items-center justify-center" }, [
            ...statusIcon(option),
          ]),
          el("span", { className: "truncate", text: option.status }),
        );
        item.addEventListener("click", (event) => {
          event.stopPropagation();
          setSelected(option);
          renderOptions();
          closeList();
        });
        list.append(item);
      }
    };

    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      isOpen = !isOpen;
      list.classList.toggle("hidden", !isOpen);
      trigger.setAttribute("aria-expanded", String(isOpen));
    });

    document.addEventListener("click", closeList);
    cleanupCallbacks.push(() => document.removeEventListener("click", closeList));

    void loadStatusOptions(currentValue).then((loadedOptions) => {
      options = loadedOptions.some((option) => option.status === currentValue)
        ? loadedOptions
        : [{ status: currentValue, iconPath: "" }, ...loadedOptions];
      const selected = options.find((option) => option.status === hiddenInput.value) ?? options[0];
      setSelected(selected);
      renderOptions();
    });

    setSelected(options[0]);
    renderOptions();

    return el("div", { className: "relative space-y-1" }, [
      el("div", {
        className: "text-xs font-semibold uppercase text-slate-600",
        text: label,
      }),
      trigger,
      list,
    ]);
  };

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
    el("div", { className: "sticky top-0 z-10 border-b border-slate-200 bg-pink-100 px-6 py-4" }, [
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
        statusDropdownField("Status", "status", ticket.status),
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
        readonlyField({ label: "Category Override Reason", value: ticket.category_override_reason }),
        readonlyField({ label: "Category Override Set At", value: ticket.category_override_set_at }),
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
    el("div", { className: "sticky bottom-0 flex items-center justify-between gap-4 border-t border-slate-200 bg-pink-100 px-6 py-4" }, [
      discardButton,
      saveButton,
    ]),
  );

  overlay.append(dialog);
  document.body.append(overlay);
}

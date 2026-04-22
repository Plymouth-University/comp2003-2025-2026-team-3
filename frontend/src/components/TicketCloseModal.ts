import { closeAITicketState, TicketApiError } from "../shared/api/aiTickets.js";
import { el } from "../shared/lib/dom.js";
import type { BackendTicket } from "../shared/types.js";

export function openTicketCloseModal(
  ticket: BackendTicket,
  onClosed: (closedTicket: BackendTicket) => void,
): void {
  const overlay = el("div", {
    className: "fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4",
  });

  const dialog = el("div", {
    className: "w-full max-w-md rounded-lg border border-slate-200 bg-emerald-200 p-6 shadow-2xl",
    attrs: {
      role: "dialog",
      "aria-modal": "true",
      "aria-labelledby": `ticket-close-title-${ticket.autotask_ticket_id}`,
    },
  });

  const reasonInput = el("textarea", {
    className:
      "mt-2 min-h-28 w-full resize-y rounded border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-cyan-500",
    attrs: {
      rows: "4",
      placeholder: "Write the closure reason...",
    },
  }) as HTMLTextAreaElement;

  const errorMessage = el("div", {
    className: "mt-3 hidden rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700",
  });

  const closeButton = el("button", {
    className:
      "rounded bg-green-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-green-300",
    attrs: { type: "button" },
    text: "Close Ticket",
  }) as HTMLButtonElement;

  const cancelButton = el("button", {
    className:
      "rounded bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700",
    attrs: { type: "button" },
    text: "Cancel",
  }) as HTMLButtonElement;

  const closeModal = (): void => {
    overlay.remove();
  };

  closeButton.addEventListener("click", async () => {
    const reason = reasonInput.value.trim();
    if (!reason) {
      errorMessage.textContent = "Please enter a reason before closing this ticket.";
      errorMessage.classList.remove("hidden");
      reasonInput.focus();
      return;
    }

    errorMessage.classList.add("hidden");
    errorMessage.textContent = "";
    closeButton.disabled = true;

    try {
      const closedTicket = await closeAITicketState(ticket.autotask_ticket_id, reason);
      onClosed(closedTicket);
      closeModal();
    } catch (error) {
      console.error("Failed to close ticket", error);
      if (error instanceof TicketApiError) {
        console.error("Ticket close error detail", error.detail);
      }
      errorMessage.textContent =
        error instanceof Error ? error.message : "Failed to close ticket.";
      errorMessage.classList.remove("hidden");
      closeButton.disabled = false;
    }
  });

  cancelButton.addEventListener("click", closeModal);
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) closeModal();
  });

  dialog.append(
    el("h2", {
      className: "text-xl font-bold text-slate-900",
      attrs: { id: `ticket-close-title-${ticket.autotask_ticket_id}` },
      text: "Close Ticket",
    }),
    el("p", {
      className: "mt-2 text-sm text-slate-600",
      text: `Why is ticket ${ticket.autotask_ticket_id} being closed?`,
    }),
    reasonInput,
    errorMessage,
    el("div", { className: "mt-5 flex justify-end gap-3" }, [
      cancelButton,
      closeButton,
    ]),
  );

  overlay.append(dialog);
  document.body.append(overlay);
  reasonInput.focus();
}

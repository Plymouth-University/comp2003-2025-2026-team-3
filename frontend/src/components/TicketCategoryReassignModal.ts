import {
  fetchAITicketCategories,
  reassignAITicketCategory,
  TicketApiError,
  type AITicketCategory,
} from "../shared/api/aiTickets.js";
import { el } from "../shared/lib/dom.js";
import type { BackendTicket } from "../shared/types.js";

function categoryLabel(category: AITicketCategory): string {
  return category.label === category.key ? category.key : `${category.label} (${category.key})`;
}

export function openTicketCategoryReassignModal(
  ticket: BackendTicket,
  onSaved: (updatedTicket: BackendTicket) => void,
): void {
  const overlay = el("div", {
    className: "fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4",
  });

  const dialog = el("div", {
    className: "w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-2xl",
    attrs: {
      role: "dialog",
      "aria-modal": "true",
      "aria-labelledby": `ticket-category-title-${ticket.autotask_ticket_id}`,
    },
  });

  const categorySelect = el("select", {
    className:
      "mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:bg-slate-100",
  }) as HTMLSelectElement;
  categorySelect.disabled = true;
  categorySelect.append(
    el("option", {
      attrs: { value: ticket.ai.category },
      text: `Current: ${ticket.ai.category}`,
    }),
  );

  const reasonInput = el("input", {
    className:
      "mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-cyan-500",
    attrs: {
      type: "text",
      placeholder: "Reason for manual category override...",
    },
  }) as HTMLInputElement;

  const loadingMessage = el("div", {
    className: "mt-2 text-xs text-slate-500",
    text: "Loading categories...",
  });

  const errorMessage = el("div", {
    className: "mt-3 hidden rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700",
  });

  const reassignButton = el("button", {
    className:
      "rounded bg-green-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-green-300",
    attrs: { type: "button" },
    text: "Re-assign",
  }) as HTMLButtonElement;
  reassignButton.disabled = true;

  const cancelButton = el("button", {
    className:
      "rounded bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700",
    attrs: { type: "button" },
    text: "Cancel",
  }) as HTMLButtonElement;

  const closeModal = (): void => {
    overlay.remove();
  };

  const showError = (message: string): void => {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
  };

  const hideError = (): void => {
    errorMessage.textContent = "";
    errorMessage.classList.add("hidden");
  };

  const renderCategories = (categories: AITicketCategory[]): void => {
    const sortedCategories = [...categories].sort((a, b) => a.label.localeCompare(b.label));
    const hasCurrent = sortedCategories.some((category) => category.key === ticket.ai.category);

    categorySelect.innerHTML = "";
    if (!hasCurrent) {
      categorySelect.append(
        el("option", {
          attrs: { value: ticket.ai.category },
          text: ticket.ai.category,
        }),
      );
    }
    for (const category of sortedCategories) {
      categorySelect.append(
        el("option", {
          attrs: { value: category.key },
          text: categoryLabel(category),
        }),
      );
    }
    categorySelect.value = ticket.ai.category;
    categorySelect.disabled = false;
    reassignButton.disabled = false;
  };

  const loadCategories = async (): Promise<void> => {
    try {
      renderCategories(await fetchAITicketCategories());
      loadingMessage.textContent = "";
      loadingMessage.classList.add("hidden");
    } catch (error) {
      console.error("Failed to load AI categories", error);
      loadingMessage.textContent = "Categories could not be loaded.";
      showError("Failed to load available categories.");
    }
  };

  reassignButton.addEventListener("click", async () => {
    const selectedCategory = categorySelect.value;
    const reason = reasonInput.value.trim();

    if (!selectedCategory) {
      showError("Please choose a category.");
      categorySelect.focus();
      return;
    }
    if (selectedCategory === ticket.ai.category) {
      showError("Please choose a different category.");
      categorySelect.focus();
      return;
    }
    if (!reason) {
      showError("Please enter a reason for the manual category override.");
      reasonInput.focus();
      return;
    }

    hideError();
    reassignButton.disabled = true;

    try {
      const updatedTicket = await reassignAITicketCategory(
        ticket.autotask_ticket_id,
        selectedCategory,
        reason,
      );
      onSaved(updatedTicket);
      closeModal();
    } catch (error) {
      console.error("Failed to reassign ticket category", error);
      if (error instanceof TicketApiError) {
        console.error("Category reassignment error detail", error.detail);
      }
      showError(error instanceof Error ? error.message : "Failed to reassign category.");
      reassignButton.disabled = false;
    }
  });

  cancelButton.addEventListener("click", closeModal);
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) closeModal();
  });

  dialog.append(
    el("h2", {
      className: "text-xl font-bold text-slate-900",
      attrs: { id: `ticket-category-title-${ticket.autotask_ticket_id}` },
      text: "Reassign Category",
    }),
    el("p", {
      className: "mt-2 text-sm text-slate-600",
      text: `Change the AI category for ticket ${ticket.autotask_ticket_id}.`,
    }),
    el("label", { className: "mt-4 block" }, [
      el("span", {
        className: "text-xs font-semibold uppercase text-slate-600",
        text: "Category",
      }),
      categorySelect,
    ]),
    loadingMessage,
    el("label", { className: "mt-4 block" }, [
      el("span", {
        className: "text-xs font-semibold uppercase text-slate-600",
        text: "Reason for Manual Category Override",
      }),
      reasonInput,
    ]),
    errorMessage,
    el("div", { className: "mt-5 flex justify-end gap-3" }, [
      cancelButton,
      reassignButton,
    ]),
  );

  overlay.append(dialog);
  document.body.append(overlay);
  void loadCategories();
  reasonInput.focus();
}

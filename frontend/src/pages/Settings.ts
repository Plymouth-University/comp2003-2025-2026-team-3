import { el } from "../shared/lib/dom.js";
import type { CurrentUserResponse } from "../shared/auth.js";
import {
  fetchAvailableSpecialismOptions,
  fetchMySpecialisms,
  replaceMySpecialisms,
  type AssignedSpecialism,
  type SpecialismOption,
} from "../shared/api/profileSpecialisms.js";

export function Settings(currentUser: CurrentUserResponse): HTMLElement {
  const wrap = el("div", { className: "bg-white rounded-xl shadow p-8 border border-slate-200" });
  const specialisationsSection = el("div", { className: "space-y-4" });
  const statusMessage = el("p", { className: "text-sm text-slate-500", text: "Loading specialisations..." });
  const tagsContainer = el("div", { className: "flex flex-wrap gap-3" });
  const saveHint = el("p", {
    className: "text-sm text-slate-500",
    text: "These specialisations now feed the AI assignment recommendation logic for category-matched tickets.",
  });

  let availableSpecialisations: SpecialismOption[] = [];
  let selectedSpecialismKeys = new Set<string>();
  let isSaving = false;

  function renderTags(): void {
    tagsContainer.innerHTML = "";
    if (selectedSpecialismKeys.size === 0) {
      tagsContainer.append(
        el("p", { className: "text-slate-500 text-sm", text: "No specialisations added yet" }),
      );
      return;
    }

    const labelByKey = new Map(availableSpecialisations.map((item) => [item.key, item.label]));
    Array.from(selectedSpecialismKeys).sort().forEach((specialismKey) => {
      const tag = el("div", {
        className: "flex items-center gap-2 bg-blue-100 text-blue-900 px-4 py-2 rounded-full",
      });

      const deleteButton = el("button", {
        className: "ml-2 text-blue-900 hover:text-blue-600 font-bold transition",
        attrs: isSaving ? { type: "button", disabled: "true" } : { type: "button" },
        text: "x",
      }) as HTMLButtonElement;
      deleteButton.addEventListener("click", async () => {
        if (isSaving) return;
        selectedSpecialismKeys.delete(specialismKey);
        renderTags();
        await saveSpecialisms();
      });

      tag.append(
        el("span", { text: labelByKey.get(specialismKey) ?? specialismKey }),
        deleteButton,
      );
      tagsContainer.append(tag);
    });
  }

  async function loadData(): Promise<void> {
    try {
      statusMessage.textContent = "Loading specialisations...";
      const [available, assigned] = await Promise.all([
        fetchAvailableSpecialismOptions(),
        fetchMySpecialisms(),
      ]);
      availableSpecialisations = available;
      selectedSpecialismKeys = new Set(
        assigned.map((item: AssignedSpecialism) => item.specialism.specialism_key),
      );
      statusMessage.textContent = `Managing specialisations for ${currentUser.profile.display?.display_name || currentUser.session.display_name}.`;
      renderTags();
      renderModalOptions();
    } catch (error) {
      console.error("Failed to load specialisations", error);
      statusMessage.textContent = "Failed to load specialisations.";
      statusMessage.className = "text-sm text-red-600";
    }
  }

  async function saveSpecialisms(): Promise<void> {
    isSaving = true;
    statusMessage.className = "text-sm text-slate-500";
    statusMessage.textContent = "Saving specialisations...";
    try {
      const saved = await replaceMySpecialisms(Array.from(selectedSpecialismKeys));
      selectedSpecialismKeys = new Set(saved.map((item) => item.specialism.specialism_key));
      statusMessage.className = "text-sm text-green-700";
      statusMessage.textContent = "Specialisations saved.";
      renderTags();
    } catch (error) {
      console.error("Failed to save specialisations", error);
      statusMessage.className = "text-sm text-red-600";
      statusMessage.textContent = "Failed to save specialisations.";
    } finally {
      isSaving = false;
    }
  }

  specialisationsSection.append(
    el("div", { className: "flex items-center justify-between mb-4" }, [
      el("div", {}, [
        el("h2", { className: "text-2xl font-bold", text: "Specialisations" }),
        el("p", {
          className: "text-sm text-slate-500 mt-1",
          text: "Choose the AI ticket categories you want the assignment engine to treat as your strengths.",
        }),
      ]),
      el("button", {
        className: "px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold text-sm",
        attrs: { type: "button" },
        text: "Add Specialisation +",
      }),
    ]),
  );

  specialisationsSection.append(statusMessage, tagsContainer, saveHint);
  wrap.append(specialisationsSection);

  const modalOverlay = el("div", {
    className: "hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50",
  });
  const modalContent = el("div", {
    className: "bg-white rounded-lg shadow-lg p-8 max-w-2xl w-full max-h-96 overflow-y-auto",
  });
  const modalText = el("p", {
    className: "text-slate-700 mb-4",
    text: "Select category-aligned specialisations to improve who the AI recommends for matching tickets.",
  });
  const tagsGrid = el("div", { className: "grid grid-cols-2 md:grid-cols-3 gap-3" });

  function renderModalOptions(): void {
    tagsGrid.innerHTML = "";
    availableSpecialisations.forEach((specialism) => {
      const selected = selectedSpecialismKeys.has(specialism.key);
      const tagBtn = el("button", {
        className: selected
          ? "px-4 py-2 bg-slate-900 text-white rounded-full transition text-sm font-medium"
          : "px-4 py-2 bg-slate-200 text-slate-900 rounded-full hover:bg-cyan-700 hover:text-white transition text-sm font-medium",
        attrs: isSaving ? { type: "button", disabled: "true" } : { type: "button" },
        text: specialism.label,
      }) as HTMLButtonElement;

      tagBtn.addEventListener("click", async () => {
        if (isSaving) return;
        if (selectedSpecialismKeys.has(specialism.key)) {
          selectedSpecialismKeys.delete(specialism.key);
        } else {
          selectedSpecialismKeys.add(specialism.key);
        }
        renderTags();
        renderModalOptions();
        await saveSpecialisms();
      });

      tagsGrid.append(tagBtn);
    });
  }

  modalContent.append(
    el("h3", { className: "text-xl font-bold mb-6", text: "Select Specialisations" }),
    modalText,
    tagsGrid,
  );

  const closeBtn = el("button", {
    className: "mt-6 w-full px-4 py-2 bg-slate-300 text-slate-900 rounded-lg hover:bg-slate-400 transition font-semibold",
    attrs: { type: "button" },
    text: "Close",
  });
  closeBtn.addEventListener("click", () => {
    modalOverlay.classList.add("hidden");
  });
  modalContent.append(closeBtn);
  modalOverlay.append(modalContent);

  const addButton = specialisationsSection.querySelector("button") as HTMLButtonElement;
  addButton.addEventListener("click", () => {
    modalOverlay.classList.remove("hidden");
  });

  modalOverlay.addEventListener("click", (event) => {
    if (event.target === modalOverlay) {
      modalOverlay.classList.add("hidden");
    }
  });

  wrap.append(modalOverlay);
  void loadData();
  return wrap;
}

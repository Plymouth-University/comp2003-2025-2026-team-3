import { el } from "../lib/dom.js";

export function Settings(): HTMLElement {
  const wrap = el("div", { className: "bg-white rounded-xl shadow p-8 border border-slate-200" });

  //Specialisations section
  const specialisationsSection = el("div", { className: "space-y-4" });
  specialisationsSection.append(
    el("div", { className: "flex items-center justify-between mb-4" }, [
      el("h2", { className: "text-2xl font-bold", text: "Specialisations" }),
      el("button", {
        className: "px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold text-sm",
        attrs: { type: "button" },
        text: "Add Specialisation +",
      }),
    ])
  );

  //container for specialisation tags
  const tagsContainer = el("div", { className: "flex flex-wrap gap-3" });
  specialisationsSection.append(tagsContainer);

  //hardcoded dummy placeholder for specialisation of dummy user
  const specialisations = new Set<string>([
    "Networks",
    "Database Management",
    "Cloud Infrastructure",
  ]);

  //function to render specialisation tags
  const renderTags = () => {
    tagsContainer.innerHTML = "";
    if (specialisations.size === 0) {
      tagsContainer.append(
        el("p", { className: "text-slate-500 text-sm", text: "No specialisations added yet" })
      );
      return;
    }

    for (const spec of specialisations) {
      const tag = el("div", {
        className: "flex items-center gap-2 bg-blue-100 text-blue-900 px-4 py-2 rounded-full",
      });

      tag.append(
        el("span", { text: spec }),
        el("button", {
          className: "ml-2 text-blue-900 hover:text-blue-600 font-bold transition",
          attrs: { type: "button" },
          text: "×",
        })
      );

      const deleteBtn = tag.querySelector("button") as HTMLButtonElement;
      deleteBtn.addEventListener("click", () => {
        specialisations.delete(spec);
        renderTags();
      });

      tagsContainer.append(tag);
    }
  };

  renderTags();
  wrap.append(specialisationsSection);

  //modal for adding specialisations
  const modalOverlay = el("div", {
    className: "hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50",
  });

  const modalContent = el("div", {
    className: "bg-white rounded-lg shadow-lg p-8 max-w-2xl w-full max-h-96 overflow-y-auto",
  });


  //explanatory text
  const modalText = el("p", {
    className: "text-slate-700 mb-4",
    text: "Select specialisations to add to your profile to let your colleagues know your strengths. \n Specialisations can be a work type, issue type, category, company or contact. \n Click on a specialisation to add it.",
  });

  //list of available categories and fake company names
  const availableSpecialisations = [
    "Access",
    "Admin/Sales",
    "Backups",
    "Company 4",
    "Company 11",
    "Company 05",
    "Cloud Infrastructure",
    "Data Analytics",
    "Database Management",
    "DevOps",
    "IT",
    "Maintenance",
    "Malware",
    "Networks",
    "Riley Thomas (Contact)",
    "Remote Support",
    "Sam Taylor (Contact)",
    "Security",
    "System Administration",
    "System Performance",
    "Web Development",
  ];

  modalContent.append(
    el("h3", { className: "text-xl font-bold mb-6", text: "Select Specialisations" }), modalText
  );

  const tagsGrid = el("div", { className: "grid grid-cols-2 md:grid-cols-3 gap-3" });

  for (const spec of availableSpecialisations) {
    const tagBtn = el("button", {
      className: `px-4 py-2 bg-slate-200 text-slate-900 rounded-full hover:bg-violet-400 hover:text-white transition text-sm font-medium`,
      attrs: { type: "button" },
      text: spec,
    });

    tagBtn.addEventListener("click", () => {
      specialisations.add(spec);
      renderTags();
      modalOverlay.classList.add("hidden");
    });

    tagsGrid.append(tagBtn);
  }

  modalContent.append(tagsGrid);

  //close button for modal
  const closeBtn = el("button", {
    className: "mt-6 w-full px-4 py-2 bg-slate-300 text-slate-900 rounded-lg hover:bg-rose-500 transition font-semibold",
    attrs: { type: "button" },
    text: "Close",
  });

  closeBtn.addEventListener("click", () => {
    modalOverlay.classList.add("hidden");
  });

  modalContent.append(closeBtn);
  modalOverlay.append(modalContent);

  //wire up the add specialisation button to open modal
  const addBtn = wrap.querySelector("button") as HTMLButtonElement;
  addBtn.addEventListener("click", () => {
    modalOverlay.classList.remove("hidden");
  });

  //close modal when clicking overlay
  modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) {
      modalOverlay.classList.add("hidden");
    }
  });

  wrap.append(modalOverlay);

  return wrap;
}

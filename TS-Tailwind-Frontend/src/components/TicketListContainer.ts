import { dummyTickets, type UITicketCard } from "../data/dummyTickets.js";
import { el } from "../lib/dom.js";
import { TicketCard } from "./TicketCard.js";

export function TicketListContainer(onOpenTicket: (id: string) => void): HTMLElement {
  let collapsed = false;
  let sortByPriority: "asc" | "desc" = "desc";
  let sortByDate: "asc" | "desc" = "asc";

  const container = el("div", {
    className: "bg-slate-300 rounded-xl shadow p-6 border border-gray-400 w-full",
  });

  const header = el("div", { className: "flex justify-between items-center mb-4" });
  header.append(el("h2", { className: "text-xl font-bold", text: "Backups" }));

  const btnRow = el("div", { className: "flex gap-3" });

  const collapseBtn = el("button", { attrs: { type: "button" } });
  const collapseImg = el("img", {
    className: "w-5 h-5",
    attrs: { src: "./assets/collapse-icon/collapseTriangle.png", alt: "collapse" },
  });
  collapseBtn.append(collapseImg);

  const dateBtn = el("button", { attrs: { type: "button" } });
  dateBtn.append(
    el("img", {
      className: "w-5 h-5 invert",
      attrs: { src: "./assets/sort-by-icon/sortIcon.png", alt: "Sort by Date" },
    })
  );

  const priorityBtn = el("button", { attrs: { type: "button" } });
  priorityBtn.append(
    el("img", {
      className: "w-5 h-5",
      attrs: { src: "./assets/priority-icon/danger.png", alt: "Sort by Priority" },
    })
  );

  btnRow.append(collapseBtn, dateBtn, priorityBtn);
  header.append(btnRow);

  const listWrap = el("div", { className: "flex flex-col gap-4" });

  const sortTickets = (tickets: UITicketCard[]) => {
    return [...tickets]
      .sort((a, b) => {
        const priorityOrder = { Critical: 3, Medium: 2, Low: 1 } as const;
        return sortByPriority === "asc"
          ? priorityOrder[a.priority] - priorityOrder[b.priority]
          : priorityOrder[b.priority] - priorityOrder[a.priority];
      })
      .sort((a, b) => {
        // mimic original: compare day-of-month from dueDate
        const dateA = new Date(a.dueDate).getDate();
        const dateB = new Date(b.dueDate).getDate();
        return sortByDate === "asc" ? dateA - dateB : dateB - dateA;
      });
  };

  const render = () => {
    listWrap.innerHTML = "";
    if (collapsed) return;
    for (const t of sortTickets(dummyTickets)) {
      listWrap.append(TicketCard(t, onOpenTicket));
    }
  };

  const toggleCollapse = () => {
    collapsed = !collapsed;
    collapseImg.setAttribute(
      "src",
      collapsed ? "./assets/collapse-icon/deCollapse.png" : "./assets/collapse-icon/collapseTriangle.png"
    );
    render();
  };

  collapseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleCollapse();
  });

  dateBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    sortByDate = sortByDate === "asc" ? "desc" : "asc";
    render();
  });

  priorityBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    sortByPriority = sortByPriority === "asc" ? "desc" : "asc";
    render();
  });

  container.append(header, listWrap);
  render();
  return container;
}

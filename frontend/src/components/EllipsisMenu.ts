import { el } from "../shared/lib/dom.js";

export function EllipsisMenu(): HTMLElement {
  const wrapper = el("div", { className: "relative" });

  const btn = el("button", {
    className:
      "p-2 rounded hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-400",
    attrs: { type: "button", "aria-label": "More actions" },
    text: "...",
  });

  const menu = el("div", {
    className:
      "hidden absolute right-0 mt-2 w-44 bg-white border border-slate-200 shadow-lg rounded-lg overflow-hidden z-10",
  });

  const mkItem = (label: string, onClick: () => void) => {
    const item = el("button", {
      className: "w-full text-left px-3 py-2 hover:bg-slate-50",
      attrs: { type: "button" },
      text: label,
    });
    item.addEventListener("click", (e) => {
      e.stopPropagation();
      onClick();
      menu.classList.add("hidden");
    });
    return item;
  };

  menu.append(
    mkItem("View", () => wrapper.dispatchEvent(new CustomEvent("view", { bubbles: true }))),
    mkItem("Edit", () => wrapper.dispatchEvent(new CustomEvent("edit", { bubbles: true }))),
    mkItem("Reassign Category", () => alert("Reassign Category")),
    mkItem("Close Ticket", () => wrapper.dispatchEvent(new CustomEvent("close", { bubbles: true })))
  );

  const closeOnOutsideClick = (e: MouseEvent) => {
    if (!wrapper.contains(e.target as Node)) menu.classList.add("hidden");
  };

  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    menu.classList.toggle("hidden");
  });

  document.addEventListener("click", closeOnOutsideClick);

  wrapper.append(btn, menu);
  return wrapper;
}

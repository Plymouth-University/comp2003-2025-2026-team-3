import { el } from "../lib/dom.js";
export function EllipsisMenu() {
    const wrapper = el("div", { className: "relative" });
    const btn = el("button", {
        className: "p-2 rounded hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-400",
        attrs: { type: "button", "aria-label": "More actions" },
        text: "⋯",
    });
    const menu = el("div", {
        className: "hidden absolute right-0 mt-2 w-44 bg-white border border-slate-200 shadow-lg rounded-lg overflow-hidden z-10",
    });
    const mkItem = (label, onClick) => {
        const item = el("button", {
            className: "w-full text-left px-3 py-2 hover:bg-slate-50",
            attrs: { type: "button" },
            text: label,
        });
        item.addEventListener("click", () => {
            onClick();
            menu.classList.add("hidden");
        });
        return item;
    };
    menu.append(mkItem("View", () => wrapper.dispatchEvent(new CustomEvent("view", { bubbles: true }))), mkItem("Duplicate", () => alert("Duplicate (demo)")), mkItem("Delete", () => alert("Delete (demo)")));
    const closeOnOutsideClick = (e) => {
        if (!wrapper.contains(e.target))
            menu.classList.add("hidden");
    };
    btn.addEventListener("click", () => {
        menu.classList.toggle("hidden");
    });
    document.addEventListener("click", closeOnOutsideClick);
    wrapper.append(btn, menu);
    return wrapper;
}
//# sourceMappingURL=EllipsisMenu.js.map
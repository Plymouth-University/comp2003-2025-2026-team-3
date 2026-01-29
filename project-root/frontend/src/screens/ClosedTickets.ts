import {el} from "../lib/dom.js";

export function ClosedTicketsPage(): HTMLElement {
  const wrap = el("div", { className: "bg-white rounded-xl shadow p-8 border border-slate-200" });
    wrap.append(
    el("h1", { className: "text-2xl font-bold mb-6", text: "Closed Tickets" }),
    el("p", { className: "text-slate-600", text: "Closed Tickets will be in construction soon. Please check back later." })
  );
  return wrap;
}
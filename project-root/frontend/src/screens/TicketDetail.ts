import { el } from "../lib/dom.js";

export function TicketDetail(id: string, onBack: () => void): HTMLElement {
  // Create a wrapper div with styling
  const wrap = el("div", { className: "bg-white rounded-xl shadow p-6 border border-slate-200" });

  // Add a header with ticket ID and a back button
  wrap.append(
    el("div", { className: "flex items-center justify-between gap-3" }, [
      el("div", {}, [
        el("div", { className: "text-xs text-slate-500", text: id }),
        el("h2", { className: "text-xl font-bold", text: "Ticket Details" }),
      ]),
      el("button", {
        className: "px-3 py-2 rounded bg-slate-900 text-white hover:bg-slate-800",
        attrs: { type: "button" },
        text: "Back",
      }),
    ])
  );

  // Add a click event to the back button to return to active tickets page
  (wrap.querySelector("button") as HTMLButtonElement).addEventListener("click", onBack);

  // Add ticket details
  wrap.append(
    el("div", { className: "mt-4 text-sm text-slate-700 space-y-2" }, [
      el("div", { text: `Ticket ID: ${id}` }),
      el("div", { className: "pt-2 text-slate-500", text: "Detailed ticket view coming soon." }),
    ])
  );

  return wrap;
}

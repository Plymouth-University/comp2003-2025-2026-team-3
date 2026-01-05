import { el } from "../lib/dom.js";

export function Dashboard(): HTMLElement {
  const container = el("div", { className: "max-w-4xl" });

  container.append(
    el("div", { className: "bg-white rounded-lg shadow border border-slate-200 p-6 mb-6" }, [
      el("h1", { className: "text-3xl font-bold mb-2", text: "Welcome to Global4 Ticket Interface" }),
      el("p", { className: "text-slate-600", text: "Manage and track your support tickets efficiently." })
    ]),

    el("div", { className: "grid grid-cols-1 md:grid-cols-3 gap-4" }, [
      el("div", { className: "bg-blue-50 rounded-lg border border-blue-200 p-4" }, [
        el("div", { className: "text-blue-600 font-semibold", text: "Active Tickets" }),
        el("div", { className: "text-3xl font-bold text-blue-900 mt-2", text: "—" }),
        el("p", { className: "text-sm text-blue-700 mt-2", text: "Tickets awaiting resolution" })
      ]),

      el("div", { className: "bg-green-50 rounded-lg border border-green-200 p-4" }, [
        el("div", { className: "text-green-600 font-semibold", text: "Resolved" }),
        el("div", { className: "text-3xl font-bold text-green-900 mt-2", text: "—" }),
        el("p", { className: "text-sm text-green-700 mt-2", text: "Closed tickets this month" })
      ]),

      el("div", { className: "bg-purple-50 rounded-lg border border-purple-200 p-4" }, [
        el("div", { className: "text-purple-600 font-semibold", text: "Categories" }),
        el("div", { className: "text-3xl font-bold text-purple-900 mt-2", text: "—" }),
        el("p", { className: "text-sm text-purple-700 mt-2", text: "Ticket categories detected" })
      ])
    ]),

    el("div", { className: "bg-white rounded-lg shadow border border-slate-200 p-6 mt-6" }, [
      el("h2", { className: "text-xl font-semibold mb-4", text: "Quick Start" }),
      el("ul", { className: "space-y-2 text-slate-600" }, [
        el("li", { text: "• Click 'Active Tickets' in the sidebar to view all open tickets" }),
        el("li", { text: "• Tickets are grouped by category with AI-powered analysis" }),
        el("li", { text: "• Use sort buttons to organize by date or priority" }),
        el("li", { text: "• Click any ticket card or use the ⋯ menu to view details" })
      ])
    ])
  );

  return container;
}

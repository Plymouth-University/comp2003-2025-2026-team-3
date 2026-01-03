import { el } from "./lib/dom.js";
import { TicketListContainer } from "./components/TicketListContainer.js";
import { dummyTickets } from "./data/dummyTickets.js";
function parseHash() {
    const h = location.hash.replace(/^#/, "");
    if (!h || h === "/")
        return { name: "dashboard" };
    const parts = h.split("/").filter(Boolean);
    if (parts[0] === "ticket" && parts[1])
        return { name: "ticket", id: parts[1] };
    return { name: "dashboard" };
}
function setHash(route) {
    if (route.name === "dashboard")
        location.hash = "#/";
    if (route.name === "ticket")
        location.hash = `#/ticket/${encodeURIComponent(route.id)}`;
}
function Sidebar() {
    const nav = el("aside", { className: "w-64 hidden md:block bg-white border-r border-slate-200" });
    const inner = el("div", { className: "p-4" });
    inner.append(el("div", { className: "font-bold text-lg mb-4", text: "My UI" }), el("button", {
        className: "w-full text-left px-3 py-2 rounded hover:bg-slate-50",
        attrs: { type: "button" },
        text: "Dashboard",
    }));
    inner.querySelector("button").addEventListener("click", () => setHash({ name: "dashboard" }));
    nav.append(inner);
    return nav;
}
function TopHeader() {
    const hdr = el("header", { className: "bg-white border-b border-slate-200" });
    hdr.append(el("div", { className: "px-4 py-3 flex items-center justify-between" }, [
        el("div", { className: "font-semibold", text: "Tickets" }),
        el("div", { className: "text-sm text-slate-500", text: "Vanilla TS + Tailwind (no React/Vite)" }),
    ]));
    return hdr;
}
function TicketDetail(id) {
    const t = dummyTickets.find((x) => x.ticketID === id);
    const wrap = el("div", { className: "bg-white rounded-xl shadow p-6 border border-slate-200" });
    wrap.append(el("div", { className: "flex items-center justify-between gap-3" }, [
        el("div", {}, [
            el("div", { className: "text-xs text-slate-500", text: id }),
            el("h2", { className: "text-xl font-bold", text: t?.ticketTitle ?? "Ticket" }),
        ]),
        el("button", {
            className: "px-3 py-2 rounded bg-slate-900 text-white hover:bg-slate-800",
            attrs: { type: "button" },
            text: "Back",
        }),
    ]));
    wrap.querySelector("button").addEventListener("click", () => setHash({ name: "dashboard" }));
    wrap.append(el("div", { className: "mt-4 text-sm text-slate-700 space-y-2" }, [
        el("div", { text: `Due date: ${t?.dueDate ?? "—"}` }),
        el("div", { text: `Priority: ${t?.priority ?? "—"}` }),
        el("div", { text: `Status: ${t ? t.status : "—"}` }),
        el("div", { className: "pt-2 text-slate-500", text: "Detail page is a simple demo route." }),
    ]));
    return wrap;
}
export function App(root) {
    root.innerHTML = "";
    const shell = el("div", { className: "min-h-screen flex" });
    const mainCol = el("div", { className: "flex-1 flex flex-col" });
    const content = el("main", { className: "p-4 md:p-6" });
    const renderRoute = () => {
        const r = parseHash();
        content.innerHTML = "";
        if (r.name === "dashboard") {
            content.append(TicketListContainer((id) => setHash({ name: "ticket", id })));
        }
        else {
            content.append(TicketDetail(r.id));
        }
    };
    window.addEventListener("hashchange", renderRoute);
    mainCol.append(TopHeader(), content);
    shell.append(Sidebar(), mainCol);
    root.append(shell);
    renderRoute();
}
//# sourceMappingURL=app.js.map
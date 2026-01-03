import { el, formatDueDate } from "../lib/dom.js";
import { EllipsisMenu } from "./EllipsisMenu.js";
import { StatusIconPaths, StatusLabels } from "../lib/ticketStatus.js";
function priorityDotClass(priority) {
    if (priority === "Critical")
        return "bg-red-500";
    if (priority === "Medium")
        return "bg-yellow-400";
    return "bg-green-400";
}
export function TicketCard(ticket, onOpen) {
    const card = el("button", {
        className: "bg-white p-4 relative shadow rounded text-left hover:ring-2 hover:ring-slate-400 transition w-full",
        attrs: { type: "button" },
    });
    const top = el("div", { className: "flex justify-between items-start gap-3" });
    const left = el("div", { className: "min-w-0" }, [
        el("div", { className: "text-xs text-slate-500", text: ticket.ticketID }),
        el("div", { className: "font-semibold truncate", text: ticket.ticketTitle }),
        el("div", { className: "text-sm text-slate-600 mt-1", text: `Due: ${formatDueDate(ticket.dueDate)}` }),
    ]);
    const statusWrap = el("div", { className: "flex items-center gap-2 shrink-0" });
    const icon = el("img", {
        className: "w-5 h-5",
        attrs: { src: StatusIconPaths[ticket.status], alt: StatusLabels[ticket.status] },
    });
    const label = el("span", { className: "text-sm text-slate-700", text: StatusLabels[ticket.status] });
    statusWrap.append(icon, label);
    const menu = EllipsisMenu();
    menu.addEventListener("view", () => onOpen(ticket.ticketID));
    top.append(left, el("div", { className: "flex items-center gap-2" }, [statusWrap, menu]));
    const dot = el("span", {
        className: `absolute bottom-3 right-3 w-3 h-3 rounded-full ${priorityDotClass(ticket.priority)}`,
    });
    card.append(top, dot);
    card.addEventListener("click", () => onOpen(ticket.ticketID));
    return card;
}
//# sourceMappingURL=TicketCard.js.map
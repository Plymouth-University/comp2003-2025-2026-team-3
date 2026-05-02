import { TicketListContainer } from "../components/TicketListContainer.js";
import type { BackendTicket } from "../shared/types.js";

export function TeamTickets(onOpenTicket: (ticket: BackendTicket) => void): HTMLElement {
  return TicketListContainer(onOpenTicket, { initialView: "team" });
}

import { TicketListContainer } from "../components/TicketListContainer.js";
import type { BackendTicket } from "../types.js";

//pass whole ticket object to TicketListContainer for handling ticket opening
export function ActiveTickets(onOpenTicket: (ticket: BackendTicket) => void): HTMLElement {
  return TicketListContainer(onOpenTicket);
}

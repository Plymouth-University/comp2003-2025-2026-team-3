import { TicketListContainer } from "../components/TicketListContainer.js";
import type { BackendTicket } from "../shared/types.js";

//pass whole ticket object to TicketListContainer for handling ticket opening
export function ActiveTickets(onOpenTicket: (ticket: BackendTicket) => void): HTMLElement {
  return TicketListContainer(onOpenTicket);
}

import { TicketListContainer } from "../components/TicketListContainer.js";

export function ActiveTickets(onOpenTicket: (id: string) => void): HTMLElement {
  return TicketListContainer(onOpenTicket);
}

import { TicketListContainer } from "../components/TicketListContainer.js";

type BackendTicket = {
  autotask_ticket_id: number;
  ticket_number: string;
  company: string;
  contact: string;
  status: string;
  priority: string;
  created: string;
  title: string;
  description: string;
  due_date: string;
  ai: {
    category: string;
    confidence: number;
  };
};

//pass whole ticket object to TicketListContainer for handling ticket opening
export function ActiveTickets(onOpenTicket: (ticket: BackendTicket) => void): HTMLElement {
  return TicketListContainer(onOpenTicket);
}

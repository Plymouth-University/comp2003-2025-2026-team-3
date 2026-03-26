import { TicketListContainer } from "../components/TicketListContainer.js";
import type { TicketViewKey } from "../shared/api/aiTickets.js";
import type { BackendTicket } from "../shared/types.js";

type ActiveTicketsOptions = {
  initialView?: TicketViewKey;
  onViewChange?: (view: TicketViewKey) => void;
};

//pass whole ticket object to TicketListContainer for handling ticket opening
export function ActiveTickets(
  onOpenTicket: (ticket: BackendTicket) => void,
  options?: ActiveTicketsOptions,
): HTMLElement {
  return TicketListContainer(onOpenTicket, {
    initialView: options?.initialView ?? "my-assigned",
    onViewChange: options?.onViewChange,
  });
}

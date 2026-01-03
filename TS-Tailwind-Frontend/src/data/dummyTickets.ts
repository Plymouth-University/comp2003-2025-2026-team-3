export type StatusKey =
  | "onHold"
  | "callbackRequired"
  | "immediateReviewRQD"
  | "customerEsc";

// this is what the UI will display pertaining to a ticket
export interface UITicketCard {
  ticketID: string;
  ticketTitle: string;
  dueDate: string; // YYYY-MM-DD
  priority: "Critical" | "Medium" | "Low";
  status: StatusKey;
}

// dummy data in JSON format for tickets to display
export const dummyTickets: UITicketCard[] = [
  {
    ticketID: "TX-0001",
    ticketTitle: "Backup failed on primary server",
    dueDate: "2025-12-18",
    priority: "Critical",
    status: "immediateReviewRQD",
  },
  {
    ticketID: "TX-0002",
    ticketTitle: "Restore point verification required",
    dueDate: "2025-12-17",
    priority: "Medium",
    status: "onHold",
  },
  {
    ticketID: "TX-0022",
    ticketTitle: "Unable to update account details",
    dueDate: "2025-12-16",
    priority: "Low",
    status: "callbackRequired",
  },
  {
    ticketID: "TX-0104",
    ticketTitle: "Customer escalation: missing backup snapshots",
    dueDate: "2025-12-15",
    priority: "Critical",
    status: "customerEsc",
  },
];

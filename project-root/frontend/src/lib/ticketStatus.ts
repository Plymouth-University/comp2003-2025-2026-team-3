import type { StatusKey } from "../data/dummyTickets.js";

export const StatusLabels: Record<StatusKey, string> = {
  onHold: "On hold",
  callbackRequired: "Callback required",
  immediateReviewRQD: "Immediate review",
  customerEsc: "Customer escalation",
};

export const StatusIconPaths: Record<StatusKey, string> = {
  onHold: "./assets/ticketstatus-icons/purpleclock.png",
  callbackRequired: "./assets/ticketstatus-icons/callback.png",
  immediateReviewRQD: "./assets/ticketstatus-icons/orangeexclamation.png",
  customerEsc: "./assets/ticketstatus-icons/redexclamation.png",
};

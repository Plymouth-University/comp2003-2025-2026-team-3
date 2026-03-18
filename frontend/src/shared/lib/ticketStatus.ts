export type StatusKey = "onHold" | "callbackRequired" | "immediateReviewRQD" | "customerEsc";

export const StatusLabels: Record<StatusKey, string> = {
  onHold: "On hold",
  callbackRequired: "Callback required",
  immediateReviewRQD: "Immediate review",
  customerEsc: "Customer escalation",
};

export const StatusIconPaths: Record<StatusKey, string> = {
  onHold: "./public/ticketstatus-icons/purpleclock.png",
  callbackRequired: "./public/ticketstatus-icons/callback.png",
  immediateReviewRQD: "./public/ticketstatus-icons/orangeexclamation.png",
  customerEsc: "./public/ticketstatus-icons/redexclamation.png",
};

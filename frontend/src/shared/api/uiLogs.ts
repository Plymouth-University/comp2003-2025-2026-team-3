import { API_BASE_URL } from "../auth.js";

type UIClickLogInput = {
  actionType: string;
  component: string;
  pagePath?: string;
  elementId?: string;
  durationMs?: number;
  details?: Record<string, unknown>;
};

export function logUIClick(input: UIClickLogInput): void {
  void fetch(`${API_BASE_URL}/api/v1/logs/ui-clicks`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action_type: input.actionType,
      component: input.component,
      page_path: input.pagePath ?? window.location.pathname,
      element_id: input.elementId,
      duration_ms: input.durationMs,
      details: input.details,
      occurred_at: new Date().toISOString(),
    }),
  }).catch((error) => {
    console.debug("UI log event was not persisted", error);
  });
}

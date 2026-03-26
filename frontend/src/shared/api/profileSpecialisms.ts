import { API_BASE_URL } from "../auth.js";

export type SpecialismOption = {
  key: string;
  label: string;
};

export type AssignedSpecialism = {
  specialism: {
    specialism_id: string;
    tenant_id: string;
    specialism_key: string;
    specialism_name: string;
    description: string | null;
    is_active: boolean;
    created_at: string;
  };
  proficiency_level: string | null;
  assigned_at: string;
};

export async function fetchAvailableSpecialismOptions(): Promise<SpecialismOption[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai/categories`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to load AI categories (${response.status})`);
  }

  const payload = (await response.json()) as { items: SpecialismOption[] };
  return payload.items;
}

export async function fetchMySpecialisms(): Promise<AssignedSpecialism[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/profile/specialisms`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to load assigned specialisms (${response.status})`);
  }

  return (await response.json()) as AssignedSpecialism[];
}

export async function replaceMySpecialisms(specialismKeys: string[]): Promise<AssignedSpecialism[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/profile/specialisms`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ specialism_keys: specialismKeys }),
  });
  if (!response.ok) {
    throw new Error(`Failed to save specialisms (${response.status})`);
  }

  return (await response.json()) as AssignedSpecialism[];
}

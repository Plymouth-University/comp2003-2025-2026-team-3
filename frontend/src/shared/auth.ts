export const API_BASE_URL = "http://localhost:8000";

export type AuthSession = {
  profile_id: string;
  tenant_id: string;
  entra_tenant_id: string;
  object_id: string;
  display_name: string;
  issuer: string;
  exp: number;
};

export type ProfileDisplay = {
  display_name: string;
  created_at: string;
  updated_at: string;
};

export type ProfileResponse = {
  profile_id: string;
  tenant_id: string;
  status: string;
  created_at: string;
  deactivated_at: string | null;
  deactivated_reason: string | null;
  display: ProfileDisplay | null;
};

export type CurrentUserResponse = {
  session: AuthSession;
  profile: ProfileResponse;
};

export async function fetchCurrentUser(): Promise<CurrentUserResponse | null> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    credentials: "include",
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Failed to load current user (${response.status})`);
  }

  return response.json() as Promise<CurrentUserResponse>;
}

export function startLogin(): void {
  window.location.href = `${API_BASE_URL}/auth/login`;
}

export async function logout(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok && response.status !== 204) {
    throw new Error(`Failed to log out (${response.status})`);
  }
}

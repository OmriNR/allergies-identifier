// User accounts: log in, register, load/update the current profile.
// Backed by /users and /login on the aller-scan-api.

import { ApiError, apiRequest } from "./httpClient";

export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  createdAt: string;
}

interface BackendUser {
  uuid: string;
  name: string;
  email: string;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
}

function mapUser(raw: BackendUser): User {
  return {
    id: raw.uuid,
    name: raw.name,
    email: raw.email,
    avatarUrl: raw.avatar_url ?? undefined,
    createdAt: raw.created_at,
  };
}

export async function getUser(id: string): Promise<User | null> {
  try {
    const raw = await apiRequest<BackendUser>(`/users/${id}`);
    return mapUser(raw);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

// Loads the profile for a given token (or the stored one, if omitted)
// without throwing when the token is missing/expired.
export async function getMe(token?: string): Promise<User | null> {
  try {
    const raw = await apiRequest<BackendUser>("/users/me", { token });
    return mapUser(raw);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) return null;
    throw err;
  }
}

export async function login(email: string, password: string): Promise<{ user: User; token: string }> {
  const { access_token } = await apiRequest<{ access_token: string; token_type: string }>(
    "/login/access-token",
    { method: "POST", form: { username: email, password } }
  );
  const user = await getMe(access_token);
  if (!user) {
    throw new ApiError("Could not load account", 401);
  }
  return { user, token: access_token };
}

// Creates the account (active immediately - the backend has no email
// verification step) and logs the caller straight in.
export async function register(email: string, password: string, name?: string): Promise<{ user: User; token: string }> {
  await apiRequest<BackendUser>("/users/", {
    method: "POST",
    json: { name: name?.trim() || email.split("@")[0], email, password },
  });
  return login(email, password);
}

// Updates the signed-in user's profile. The backend only accepts name and
// avatar_url on this endpoint (email changes aren't supported yet).
export async function updateUser(data: Partial<Pick<User, "name" | "avatarUrl">>): Promise<User> {
  const raw = await apiRequest<BackendUser>("/users/me", {
    method: "PATCH",
    json: { name: data.name, avatar_url: data.avatarUrl },
  });
  return mapUser(raw);
}

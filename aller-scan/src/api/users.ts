import { ALLER_SCAN_API_BASE_URL } from "./config";
import { ApiError, get, patch, post } from "./httpClient";

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
    const raw = await get<BackendUser>(`${ALLER_SCAN_API_BASE_URL}/users/${id}`);
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
    const raw = await get<BackendUser>(`${ALLER_SCAN_API_BASE_URL}/users/me`, { token });
    return mapUser(raw);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) return null;
    throw err;
  }
}

export async function login(email: string, password: string): Promise<{ user: User; token: string }> {
  const { access_token } = await post<{ access_token: string; token_type: string }>(
    `${ALLER_SCAN_API_BASE_URL}/login/access-token`,
    { form: { username: email, password } }
  );
  const user = await getMe(access_token);
  if (!user) {
    throw new ApiError("Could not load account", 401);
  }
  return { user, token: access_token };
}

export async function register(email: string, password: string, name?: string): Promise<{ user: User; token: string }> {
  await post<BackendUser>(`${ALLER_SCAN_API_BASE_URL}/users/`, {
    json: { name: name?.trim() || email.split("@")[0], email, password },
  });
  return login(email, password);
}

export async function updateUser(data: Partial<Pick<User, "name" | "avatarUrl">>): Promise<User> {
  const raw = await patch<BackendUser>(`${ALLER_SCAN_API_BASE_URL}/users/me`, {
    json: { name: data.name, avatar_url: data.avatarUrl },
  });
  return mapUser(raw);
}

// User accounts: log in, register, update profile.
// Builds on authentication.ts for credentials/tokens/verification/providers.

import { ApiError, delay, generateId, readCollection, writeCollection } from "./_mockClient";
import * as auth from "./authentication";

export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  createdAt: string;
}

const usersSeed: User[] = [
  {
    id: "seed-user-1",
    name: "Demo User",
    email: "demo@allerscan.app",
    createdAt: new Date().toISOString(),
  },
];

function users(): User[] {
  return readCollection<User>("users", usersSeed);
}

export async function getUser(id: string): Promise<User | null> {
  return delay(users().find((u) => u.id === id) ?? null);
}

export async function login(email: string, password: string): Promise<{ user: User; token: string }> {
  const result = await auth.verifyPassword(email, password);
  if (!result) {
    throw new ApiError("Invalid email or password", 401);
  }
  const user = await getUser(result.userId);
  if (!user) {
    throw new ApiError("Invalid email or password", 401);
  }
  const token = await auth.issueToken(user.id);
  return { user, token };
}

// Creates the account and sends a verification email; the caller isn't
// logged in yet until they verify via authentication.verifyEmailCode.
export async function register(email: string, password: string, name?: string): Promise<{ email: string }> {
  const id = generateId();
  const user: User = {
    id,
    name: name?.trim() || email.split("@")[0],
    email,
    createdAt: new Date().toISOString(),
  };

  await auth.createCredentials(id, email, password);
  writeCollection("users", [...users(), user]);
  await auth.sendVerificationEmail(email);

  return delay({ email });
}

export async function verifyRegistration(email: string, code: string): Promise<{ user: User; token: string }> {
  const { userId, token } = await auth.verifyEmailCode(email, code);
  const user = await getUser(userId);
  if (!user) {
    throw new ApiError("Account not found", 404);
  }
  return { user, token };
}

export async function updateUser(
  id: string,
  data: Partial<Pick<User, "name" | "avatarUrl" | "email">>
): Promise<User> {
  const all = users();
  const index = all.findIndex((u) => u.id === id);
  if (index === -1) {
    throw new ApiError("User not found", 404);
  }
  const updated = { ...all[index], ...data };
  const next = [...all];
  next[index] = updated;
  writeCollection("users", next);
  return delay(updated);
}

export async function loginWithGoogle(): Promise<{ user: User; token: string }> {
  const result = await auth.loginWithProvider("google");

  if (!result.isNewUser) {
    const user = await getUser(result.userId);
    if (!user) {
      throw new ApiError("Account not found", 404);
    }
    return { user, token: result.token };
  }

  const id = generateId();
  const user: User = {
    id,
    name: result.name,
    email: result.email,
    createdAt: new Date().toISOString(),
  };
  writeCollection("users", [...users(), user]);
  await auth.linkProvider("google", id);
  const token = await auth.issueToken(id);
  return { user, token };
}

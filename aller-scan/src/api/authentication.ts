// Authentication: session tokens, password credentials, email verification
// codes, password reset tokens, and OAuth-style providers.
//
// This is the lower-level layer that users.ts builds on for login/register.
// Pages call it directly for the pieces that don't produce a user profile
// (resend/verify code, request/reset password, provider login).

import { ApiError, delay, generateCode, generateToken, readCollection, writeCollection } from "./_mockClient";

const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000;
const CODE_TTL_MS = 10 * 60 * 1000;
const RESET_TOKEN_TTL_MS = 30 * 60 * 1000;

export type AuthProvider = "google";

interface Credential {
  userId: string;
  email: string;
  password: string;
  verified: boolean;
}

interface Session {
  token: string;
  userId: string;
  expiresAt: string;
}

interface VerificationCode {
  email: string;
  code: string;
  expiresAt: string;
}

interface PasswordResetToken {
  token: string;
  email: string;
  expiresAt: string;
}

interface ProviderLink {
  provider: AuthProvider;
  providerId: string;
  userId: string;
}

const credentialsSeed: Credential[] = [
  { userId: "seed-user-1", email: "demo@allerscan.app", password: "password123", verified: true },
];

function credentials(): Credential[] {
  return readCollection<Credential>("credentials", credentialsSeed);
}

function sessions(): Session[] {
  return readCollection<Session>("sessions", []);
}

function verificationCodes(): VerificationCode[] {
  return readCollection<VerificationCode>("verificationCodes", []);
}

function resetTokens(): PasswordResetToken[] {
  return readCollection<PasswordResetToken>("passwordResetTokens", []);
}

function providerLinks(): ProviderLink[] {
  return readCollection<ProviderLink>("providerLinks", []);
}

export async function createCredentials(userId: string, email: string, password: string): Promise<void> {
  const existing = credentials();
  if (existing.some((c) => c.email.toLowerCase() === email.toLowerCase())) {
    throw new ApiError("An account with this email already exists", 409);
  }
  writeCollection("credentials", [...existing, { userId, email, password, verified: false }]);
  return delay(undefined);
}

export async function verifyPassword(email: string, password: string): Promise<{ userId: string } | null> {
  const match = credentials().find(
    (c) => c.email.toLowerCase() === email.toLowerCase() && c.password === password
  );
  return delay(match ? { userId: match.userId } : null);
}

export async function issueToken(userId: string): Promise<string> {
  const token = generateToken();
  const expiresAt = new Date(Date.now() + SESSION_TTL_MS).toISOString();
  writeCollection("sessions", [...sessions(), { token, userId, expiresAt }]);
  return delay(token);
}

export async function getSession(token: string): Promise<{ userId: string } | null> {
  const session = sessions().find((s) => s.token === token);
  if (!session || new Date(session.expiresAt).getTime() < Date.now()) {
    return delay(null);
  }
  return delay({ userId: session.userId });
}

export async function invalidateToken(token: string): Promise<void> {
  writeCollection("sessions", sessions().filter((s) => s.token !== token));
  return delay(undefined);
}

// No real email provider is wired up yet, so verification/reset codes are
// logged to the console instead of actually being emailed.
export async function sendVerificationEmail(email: string): Promise<void> {
  const code = generateCode();
  const expiresAt = new Date(Date.now() + CODE_TTL_MS).toISOString();
  writeCollection("verificationCodes", [
    ...verificationCodes().filter((v) => v.email.toLowerCase() !== email.toLowerCase()),
    { email, code, expiresAt },
  ]);
  console.info(`[mock email] Verification code for ${email}: ${code}`);
  return delay(undefined);
}

export async function resendVerificationEmail(email: string): Promise<void> {
  return sendVerificationEmail(email);
}

export async function verifyEmailCode(email: string, code: string): Promise<{ userId: string; token: string }> {
  const entry = verificationCodes().find((v) => v.email.toLowerCase() === email.toLowerCase());
  if (!entry || entry.code !== code || new Date(entry.expiresAt).getTime() < Date.now()) {
    throw new ApiError("Invalid or expired verification code", 400);
  }

  const creds = credentials();
  const credential = creds.find((c) => c.email.toLowerCase() === email.toLowerCase());
  if (!credential) {
    throw new ApiError("Account not found", 404);
  }

  writeCollection(
    "credentials",
    creds.map((c) => (c.email.toLowerCase() === email.toLowerCase() ? { ...c, verified: true } : c))
  );
  writeCollection("verificationCodes", verificationCodes().filter((v) => v.email.toLowerCase() !== email.toLowerCase()));

  const token = await issueToken(credential.userId);
  return { userId: credential.userId, token };
}

// Always resolves the same way whether or not the email exists, so callers
// can't use this to enumerate registered accounts.
export async function requestPasswordReset(email: string): Promise<void> {
  const credential = credentials().find((c) => c.email.toLowerCase() === email.toLowerCase());
  if (credential) {
    const token = generateToken();
    const expiresAt = new Date(Date.now() + RESET_TOKEN_TTL_MS).toISOString();
    writeCollection("passwordResetTokens", [
      ...resetTokens().filter((t) => t.email.toLowerCase() !== email.toLowerCase()),
      { token, email, expiresAt },
    ]);
    console.info(`[mock email] Password reset link for ${email}: /reset-password?token=${token}`);
  }
  return delay(undefined);
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  const entry = resetTokens().find((t) => t.token === token);
  if (!entry || new Date(entry.expiresAt).getTime() < Date.now()) {
    throw new ApiError("Invalid or expired reset link", 400);
  }

  writeCollection(
    "credentials",
    credentials().map((c) => (c.email.toLowerCase() === entry.email.toLowerCase() ? { ...c, password: newPassword } : c))
  );
  writeCollection("passwordResetTokens", resetTokens().filter((t) => t.token !== token));
  return delay(undefined);
}

// Mock OAuth: real integration would redirect to the provider and exchange
// a code server-side. Here we just simulate a successful grant.
export async function loginWithProvider(
  provider: AuthProvider
): Promise<{ userId: string; token: string; isNewUser: boolean; email: string; name: string }> {
  const providerId = `mock-${provider}-user`;
  const link = providerLinks().find((p) => p.provider === provider && p.providerId === providerId);

  if (link) {
    const token = await issueToken(link.userId);
    return delay({ userId: link.userId, token, isNewUser: false, email: "", name: "" }, 500);
  }

  return delay(
    { userId: "", token: "", isNewUser: true, email: `${providerId}@gmail.com`, name: "Google User" },
    500
  );
}

export async function linkProvider(provider: AuthProvider, userId: string): Promise<void> {
  const providerId = `mock-${provider}-user`;
  writeCollection("providerLinks", [...providerLinks(), { provider, providerId, userId }]);
  return delay(undefined);
}

// Password-reset flow. The aller-scan-api backend has no email delivery or
// reset-token endpoints yet, so these are honest stubs rather than fake
// network calls:
// - requestPasswordReset resolves silently. ForgotPassword.tsx already
//   treats this as fire-and-forget and shows the same "check your email"
//   message regardless of the outcome (so real accounts can't be enumerated
//   once this is wired up server-side either).
// - resetPassword rejects with a clear message instead of pretending to
//   succeed, since ResetPassword.tsx does surface the error.

import { ApiError } from "./httpClient";

export async function requestPasswordReset(_email: string): Promise<void> {
  return Promise.resolve();
}

export async function resetPassword(_token: string, _newPassword: string): Promise<void> {
  throw new ApiError("Password reset isn't available yet. Please contact support.", 501);
}

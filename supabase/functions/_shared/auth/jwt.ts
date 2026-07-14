/**
 * JWT extraction primitive (WP-8B foundation).
 *
 * FRAMEWORK ONLY — this extracts and shapes claims from a bearer token; it is NOT an
 * authentication *flow* (no login/signup/onboarding — those are later WPs and are owned by
 * Supabase Auth). Signature verification against Supabase Auth is wired in the auth middleware
 * (WP-8C) using the authenticated client / GoTrue; here we provide the token parsing contract
 * used by that middleware.
 */
import { AppError } from "../errors/app-error.ts";
import { ERROR_CATALOGUE } from "../errors/catalogue.ts";
import type { AuthClaims } from "../types/context.ts";

/** Extract the bearer token from an Authorization header, or throw AUTH_REQUIRED. */
export function extractBearer(authorizationHeader: string | null): string {
  if (!authorizationHeader) {
    throw new AppError(ERROR_CATALOGUE.AUTH_REQUIRED, { detail: "Missing Authorization header" });
  }
  const [scheme, token] = authorizationHeader.split(" ");
  if (scheme?.toLowerCase() !== "bearer" || !token) {
    throw new AppError(ERROR_CATALOGUE.AUTH_REQUIRED, { detail: "Malformed Authorization header" });
  }
  return token;
}

/** Decode the (already-verified) JWT payload into typed claims. Verification is the caller's job. */
export function claimsFromPayload(payload: Record<string, unknown>): AuthClaims {
  const userId = typeof payload.sub === "string" ? payload.sub : "";
  if (!userId) {
    throw new AppError(ERROR_CATALOGUE.AUTH_REQUIRED, { detail: "JWT missing sub claim" });
  }
  return {
    userId,
    role: typeof payload.role === "string" ? payload.role : "authenticated",
    email: typeof payload.email === "string" ? payload.email : undefined,
  };
}

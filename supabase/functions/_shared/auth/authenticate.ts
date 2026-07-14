/**
 * Authentication middleware + ownership guard (WP-8C).
 *
 * WP-8B provided JWT *parsing* primitives (auth/jwt.ts) but explicitly deferred signature
 * VERIFICATION to WP-8C. This module closes that gap:
 *
 *   - `authenticate()` middleware verifies the bearer token's signature against Supabase Auth
 *     (GoTrue) and attaches the verified claims to the request context. Any failure → a generic
 *     ERR_UNAUTHENTICATED (401), matching DOC-P3-06 §04 / §05.1 (missing/expired/invalid JWT are
 *     intentionally indistinguishable to the client — §05.1 ordering note).
 *   - `requireOwnership()` is the single Surface-B authorization boundary (DOC-P3-06 §05): because
 *     Edge Functions run under service_role and RLS enforces nothing here, ownership MUST be
 *     checked in code. Mismatch → ERR_OWNERSHIP_MISMATCH (403).
 *
 * The verifier is injectable so services/handlers are unit-testable without a live GoTrue.
 */
import { createAuthenticatedClient } from "../db/client.ts";
import { extractBearer } from "./jwt.ts";
import { AppError } from "../errors/app-error.ts";
import { API_ERRORS } from "../errors/api-catalogue.ts";
import type { AppConfig } from "../config/config.ts";
import type { AuthClaims } from "../types/context.ts";
import type { Handler, Middleware } from "../middleware/types.ts";

/** Verifies a JWT and returns its claims, or throws. Swappable for tests. */
export type JwtVerifier = (jwt: string, config: AppConfig) => Promise<AuthClaims>;

/**
 * Default verifier: asks Supabase Auth (GoTrue) to validate the token's signature/expiry and
 * return the user. This is real verification, not a local decode — a forged/expired token is
 * rejected server-side.
 */
export const supabaseJwtVerifier: JwtVerifier = async (jwt, config) => {
  const client = createAuthenticatedClient(config, jwt);
  const { data, error } = await client.auth.getUser(jwt);
  if (error || !data?.user) {
    throw new AppError(API_ERRORS.ERR_UNAUTHENTICATED, {
      detail: error?.message ?? "getUser returned no user",
    });
  }
  return {
    userId: data.user.id,
    role: typeof data.user.role === "string" ? data.user.role : "authenticated",
    email: data.user.email,
  };
};

/**
 * Middleware that authenticates the request and attaches verified claims to a fresh context.
 * Every JWT failure surfaces as the same generic 401 (no information disclosure — §05.1).
 */
export function authenticate(verifier: JwtVerifier = supabaseJwtVerifier): Middleware {
  return (next: Handler): Handler => {
    return async (req, ctx) => {
      let token: string;
      try {
        token = extractBearer(req.headers.get("Authorization"));
      } catch {
        // Normalize the foundation AUTH_REQUIRED into the contract's ERR_UNAUTHENTICATED.
        throw new AppError(API_ERRORS.ERR_UNAUTHENTICATED, { detail: "missing/malformed bearer" });
      }
      let claims: AuthClaims;
      try {
        claims = await verifier(token, ctx.config);
      } catch (e) {
        if (AppError.isAppError(e)) throw e;
        throw new AppError(API_ERRORS.ERR_UNAUTHENTICATED, {
          detail: e instanceof Error ? e.message : String(e),
        });
      }
      return await next(req, { ...ctx, claims });
    };
  };
}

/**
 * Assert the authenticated caller owns the target resource (DOC-P3-06 §05). The internal detail
 * deliberately omits the ids (kept out of logs; DPDP / DOC-P3-07 §16).
 */
export function requireOwnership(claims: AuthClaims, resourceOwnerId: string): void {
  if (claims.userId !== resourceOwnerId) {
    throw new AppError(API_ERRORS.ERR_OWNERSHIP_MISMATCH, { detail: "ownership check failed" });
  }
}

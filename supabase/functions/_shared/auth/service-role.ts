/**
 * Service-role auth guard for scheduled jobs (LF-M03 / DCR-P3-07-004).
 *
 * cron-hard-delete and cron-retention-purge are meant to be invoked only by pg_cron via
 * net.http_post with `Authorization: Bearer <service_role key>` (see
 * ops/audits/audit-dpdp/RUNBOOK_schedule-retention-jobs-2026-07-30.md). They previously shipped
 * with `verify_jwt=false` at the gateway and no application-level check at all, so any request to
 * the URL — no token required — triggered a real deletion run. `authenticate()` can't be reused
 * here: it calls GoTrue's `auth.getUser()`, which only resolves end-user JWTs and rejects the
 * service_role key outright. This guard instead compares the bearer token directly against this
 * project's own `SUPABASE_SERVICE_ROLE_KEY`, in constant time, so only the scheduler (or an
 * operator holding that key) can invoke these endpoints.
 */
import { extractBearer } from "./jwt.ts";
import { AppError } from "../errors/app-error.ts";
import { API_ERRORS } from "../errors/api-catalogue.ts";
import type { Handler, Middleware } from "../middleware/types.ts";

/** Constant-time string comparison — avoids leaking the secret via response-time differences. */
export function timingSafeEqual(a: string, b: string): boolean {
  const bufA = new TextEncoder().encode(a);
  const bufB = new TextEncoder().encode(b);
  if (bufA.length !== bufB.length) return false;
  let diff = 0;
  for (let i = 0; i < bufA.length; i++) diff |= bufA[i] ^ bufB[i];
  return diff === 0;
}

/** Requires the bearer token to exactly match this project's service_role key. */
export function requireServiceRole(): Middleware {
  return (next: Handler): Handler => {
    return async (req, ctx) => {
      let token: string;
      try {
        token = extractBearer(req.headers.get("Authorization"));
      } catch {
        throw new AppError(API_ERRORS.ERR_UNAUTHENTICATED, { detail: "missing/malformed bearer" });
      }
      if (!timingSafeEqual(token, ctx.config.supabaseServiceRoleKey)) {
        throw new AppError(API_ERRORS.ERR_UNAUTHENTICATED, { detail: "bearer is not service_role" });
      }
      return await next(req, ctx);
    };
  };
}

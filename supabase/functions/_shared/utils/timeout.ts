/**
 * Timeout guard for internal Supabase/Postgres calls (MEDIUM audit finding —
 * ops/audits/audit-edge-functions/edge-function-audit.md: "no timeout guard on internal
 * Supabase/Postgres calls in any function — only the external RE call has one").
 *
 * Mirrors the AbortController-based discipline already used for the external RE call
 * (recommendations/re-client.ts RE_TIMEOUT_MS = 2500ms) — applied here to internal DB calls,
 * which previously had none at all and could hang until the platform's own function-timeout
 * killed the whole request with no typed, client-safe error.
 *
 * Supabase-js v2 query builders are thenables that support `.abortSignal()`, but not every call
 * site in this codebase builds (and holds a reference to) a query object before awaiting it — many
 * chain `.select()...maybeSingle()` directly in a `return await db.from(...)` expression. A
 * generic `Promise.race` timeout works uniformly at every call site without requiring each one to
 * be restructured, at the known cost of not aborting the underlying HTTP request itself (the
 * query keeps running server-side until Postgres's own statement timeout; the Edge Function simply
 * stops waiting and surfaces a clean, typed error instead of hanging).
 */
import { AppError } from "../errors/app-error.ts";
import { ERROR_CATALOGUE } from "../errors/catalogue.ts";

/**
 * Default internal DB-call timeout (ms). Deliberately distinct from RE_TIMEOUT_MS (2500ms, a
 * cross-service HTTP call to the external RE) — an internal Postgres round-trip over the
 * project's own service-role connection should be far faster than that; 5s is a generous ceiling
 * that only trips on a genuinely stuck connection/query, not normal latency variance.
 */
export const DB_TIMEOUT_MS = 5000;

/**
 * Race a promise against a timeout. On timeout, throws `AppError(ERROR_CATALOGUE.INTERNAL)` tagged
 * with `op` so logs/traces show exactly which internal call stalled — never leaked to the client
 * as anything but a generic 500 (DOC-P3-07), same discipline as `dbFail()` in
 * `_shared/services/adapters/supabase-stores.ts`.
 */
export function withTimeout<T>(
  promise: PromiseLike<T>,
  op: string,
  timeoutMs: number = DB_TIMEOUT_MS,
): Promise<T> {
  let timer: ReturnType<typeof setTimeout>;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => {
      reject(
        new AppError(ERROR_CATALOGUE.INTERNAL, {
          detail: `${op}: internal call timed out after ${timeoutMs}ms`,
        }),
      );
    }, timeoutMs);
  });
  return Promise.race([Promise.resolve(promise), timeout]).finally(() => clearTimeout(timer));
}

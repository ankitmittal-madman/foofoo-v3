import { supabase } from "../auth/supabaseClient";
import { logger } from "../lib/logger";
import { withActiveHousehold } from "../household/activeHousehold";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "";

// Request timeout budget (audit-onboarding-funnel HIGH finding: "no timeout on apiPost() —
// infinite loader risk"). No documented client-side convention existed yet; 15s mirrors the
// style of supabase/functions/recommendations/re-client.ts's RE_TIMEOUT_MS (AbortController +
// a single named constant), scaled up from that file's 2.5s service-to-service budget since this
// is a client-to-edge-function call over a real (possibly slow/mobile) network, not two backend
// services on the same infrastructure.
export const REQUEST_TIMEOUT_MS = 15000;

/** Client-facing error codes that are NOT part of the backend's app-error.ts catalogue — both
 * describe transport failures the backend never gets a chance to respond to. */
export const CLIENT_ERROR_CODES = {
  TIMEOUT: "TIMEOUT",
  NETWORK_ERROR: "NETWORK_ERROR",
} as const;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly traceId?: string,
    // Backend error taxonomy field (app-error.ts's `toClientJSON().error.code`), or one of
    // CLIENT_ERROR_CODES for failures that never reached the backend at all. Optional/undefined
    // for older call sites that predate this field, or a response with no code at all.
    public readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function isAbortError(e: unknown): boolean {
  return e instanceof Error && (e.name === "AbortError" || e.name === "TimeoutError");
}

/**
 * POST helper carrying the Supabase session JWT as a bearer token — the exact pattern
 * authenticate.ts's supabaseJwtVerifier expects (Authorization: Bearer <token>, verified against
 * live GoTrue via auth.getUser()).
 *
 * Applies a hard request timeout via AbortController (audit-onboarding-funnel HIGH finding —
 * previously an unbounded fetch() could leave a caller's mutation.isPending stuck forever on a
 * stalled network). A timeout throws a distinguishable ApiError (code TIMEOUT) rather than
 * hanging, so callers can render "request timed out, try again" instead of a silent spinner.
 */
export async function apiPost<TResponse>(path: string, body: unknown): Promise<TResponse> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) {
    throw new ApiError("No active session — sign in before calling the API", 401);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (e) {
    if (isAbortError(e)) {
      logger.warn("api.timeout", { path, timeout_ms: REQUEST_TIMEOUT_MS });
      throw new ApiError(
        "Request timed out — check your connection and try again.",
        0,
        undefined,
        CLIENT_ERROR_CODES.TIMEOUT,
      );
    }
    logger.warn("api.network_error", { path, detail: e instanceof Error ? e.message : String(e) });
    throw new ApiError(
      "Network error — check your connection and try again.",
      0,
      undefined,
      CLIENT_ERROR_CODES.NETWORK_ERROR,
    );
  } finally {
    clearTimeout(timer);
  }

  const traceId = res.headers.get("x-trace-id") ?? undefined;
  const json = await res.json().catch(() => ({}));

  if (!res.ok) {
    // Shape per app-error.ts's toClientJSON: { error: { code, message, retriable, trace_id, context? } }.
    const message = typeof json?.error?.message === "string" ? json.error.message : res.statusText;
    const code = typeof json?.error?.code === "string" ? json.error.code : undefined;
    throw new ApiError(message, res.status, traceId, code);
  }

  return json as TResponse;
}

/** Adds the signed-in user's selected household to a household-scoped request. Older/solo users
 * with no stored selection keep the server's compatibility default (their own user ID). */
export async function householdApiPost<TResponse>(
  path: string,
  body: Record<string, unknown>,
): Promise<TResponse> {
  return apiPost<TResponse>(path, await withActiveHousehold(body));
}

/**
 * GET helper, same auth/timeout/error-shape conventions as apiPost above (P0-2, 2026-08 — added
 * for GET /v1/user/export, the first GET endpoint the mobile client needs to call). Not a
 * refactor of apiPost: kept as a separate sibling function so apiPost's existing behavior/call
 * sites are untouched.
 */
export async function apiGet<TResponse>(path: string): Promise<TResponse> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) {
    throw new ApiError("No active session — sign in before calling the API", 401);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: "GET",
      headers: { authorization: `Bearer ${token}` },
      signal: controller.signal,
    });
  } catch (e) {
    if (isAbortError(e)) {
      logger.warn("api.timeout", { path, timeout_ms: REQUEST_TIMEOUT_MS });
      throw new ApiError(
        "Request timed out — check your connection and try again.",
        0,
        undefined,
        CLIENT_ERROR_CODES.TIMEOUT,
      );
    }
    logger.warn("api.network_error", { path, detail: e instanceof Error ? e.message : String(e) });
    throw new ApiError(
      "Network error — check your connection and try again.",
      0,
      undefined,
      CLIENT_ERROR_CODES.NETWORK_ERROR,
    );
  } finally {
    clearTimeout(timer);
  }

  const traceId = res.headers.get("x-trace-id") ?? undefined;
  const json = await res.json().catch(() => ({}));

  if (!res.ok) {
    const message = typeof json?.error?.message === "string" ? json.error.message : res.statusText;
    const code = typeof json?.error?.code === "string" ? json.error.code : undefined;
    throw new ApiError(message, res.status, traceId, code);
  }

  return json as TResponse;
}

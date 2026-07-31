/**
 * RE service client (Phase C) — the service-to-service call to the stateless Python RE.
 *
 * Auth scheme (RE-DOC-10 §9), defined exactly:
 *   timestamp     = floor(Date.now()/1000)                    (unix seconds)
 *   signedPayload = `${timestamp}.${rawBody}`                 (rawBody = the exact JSON sent)
 *   signature     = hex( HMAC-SHA256(sharedSecret, signedPayload) )
 *   headers:  X-Ghar-Signature: t=${timestamp},v1=${signature}
 *             X-Request-Id:     ${requestId}
 *   The RE verifies by recomputing the HMAC, constant-time comparing, and rejecting if
 *   |now - t| > 300s (replay guard). NOTE: the Phase B RE skeleton does not yet verify this
 *   header (no auth middleware there) — sending it now is forward-compatible; RE-side
 *   verification is a small follow-on, flagged in the summary.
 *
 * Timeout/retry (RE-DOC-10 §11): 2.5s timeout; retry AT MOST ONCE and ONLY on a network-level
 * failure (connection refused/reset → fetch throws). NEVER retry on timeout.
 */
import type { Logger } from "../_shared/logging/logger.ts";

/** Hard timeout for a single RE call attempt, in ms (RE-DOC-10 §11) — never retried on timeout. */
export const RE_TIMEOUT_MS = 2500;
/** Path appended to `cfg.gharReServiceUrl` to reach the RE's recommendation endpoint. */
export const RE_PATH = "/v1/recommendations";

export type FetchLike = (input: string, init: RequestInit) => Promise<Response>;

export type ReResult =
  | { ok: true; status: number; body: Record<string, unknown> }
  | {
    ok: false;
    kind: "timeout" | "network" | "http" | "bad_body";
    status?: number;
    detail: string;
  };

export interface ReClientDeps {
  fetchImpl?: FetchLike;
  timeoutMs?: number;
  now?: () => number; // injectable clock for deterministic signatures in tests
}

const encoder = new TextEncoder();

/** hex( HMAC-SHA256(secret, message) ). */
export async function hmacHex(secret: string, message: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, encoder.encode(message));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/**
 * Build the request headers for one signed call to the RE, per the auth scheme documented at the
 * top of this file (timestamp + HMAC-SHA256 signature over `${timestamp}.${rawBody}`).
 * @param secret - the shared RE service secret (`cfg.gharReServiceSecret`), never logged
 * @param rawBody - the exact JSON string being sent — must match byte-for-byte what is POSTed
 * @param requestId - correlation id echoed back as `X-Request-Id` for RE-side log correlation
 * @param now - injectable clock (ms since epoch) so tests get deterministic signatures
 * @returns the header map to attach to the outgoing fetch call
 */
export async function buildSignatureHeaders(
  secret: string,
  rawBody: string,
  requestId: string,
  now: () => number,
): Promise<Record<string, string>> {
  const timestamp = Math.floor(now() / 1000);
  const signature = await hmacHex(secret, `${timestamp}.${rawBody}`);
  return {
    "content-type": "application/json",
    "x-request-id": requestId,
    "x-ghar-signature": `t=${timestamp},v1=${signature}`,
  };
}

/** One attempt with a hard timeout. Distinguishes timeout (abort) from network error (throw). */
async function attempt(
  url: string,
  headers: Record<string, string>,
  rawBody: string,
  fetchImpl: FetchLike,
  timeoutMs: number,
): Promise<{ status: number; text: string }> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetchImpl(url, {
      method: "POST",
      headers,
      body: rawBody,
      signal: controller.signal,
    });
    const text = await res.text();
    return { status: res.status, text };
  } finally {
    clearTimeout(timer);
  }
}

function isAbort(e: unknown): boolean {
  return e instanceof Error && (e.name === "AbortError" || e.name === "TimeoutError");
}

/**
 * Call the RE. Returns a discriminated ReResult; never throws for transport failures (the caller
 * decides fallback vs passthrough).
 */
export async function callRecommendationEngine(
  payload: Record<string, unknown>,
  requestId: string,
  cfg: { gharReServiceUrl: string; gharReServiceSecret: string },
  logger: Logger,
  deps: ReClientDeps = {},
): Promise<ReResult> {
  const fetchImpl = deps.fetchImpl ?? (globalThis.fetch as FetchLike);
  const timeoutMs = deps.timeoutMs ?? RE_TIMEOUT_MS;
  const now = deps.now ?? Date.now;

  const rawBody = JSON.stringify(payload);
  const url = cfg.gharReServiceUrl.replace(/\/$/, "") + RE_PATH;
  const headers = await buildSignatureHeaders(cfg.gharReServiceSecret, rawBody, requestId, now);

  let networkRetried = false;
  for (let tries = 0; tries < 2; tries++) {
    try {
      const { status, text } = await attempt(url, headers, rawBody, fetchImpl, timeoutMs);
      if (status < 200 || status >= 300) {
        return { ok: false, kind: "http", status, detail: `RE returned HTTP ${status}` };
      }
      try {
        return { ok: true, status, body: JSON.parse(text) as Record<string, unknown> };
      } catch {
        return { ok: false, kind: "bad_body", status, detail: "RE response was not valid JSON" };
      }
    } catch (e) {
      if (isAbort(e)) {
        // TIMEOUT — never retry (RE-DOC-10 §11).
        logger.warn("re_call.timeout", { request_id: requestId, timeout_ms: timeoutMs });
        return { ok: false, kind: "timeout", detail: `RE call exceeded ${timeoutMs}ms` };
      }
      // NETWORK-level failure — retry at most once.
      if (!networkRetried) {
        networkRetried = true;
        logger.warn("re_call.network_retry", {
          request_id: requestId,
          detail: e instanceof Error ? e.message : String(e),
        });
        continue;
      }
      return {
        ok: false,
        kind: "network",
        detail: e instanceof Error ? e.message : String(e),
      };
    }
  }
  // Unreachable, but satisfies the type checker.
  return { ok: false, kind: "network", detail: "exhausted retries" };
}

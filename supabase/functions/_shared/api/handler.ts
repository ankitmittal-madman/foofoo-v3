/**
 * Handler wrapper (WP-8B foundation).
 *
 * `defineHandler` is the single entry point an Edge Function uses to serve requests: it builds
 * the RequestContext and applies the standard middleware pipeline (context → error-boundary →
 * logging → [endpoint-specific middleware]). Endpoints (WP-8C onward) supply their business
 * handler + any extra middleware (auth, validation, rate-limit); this wrapper supplies the
 * always-on infrastructure. No business logic lives here.
 *
 * CORS (added after a live 401 was traced to this exact gap — see corsHeaders() below): every
 * function here requires a JWT, and the platform gateway's own verify_jwt check runs before any
 * app code, including on the browser's CORS preflight OPTIONS request — which never carries an
 * Authorization header by spec. Result: any browser-based caller (Expo web, or any future web
 * client) fails at the preflight, before the real request is ever sent, with no visible error
 * beyond a generic network failure. Native app callers (iOS/Android via React Native's fetch)
 * never trigger a CORS preflight at all, so this was invisible there — only surfaced once someone
 * tested the web target.
 */
import { buildContext, requestLogging } from "../middleware/request-context.ts";
import { errorBoundary } from "../middleware/error-boundary.ts";
import { compose } from "../middleware/compose.ts";
import type { Handler, Middleware } from "../middleware/types.ts";

export interface DefineHandlerOptions {
  /** Endpoint-specific middleware (auth, validation, rate-limit), applied inside the base pipeline. */
  middleware?: Middleware[];
}

/**
 * CORS headers for a given request. Reflects the caller's own Origin rather than a wildcard —
 * no allow-list of production web origins exists yet (there is no deployed web client), and
 * auth is bearer-JWT-only (no cookies), so reflecting the origin without
 * Access-Control-Allow-Credentials carries no cross-site-cookie risk. Revisit with a real
 * allow-list once a production web origin exists.
 */
function corsHeaders(req: Request): HeadersInit {
  const origin = req.headers.get("origin") ?? "*";
  return {
    "access-control-allow-origin": origin,
    "vary": "Origin",
    "access-control-allow-methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "access-control-allow-headers": "authorization, content-type, x-request-id",
    "access-control-max-age": "86400",
  };
}

/**
 * Wrap a business handler with the always-on infrastructure pipeline and return a fetch handler
 * suitable for `Deno.serve`.
 */
export function defineHandler(
  handler: Handler,
  opts: DefineHandlerOptions = {},
): (req: Request) => Promise<Response> {
  const pipeline = compose([
    errorBoundary,
    requestLogging,
    ...(opts.middleware ?? []),
  ])(handler);

  return async (req: Request): Promise<Response> => {
    // Preflight is answered directly, before context/auth — it never carries a JWT by spec, so
    // routing it through the auth pipeline can only ever reject it.
    if (req.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(req) });
    }

    const ctx = buildContext(req);
    const res = await pipeline(req, ctx);
    const headers = new Headers(res.headers);
    for (const [k, v] of Object.entries(corsHeaders(req))) headers.set(k, v as string);
    return new Response(res.body, { status: res.status, statusText: res.statusText, headers });
  };
}

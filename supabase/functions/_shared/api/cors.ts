/**
 * CORS headers (fixes: browser callers — the Vercel web build and any future web client — were
 * getting blocked on the preflight OPTIONS request because no Edge Function ever sent an
 * Access-Control-Allow-Origin header, and none handled OPTIONS at all. Auth here is a Bearer
 * token in the Authorization header, never a cookie, so reflecting the caller's own Origin back
 * is safe — there's no ambient credential for a third-party page to ride on.
 */
export function corsHeaders(req: Request): Record<string, string> {
  const origin = req.headers.get("origin") ?? "*";
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, content-type, apikey, x-client-info",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

/** 204 preflight response for an OPTIONS request. */
export function corsPreflight(req: Request): Response {
  return new Response(null, { status: 204, headers: corsHeaders(req) });
}

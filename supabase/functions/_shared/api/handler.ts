/**
 * Handler wrapper (WP-8B foundation).
 *
 * `defineHandler` is the single entry point an Edge Function uses to serve requests: it builds
 * the RequestContext and applies the standard middleware pipeline (context → error-boundary →
 * logging → [endpoint-specific middleware]). Endpoints (WP-8C onward) supply their business
 * handler + any extra middleware (auth, validation, rate-limit); this wrapper supplies the
 * always-on infrastructure. No business logic lives here.
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
    const ctx = buildContext(req);
    return await pipeline(req, ctx);
  };
}

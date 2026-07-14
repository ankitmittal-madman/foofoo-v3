/**
 * Middleware composition (WP-8B foundation).
 *
 * `compose(mws)(handler)` applies middleware right-to-left so the FIRST listed runs OUTERMOST.
 * The canonical pipeline (WP-8A §9) is: request-context → error-boundary → logging → auth →
 * validate → rate-limit → handler. Endpoints assemble their pipeline from these pieces.
 */
import type { Handler, Middleware } from "./types.ts";

export function compose(middlewares: Middleware[]): (handler: Handler) => Handler {
  return (handler: Handler): Handler => middlewares.reduceRight((next, mw) => mw(next), handler);
}

/**
 * Request-context middleware (WP-8B foundation).
 *
 * Builds the RequestContext (trace id, child logger bound to the trace, config, method/url) and
 * threads it into the handler. Runs outermost so every downstream log carries the trace id.
 */
import { getConfig } from "../config/config.ts";
import { createLogger } from "../logging/logger.ts";
import { newTraceId } from "../utils/id.ts";
import type { RequestContext } from "../types/context.ts";
import type { Handler } from "./types.ts";

/** Create the base context for a request (called by the handler wrapper, see api/handler.ts). */
export function buildContext(req: Request): RequestContext {
  const config = getConfig();
  // x-request-id is the cross-service convention used with the RE (RE-DOC-10 §9); x-trace-id is
  // the WP-8B framework default. Honoring both means an inbound request_id survives as the trace
  // id from the very first log line (Phase D Task 1 — no separate id to reconcile downstream).
  const traceId = req.headers.get("x-request-id") ?? req.headers.get("x-trace-id") ?? newTraceId();
  const url = new URL(req.url);
  const logger = createLogger(config.logLevel, {
    trace_id: traceId,
    method: req.method,
    path: url.pathname,
  });
  return {
    traceId,
    logger,
    config,
    method: req.method,
    url,
    traceParent: req.headers.get("traceparent") ?? undefined,
  };
}

/** Logging middleware: records request start/finish with latency. */
export const requestLogging = (next: Handler): Handler => {
  return async (req, ctx) => {
    const start = performance.now();
    ctx.logger.info("request_start");
    const res = await next(req, ctx);
    ctx.logger.info("request_finish", {
      status: res.status,
      latency_ms: Math.round(performance.now() - start),
    });
    return res;
  };
};

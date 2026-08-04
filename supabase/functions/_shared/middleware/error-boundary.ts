/**
 * Error-boundary middleware (WP-8B foundation).
 *
 * Catches everything thrown downstream. AppErrors serialize to their client-safe envelope with
 * the correct HTTP status; unknown errors become a generic 500 (never leaking stack traces or DB
 * errors — DOC-P3-07). Internal detail is logged with the trace id; only safe fields reach the
 * client (DOC-P3-06 §21).
 */
import { AppError } from "../errors/app-error.ts";
import { ERROR_CATALOGUE } from "../errors/catalogue.ts";
import { resolveTelemetrySink } from "../telemetry/telemetry.ts";
import type { Handler, Middleware } from "./types.ts";

/**
 * Error-boundary middleware — catches everything thrown downstream and serializes it safely (see
 * file header).
 * Trigger: wraps every handler in the always-on infrastructure pipeline.
 * Writes to: nothing — only the HTTP response.
 * Reads from: nothing.
 * Error codes: passes through any AppError's own code; unknown errors become ERROR_CATALOGUE.INTERNAL.
 */
export const errorBoundary: Middleware = (next: Handler): Handler => {
  return async (req, ctx) => {
    try {
      return await next(req, ctx);
    } catch (e) {
      const appErr = AppError.isAppError(e) ? e : new AppError(ERROR_CATALOGUE.INTERNAL, {
        detail: e instanceof Error ? e.message : String(e),
      });

      const logFields = { code: appErr.code, status: appErr.httpStatus, detail: appErr.detail };
      if (appErr.httpStatus >= 500) {
        ctx.logger.error("request_failed", logFields);
        // P1-7 (2026-08): every 500-level failure, across every Edge Function, now actually
        // reaches a real telemetry sink (webhookSink when TELEMETRY_WEBHOOK_URL is configured,
        // log-only otherwise) -- previously TelemetrySink/Container existed but nothing in any
        // live request path ever constructed or called one. Built directly here rather than via
        // di/container.ts's Container, since Container itself is still never instantiated by any
        // handler; this is the one place every request already flows through unconditionally.
        resolveTelemetrySink(ctx.logger, ctx.config.telemetryWebhookUrl).captureError(e, {
          trace_id: ctx.traceId,
          path: ctx.url?.pathname,
          ...logFields,
        });
      } else {
        ctx.logger.warn("request_rejected", logFields);
      }

      return new Response(JSON.stringify(appErr.toClientJSON(ctx.traceId)), {
        status: appErr.httpStatus,
        headers: { "content-type": "application/json", "x-trace-id": ctx.traceId },
      });
    }
  };
};

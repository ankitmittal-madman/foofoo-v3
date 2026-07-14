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
import type { Handler, Middleware } from "./types.ts";

export const errorBoundary: Middleware = (next: Handler): Handler => {
  return async (req, ctx) => {
    try {
      return await next(req, ctx);
    } catch (e) {
      const appErr = AppError.isAppError(e) ? e : new AppError(ERROR_CATALOGUE.INTERNAL, {
        detail: e instanceof Error ? e.message : String(e),
      });

      const logFields = { code: appErr.code, status: appErr.httpStatus, detail: appErr.detail };
      if (appErr.httpStatus >= 500) ctx.logger.error("request_failed", logFields);
      else ctx.logger.warn("request_rejected", logFields);

      return new Response(JSON.stringify(appErr.toClientJSON(ctx.traceId)), {
        status: appErr.httpStatus,
        headers: { "content-type": "application/json", "x-trace-id": ctx.traceId },
      });
    }
  };
};

/**
 * Observability hooks (WP-8B foundation).
 *
 * Framework-level timing + error-capture seams (WP-8A §27). Concrete sinks (Sentry, PostHog —
 * DOC-P3-08 §09) are wired via env-configured adapters in a later WP; here we expose the seams
 * and a default no-op/log adapter so instrumentation call sites can exist now. No secrets, no PII.
 */
import type { Logger } from "../logging/logger.ts";

export interface TelemetrySink {
  captureError(error: unknown, fields?: Record<string, unknown>): void;
  recordMetric(name: string, value: number, fields?: Record<string, unknown>): void;
}

/** Default sink: routes to the structured logger. Replaced by Sentry/PostHog adapters later. */
export function loggerSink(logger: Logger): TelemetrySink {
  return {
    captureError: (error, fields) =>
      logger.error("telemetry_error", {
        error: error instanceof Error ? error.message : String(error),
        ...fields,
      }),
    recordMetric: (name, value, fields) =>
      logger.info("telemetry_metric", { metric: name, value, ...fields }),
  };
}

/**
 * Real alerting sink (P1-7, 2026-08): POSTs a JSON payload to an operator-configured webhook URL
 * for every captured error (never for metrics -- those stay log-only, to avoid spamming a webhook
 * on every request). Deliberately generic (a plain URL, not a specific vendor SDK) since this repo
 * has no real Sentry/PostHog credentials to wire honestly; a generic webhook (Slack incoming
 * webhook, a custom collector, etc.) is something an operator can point anywhere via
 * TELEMETRY_WEBHOOK_URL without this code needing to know which vendor is on the other end.
 *
 * Fire-and-forget with a short timeout, and always falls back to `fallback`'s own captureError
 * too -- a webhook failure (network error, wrong URL, receiver down) must never be the reason an
 * actual application error goes unlogged. `recordMetric` always delegates straight to `fallback`
 * (log-only), unchanged from before this sink existed.
 */
export function webhookSink(url: string, fallback: TelemetrySink): TelemetrySink {
  return {
    captureError: (error, fields) => {
      fallback.captureError(error, fields);
      const payload = {
        type: "error",
        message: error instanceof Error ? error.message : String(error),
        ...fields,
        timestamp: new Date().toISOString(),
      };
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 3000);
      fetch(url, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      })
        .catch(() => {
          // Best-effort only -- the error itself was already captured by `fallback` above, so a
          // webhook delivery failure is not re-thrown or re-logged (would risk a log-amplification
          // loop if the webhook itself is what's failing).
        })
        .finally(() => clearTimeout(timer));
    },
    recordMetric: (name, value, fields) => fallback.recordMetric(name, value, fields),
  };
}

/** Resolve the real sink for this request: webhookSink when TELEMETRY_WEBHOOK_URL is configured,
 * the pre-existing log-only loggerSink otherwise. The one place callers (di/container.ts) should
 * build a TelemetrySink from config, so this decision lives in exactly one place. */
export function resolveTelemetrySink(logger: Logger, webhookUrl: string | null): TelemetrySink {
  const base = loggerSink(logger);
  return webhookUrl ? webhookSink(webhookUrl, base) : base;
}

/** Time an async operation and record its latency as a metric. */
export async function withTiming<T>(
  sink: TelemetrySink,
  name: string,
  op: () => Promise<T>,
): Promise<T> {
  const start = performance.now();
  try {
    return await op();
  } finally {
    sink.recordMetric(name, Math.round(performance.now() - start));
  }
}

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

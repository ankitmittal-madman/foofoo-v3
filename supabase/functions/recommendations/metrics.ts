/**
 * Lightweight in-process metrics (Phase D Task 3, RE-DOC-10/§11 "don't over-build" discipline).
 *
 * Module-level counters, reset whenever the Deno isolate restarts. No metrics backend — this is
 * meant to be replaced wholesale once Phase F picks a real deploy target with real monitoring.
 * A summary line is logged every SUMMARY_EVERY requests instead of wiring an export endpoint.
 */
import type { Logger } from "../_shared/logging/logger.ts";

export interface Counters {
  requests_total: number;
  success_total: number;
  partial_total: number; // RE served plates but warnings[] was non-empty (Task 4)
  timeout_total: number;
  fallback_total: number; // any RE failure (timeout/network/http/bad_body) served the fallback plate
  errors_total: number; // non-RE failures (validation, auth, internal)
}

const counters: Counters = {
  requests_total: 0,
  success_total: 0,
  partial_total: 0,
  timeout_total: 0,
  fallback_total: 0,
  errors_total: 0,
};

const SUMMARY_EVERY = 50;

/**
 * Increment the module-level counters for one completed recommendations request.
 * @param outcome - which bucket this request landed in; "timeout_fallback" increments both
 *   `timeout_total` and `fallback_total` since a timeout always results in a served fallback plate
 */
export function recordRequest(
  outcome: "success" | "partial" | "timeout_fallback" | "fallback" | "error",
): void {
  counters.requests_total++;
  switch (outcome) {
    case "success":
      counters.success_total++;
      break;
    case "partial":
      counters.partial_total++;
      break;
    case "timeout_fallback":
      counters.timeout_total++;
      counters.fallback_total++;
      break;
    case "fallback":
      counters.fallback_total++;
      break;
    case "error":
      counters.errors_total++;
      break;
  }
}

/** Return a copy of the current in-process counters (safe to log/inspect without mutation risk). */
export function snapshotMetrics(): Counters {
  return { ...counters };
}

/** Log a periodic summary line every SUMMARY_EVERY requests. Cheap, no timers/background tasks. */
export function maybeLogSummary(logger: Logger): void {
  if (counters.requests_total % SUMMARY_EVERY === 0) {
    logger.info("recommendations.metrics_summary", { ...counters });
  }
}

/** Test-only: reset counters to zero. */
export function resetMetricsForTests(): void {
  counters.requests_total = 0;
  counters.success_total = 0;
  counters.partial_total = 0;
  counters.timeout_total = 0;
  counters.fallback_total = 0;
  counters.errors_total = 0;
}

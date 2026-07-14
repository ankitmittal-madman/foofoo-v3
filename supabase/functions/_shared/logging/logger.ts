/**
 * Structured JSON logger (WP-8B foundation).
 *
 * Org coding standard: structured logging only — this is the single sanctioned sink; product
 * code must never call console.* directly (coding-standards-enforcer). Every line is JSON with a
 * level, timestamp, message, and structured fields. Callers attach `trace_id`. NO PII and NO
 * secrets may be logged (DOC-P3-07 §16 / DPDP).
 */
export type LogLevel = "debug" | "info" | "warn" | "error";

const LEVEL_ORDER: Record<LogLevel, number> = { debug: 10, info: 20, warn: 30, error: 40 };

export interface LogFields {
  [key: string]: unknown;
}

export interface Logger {
  debug(msg: string, fields?: LogFields): void;
  info(msg: string, fields?: LogFields): void;
  warn(msg: string, fields?: LogFields): void;
  error(msg: string, fields?: LogFields): void;
  /** Return a child logger with bound fields (e.g. trace_id, endpoint). */
  child(bound: LogFields): Logger;
}

function emit(
  level: LogLevel,
  minLevel: LogLevel,
  bound: LogFields,
  msg: string,
  fields?: LogFields,
) {
  if (LEVEL_ORDER[level] < LEVEL_ORDER[minLevel]) return;
  const line = JSON.stringify({
    level,
    ts: new Date().toISOString(),
    msg,
    ...bound,
    ...(fields ?? {}),
  });
  // Single sanctioned console usage in the codebase: the logger's own sink.
  // deno-lint-ignore no-console
  (level === "error" || level === "warn" ? console.error : console.log)(line);
}

/** Create a logger at a minimum level, optionally with pre-bound fields. */
export function createLogger(minLevel: LogLevel = "info", bound: LogFields = {}): Logger {
  return {
    debug: (m, f) => emit("debug", minLevel, bound, m, f),
    info: (m, f) => emit("info", minLevel, bound, m, f),
    warn: (m, f) => emit("warn", minLevel, bound, m, f),
    error: (m, f) => emit("error", minLevel, bound, m, f),
    child: (extra) => createLogger(minLevel, { ...bound, ...extra }),
  };
}

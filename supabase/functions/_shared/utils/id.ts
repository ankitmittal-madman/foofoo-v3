/**
 * ID / correlation helpers (WP-8B foundation).
 */

/** Generate a trace/correlation id for a request (used for log + audit join-back, DOC-P3-06 §07). */
export function newTraceId(): string {
  return crypto.randomUUID();
}

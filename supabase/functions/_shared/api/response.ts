/**
 * Response envelope helpers (WP-8B foundation).
 *
 * Uniform success envelope for Surface-B endpoints (DOC-P3-06 §20). Errors are produced by the
 * error-boundary middleware, not here. Every response carries the trace id header for audit
 * join-back (DOC-P3-06 §07).
 */
export function jsonOk<T>(data: T, traceId: string, status = 200): Response {
  return new Response(JSON.stringify({ data, trace_id: traceId }), {
    status,
    headers: { "content-type": "application/json", "x-trace-id": traceId },
  });
}

/** 204 No Content with trace header. */
export function noContent(traceId: string): Response {
  return new Response(null, { status: 204, headers: { "x-trace-id": traceId } });
}

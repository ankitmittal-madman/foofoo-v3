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

/**
 * Contract-shaped success response (WP-8C).
 *
 * The frozen API contract (DOC-P3-06 §06.x) specifies each success body as the payload fields at
 * the TOP LEVEL (e.g. `{ recorded, personalization_granted }`), not under a `data` wrapper. This
 * helper returns exactly that payload and additively includes `trace_id` — required on success
 * responses by DOC-P3-06 §22.1 and non-breaking per §17.2. Use this for endpoints whose response
 * shape is pinned by the frozen contract; `jsonOk` remains for internal, non-contract responses.
 */
export function jsonContract<T extends Record<string, unknown>>(
  payload: T,
  traceId: string,
  status = 200,
): Response {
  return new Response(JSON.stringify({ ...payload, trace_id: traceId }), {
    status,
    headers: { "content-type": "application/json", "x-trace-id": traceId },
  });
}

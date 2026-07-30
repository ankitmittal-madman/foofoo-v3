import { supabase } from "../auth/supabaseClient";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly traceId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * POST helper carrying the Supabase session JWT as a bearer token — the exact pattern
 * authenticate.ts's supabaseJwtVerifier expects (Authorization: Bearer <token>, verified against
 * live GoTrue via auth.getUser()).
 */
export async function apiPost<TResponse>(path: string, body: unknown): Promise<TResponse> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) {
    throw new ApiError("No active session — sign in before calling the API", 401);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  const traceId = res.headers.get("x-trace-id") ?? undefined;
  const json = await res.json().catch(() => ({}));

  if (!res.ok) {
    // Shape per app-error.ts's toClientJSON: { error: { code, message, retriable, trace_id, context? } }.
    const message = typeof json?.error?.message === "string" ? json.error.message : res.statusText;
    throw new ApiError(message, res.status, traceId);
  }

  return json as TResponse;
}

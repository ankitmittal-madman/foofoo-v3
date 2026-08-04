/**
 * Environment variable NAMES (WP-8B foundation).
 *
 * Single source of truth for env var keys, matching DOC-P3-08 §Env-Vars. Values are read only
 * through the typed config loader (config.ts) — never via bare Deno.env.get() elsewhere.
 * Secrets ("secret: true") must be server-side only and rotatable without code/schema change
 * (DOC-P3-07 §14.1).
 */
export interface EnvVarSpec {
  readonly key: string;
  readonly required: boolean;
  readonly secret: boolean;
}

/** The full set of environment variable specs this project reads (see file header). Consumed only
 * by config.ts's typed loader — never read directly via Deno.env.get() elsewhere. */
export const ENV_VARS = {
  ENVIRONMENT: { key: "FOOFOO_ENV", required: false, secret: false },
  LOG_LEVEL: { key: "LOG_LEVEL", required: false, secret: false },
  SUPABASE_URL: { key: "SUPABASE_URL", required: true, secret: false },
  SUPABASE_ANON_KEY: { key: "SUPABASE_ANON_KEY", required: true, secret: false },
  SUPABASE_SERVICE_ROLE_KEY: { key: "SUPABASE_SERVICE_ROLE_KEY", required: true, secret: true },
  SUPABASE_DB_URL: { key: "SUPABASE_DB_URL", required: false, secret: true },
  OPENWEATHERMAP_API_KEY: { key: "OPENWEATHERMAP_API_KEY", required: false, secret: true },
  ONESIGNAL_REST_API_KEY: { key: "ONESIGNAL_REST_API_KEY", required: false, secret: true },
  ONESIGNAL_APP_ID: { key: "ONESIGNAL_APP_ID", required: false, secret: false },
  CLOUDINARY_CLOUD_NAME: { key: "CLOUDINARY_CLOUD_NAME", required: false, secret: false },
  // Ghar RE service (Phase C). URL of the stateless Python RE; SECRET is the shared HMAC key for
  // service-to-service auth (RE-DOC-10 §9). Not required locally (sensible dev defaults apply);
  // MUST be set in staging/production (enforced in config.ts).
  GHAR_RE_SERVICE_URL: { key: "GHAR_RE_SERVICE_URL", required: false, secret: false },
  GHAR_RE_SERVICE_SECRET: { key: "GHAR_RE_SERVICE_SECRET", required: false, secret: true },
  // P1-7 (2026-08): optional real alerting sink. When set, the error-boundary middleware POSTs a
  // JSON payload here for every 500-level request failure across every Edge Function (see
  // telemetry.ts's webhookSink / middleware/error-boundary.ts). Deliberately generic (a plain
  // webhook URL, e.g. a Slack incoming-webhook or a custom collector), not a specific vendor SDK
  // (Sentry/PostHog) -- this repo has no real credentials for either, and inventing a fake
  // integration would be worse than a real, generic one an operator can point anywhere. Optional:
  // if unset, telemetry falls back to the pre-existing log-only sink, unchanged.
  TELEMETRY_WEBHOOK_URL: { key: "TELEMETRY_WEBHOOK_URL", required: false, secret: true },
} as const satisfies Record<string, EnvVarSpec>;

export type EnvVarName = keyof typeof ENV_VARS;

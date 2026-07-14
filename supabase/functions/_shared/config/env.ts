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

export const ENV_VARS = {
  ENVIRONMENT: { key: "FOOFOO_ENV", required: false, secret: false },
  LOG_LEVEL: { key: "LOG_LEVEL", required: false, secret: false },
  SUPABASE_URL: { key: "SUPABASE_URL", required: true, secret: false },
  SUPABASE_ANON_KEY: { key: "SUPABASE_ANON_KEY", required: true, secret: false },
  SUPABASE_SERVICE_ROLE_KEY: { key: "SUPABASE_SERVICE_ROLE_KEY", required: true, secret: true },
  SUPABASE_DB_URL: { key: "SUPABASE_DB_URL", required: false, secret: true },
  OPENWEATHERMAP_API_KEY: { key: "OPENWEATHERMAP_API_KEY", required: false, secret: true },
  ONESIGNAL_REST_API_KEY: { key: "ONESIGNAL_REST_API_KEY", required: false, secret: true },
  CLOUDINARY_CLOUD_NAME: { key: "CLOUDINARY_CLOUD_NAME", required: false, secret: false },
} as const satisfies Record<string, EnvVarSpec>;

export type EnvVarName = keyof typeof ENV_VARS;

/**
 * Typed configuration loader (WP-8B foundation).
 *
 * Reads and validates environment configuration once at cold start, fails fast on missing
 * required secrets, and exposes a frozen, typed `AppConfig`. This is the ONLY place that reads
 * process environment (DOC-P3-08 §Env-Vars; DOC-P3-07 §14). No secret value is ever logged.
 */
import { ENV_VARS } from "./env.ts";

export type Environment = "local" | "staging" | "production";

export interface AppConfig {
  readonly environment: Environment;
  readonly logLevel: "debug" | "info" | "warn" | "error";
  readonly supabaseUrl: string;
  readonly supabaseAnonKey: string;
  readonly supabaseServiceRoleKey: string;
  readonly supabaseDbUrl: string | null;
  readonly isProduction: boolean;
  /** Ghar RE service base URL (Phase C). Defaults to localhost for dev; no deployment yet (Phase F). */
  readonly gharReServiceUrl: string;
  /** Shared HMAC secret for the service-to-service call (RE-DOC-10 §9). */
  readonly gharReServiceSecret: string;
}

/** Dev-only defaults for the Ghar RE service. NEVER used in staging/production (guarded below). */
const GHAR_RE_DEV_URL = "http://localhost:8000";
const GHAR_RE_DEV_SECRET = "dev-insecure-ghar-re-secret";

/** Read a single env var by spec, enforcing the "required" contract. */
function read(spec: { key: string; required: boolean }): string | null {
  const value = Deno.env.get(spec.key) ?? null;
  if (spec.required && (value === null || value === "")) {
    // Never include the value (there is none) — only the key name is safe to surface.
    throw new Error(`[config] Missing required environment variable: ${spec.key}`);
  }
  return value;
}

function normalizeEnv(raw: string | null): Environment {
  switch ((raw ?? "local").toLowerCase()) {
    case "production":
    case "prod":
    case "foofoo-mvp":
      return "production";
    case "staging":
    case "foofoo-staging":
      return "staging";
    default:
      return "local";
  }
}

/**
 * Load and validate configuration. Call once per cold start; cache the result.
 * @throws Error if a required variable is missing (fail-fast, before serving traffic).
 */
export function loadConfig(): AppConfig {
  const environment = normalizeEnv(read(ENV_VARS.ENVIRONMENT));
  const level = (read(ENV_VARS.LOG_LEVEL) ?? "info").toLowerCase();
  const logLevel =
    (["debug", "info", "warn", "error"].includes(level) ? level : "info") as AppConfig["logLevel"];

  const isProduction = environment === "production";

  // Ghar RE service wiring. In PRODUCTION the URL + secret MUST be provided (fail fast — never ship
  // the insecure dev default to prod, DOC-P3-07 §14). local/staging may fall back to dev defaults;
  // staging enforcement can tighten once secrets are wired in Phase F (deployment). [TODO Phase F]
  const gharReServiceUrl = read(ENV_VARS.GHAR_RE_SERVICE_URL);
  const gharReServiceSecret = read(ENV_VARS.GHAR_RE_SERVICE_SECRET);
  if (isProduction && (!gharReServiceUrl || !gharReServiceSecret)) {
    throw new Error(
      "[config] GHAR_RE_SERVICE_URL and GHAR_RE_SERVICE_SECRET are required in production.",
    );
  }

  return Object.freeze({
    environment,
    logLevel,
    supabaseUrl: read(ENV_VARS.SUPABASE_URL) as string,
    supabaseAnonKey: read(ENV_VARS.SUPABASE_ANON_KEY) as string,
    supabaseServiceRoleKey: read(ENV_VARS.SUPABASE_SERVICE_ROLE_KEY) as string,
    supabaseDbUrl: read(ENV_VARS.SUPABASE_DB_URL),
    isProduction,
    gharReServiceUrl: gharReServiceUrl ?? GHAR_RE_DEV_URL,
    gharReServiceSecret: gharReServiceSecret ?? GHAR_RE_DEV_SECRET,
  });
}

let cached: AppConfig | null = null;

/** Cold-start-cached config accessor. */
export function getConfig(): AppConfig {
  if (cached === null) cached = loadConfig();
  return cached;
}

/** Test-only: reset the cached config so a test can re-load with different env. */
export function resetConfigCacheForTests(): void {
  cached = null;
}

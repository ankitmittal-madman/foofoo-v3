/**
 * Typed configuration loader (WP-8B foundation).
 *
 * Reads and validates environment configuration once at cold start, fails fast on missing
 * required secrets, and exposes a frozen, typed `AppConfig`. This is the ONLY place that reads
 * process environment (DOC-P3-08 §Env-Vars; DOC-P3-07 §14). No secret value is ever logged.
 */
import { ENV_VARS } from "./env.ts";

export type Environment = "local" | "staging" | "production";
export type FoodOntologyReadMode = "legacy" | "shadow" | "service";
export type AuxReMode = "off" | "shadow" | "active";

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
  readonly auxReServiceUrl: string | null;
  readonly auxReServiceSecret: string | null;
  readonly auxReMode: AuxReMode;
  readonly foodOntologyServiceUrl: string | null;
  readonly foodOntologyServiceToken: string | null;
  readonly foodOntologyReadMode: FoodOntologyReadMode;
  readonly ontologyRedisRestUrl: string | null;
  readonly ontologyRedisRestToken: string | null;
  readonly ontologyCacheSeconds: number;
  /** Optional real alerting sink URL (P1-7). Null when unset -- telemetry falls back to log-only. */
  readonly telemetryWebhookUrl: string | null;
  readonly oneSignalRestApiKey: string | null;
  readonly oneSignalAppId: string | null;
  readonly openWeatherMapApiKey: string | null;
  /** Optional USDA FoodData Central key; external enrichment still uses keyless FoodOn if absent. */
  readonly usdaFoodDataApiKey: string | null;
  /** Optional Groq key. When absent, deterministic/external enrichment continues without AI. */
  readonly groqApiKey: string | null;
  readonly groqModel: string;
  readonly aiDailyRequestBudget: number;
  readonly aiDailyTokenBudget: number;
  readonly aiMinUsableConfidence: number;
  readonly aiDirectPublishConfidence: number;
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

function boundedNumber(raw: string | null, fallback: number, min: number, max: number): number {
  if (raw === null || raw.trim() === "") return fallback;
  const value = Number(raw);
  return Number.isFinite(value) ? Math.max(min, Math.min(max, value)) : fallback;
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
  const auxReServiceUrl = read(ENV_VARS.AUX_RE_SERVICE_URL);
  const auxReServiceSecret = read(ENV_VARS.AUX_RE_SERVICE_SECRET);
  const auxReModeRaw = (read(ENV_VARS.AUX_RE_MODE) ?? "off").toLowerCase();
  if (!(["off", "shadow", "active"] as string[]).includes(auxReModeRaw)) {
    throw new Error("[config] AUX_RE_MODE must be off, shadow, or active.");
  }
  const auxReMode = auxReModeRaw as AuxReMode;
  if (auxReMode !== "off" && (!auxReServiceUrl || !auxReServiceSecret)) {
    throw new Error(
      "[config] AUX_RE_SERVICE_URL and AUX_RE_SERVICE_SECRET are required when AUX_RE_MODE is shadow or active.",
    );
  }

  const ontologyModeRaw = (read(ENV_VARS.FOOD_ONTOLOGY_READ_MODE) ?? "legacy").toLowerCase();
  if (!["legacy", "shadow", "service"].includes(ontologyModeRaw)) {
    throw new Error("[config] FOOD_ONTOLOGY_READ_MODE must be legacy, shadow, or service.");
  }
  const foodOntologyReadMode = ontologyModeRaw as FoodOntologyReadMode;
  const foodOntologyServiceUrl = read(ENV_VARS.FOOD_ONTOLOGY_SERVICE_URL);
  const foodOntologyServiceToken = read(ENV_VARS.FOOD_ONTOLOGY_SERVICE_TOKEN);
  const ontologyRedisRestUrl = read(ENV_VARS.ONTOLOGY_REDIS_REST_URL);
  const ontologyRedisRestToken = read(ENV_VARS.ONTOLOGY_REDIS_REST_TOKEN);
  if (foodOntologyReadMode !== "legacy" && (!foodOntologyServiceUrl || !foodOntologyServiceToken)) {
    throw new Error(
      "[config] FOOD_ONTOLOGY_SERVICE_URL and FOOD_ONTOLOGY_SERVICE_TOKEN are required outside legacy mode.",
    );
  }
  if (
    isProduction && foodOntologyReadMode === "service" &&
    (!ontologyRedisRestUrl || !ontologyRedisRestToken)
  ) {
    throw new Error(
      "[config] ONTOLOGY_REDIS_REST_URL and ONTOLOGY_REDIS_REST_TOKEN are required for production service mode.",
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
    auxReServiceUrl,
    auxReServiceSecret,
    auxReMode,
    foodOntologyServiceUrl,
    foodOntologyServiceToken,
    foodOntologyReadMode,
    ontologyRedisRestUrl,
    ontologyRedisRestToken,
    ontologyCacheSeconds: boundedNumber(read(ENV_VARS.ONTOLOGY_CACHE_SECONDS), 300, 1, 3600),
    telemetryWebhookUrl: read(ENV_VARS.TELEMETRY_WEBHOOK_URL),
    oneSignalRestApiKey: read(ENV_VARS.ONESIGNAL_REST_API_KEY),
    oneSignalAppId: read(ENV_VARS.ONESIGNAL_APP_ID),
    openWeatherMapApiKey: read(ENV_VARS.OPENWEATHERMAP_API_KEY),
    usdaFoodDataApiKey: read(ENV_VARS.USDA_FOODDATA_API_KEY),
    groqApiKey: read(ENV_VARS.GROQ_API_KEY),
    groqModel: read(ENV_VARS.GROQ_MODEL) ?? "openai/gpt-oss-120b",
    aiDailyRequestBudget: boundedNumber(
      read(ENV_VARS.AI_FREE_DAILY_REQUEST_BUDGET),
      800,
      1,
      10_000,
    ),
    aiDailyTokenBudget: boundedNumber(
      read(ENV_VARS.AI_FREE_DAILY_TOKEN_BUDGET),
      160_000,
      1_000,
      10_000_000,
    ),
    aiMinUsableConfidence: boundedNumber(
      read(ENV_VARS.AI_MIN_USABLE_CONFIDENCE),
      0.65,
      0.5,
      1,
    ),
    aiDirectPublishConfidence: boundedNumber(
      read(ENV_VARS.AI_DIRECT_PUBLISH_CONFIDENCE),
      0.8,
      0.5,
      1,
    ),
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

/** Optional, fail-open shadow client that retrieves canonical candidates before Ghar ranking. */
import type { AppConfig } from "../_shared/config/config.ts";
import type { Logger } from "../_shared/logging/logger.ts";
import { type FetchLike, hmacHex } from "./re-client.ts";

export const AUX_TIMEOUT_MS = 800;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export type AuxResult =
  | { ok: true; candidateIds: string[]; publicationVersion: string; latencyMs: number }
  | {
    ok: false;
    reason: "disabled" | "timeout" | "network" | "http" | "bad_body";
    latencyMs: number;
  };

export interface AuxShadowObservation {
  mode: "shadow" | "active";
  outcome: "retrieved" | "unavailable";
  failure_reason?: "timeout" | "network" | "http" | "bad_body";
  publication_version?: string;
  candidate_count: number;
  aux_latency_ms: number;
  comparable_served_count: number;
  served_in_candidates_count: number;
  served_candidate_coverage: number | null;
}

export interface ProductionGuardrailObservation {
  schema_version: "recommendation-serving-guardrail-observation-v1";
  measurement_status: "measured" | "unavailable";
  mode: "shadow" | "active";
  publication_version: string;
  served_dish_count: number;
  hard_constraint_violations: number;
  catalogue_version_mismatches: number;
  canonical_identity_failures: number;
  intended_date_integrity_failures: number;
  ghar_fallback_failures: number;
}

function strings(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

function dayType(date: unknown): "weekday" | "weekend" | undefined {
  if (typeof date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(date)) return undefined;
  const day = new Date(`${date}T12:00:00Z`).getUTCDay();
  return day === 0 || day === 6 ? "weekend" : "weekday";
}

function canonicalServedIds(body: Record<string, unknown>): string[] {
  const ids: string[] = [];
  const visit = (value: unknown): void => {
    if (Array.isArray(value)) {
      value.forEach(visit);
      return;
    }
    if (!value || typeof value !== "object") return;
    const item = value as Record<string, unknown>;
    if (typeof item.dish_id === "string" && UUID.test(item.dish_id)) ids.push(item.dish_id);
    if (Array.isArray(item.hero_dish_ids)) {
      ids.push(...item.hero_dish_ids.filter(
        (id): id is string => typeof id === "string" && UUID.test(id),
      ));
    }
    for (const [key, nested] of Object.entries(item)) {
      if (key !== "dish_id" && key !== "hero_dish_ids") visit(nested);
    }
  };
  visit(body.plates);
  visit(body.episodes);
  return [...new Set(ids)];
}

/** Build privacy-minimized shadow evidence: counts and ratios only, never candidate/user data. */
export function buildAuxShadowObservation(
  result: AuxResult,
  mode: AppConfig["auxReMode"],
  gharBody: Record<string, unknown>,
): AuxShadowObservation | undefined {
  if (mode === "off") return undefined;
  const servedIds = canonicalServedIds(gharBody);
  if (!result.ok) {
    if (result.reason === "disabled") return undefined;
    return {
      mode,
      outcome: "unavailable",
      failure_reason: result.reason,
      candidate_count: 0,
      aux_latency_ms: result.latencyMs,
      comparable_served_count: servedIds.length,
      served_in_candidates_count: 0,
      served_candidate_coverage: null,
    };
  }
  const candidates = new Set(result.candidateIds);
  const overlap = servedIds.filter((id) => candidates.has(id)).length;
  return {
    mode,
    outcome: "retrieved",
    publication_version: result.publicationVersion,
    candidate_count: result.candidateIds.length,
    aux_latency_ms: result.latencyMs,
    comparable_served_count: servedIds.length,
    served_in_candidates_count: overlap,
    served_candidate_coverage: servedIds.length ? overlap / servedIds.length : null,
  };
}

/**
 * Convert Ghar's independent final-response audit into privacy-safe rollout counters.
 *
 * Shadow mode intentionally does not claim to validate published-candidate identity because its
 * candidates do not affect the user-visible Ghar request. The offline publication gate covers
 * that identity path before canary; active mode then requires Ghar to hydrate the exact Aux
 * publication and treats any fallback as a hard failure. Missing/malformed Ghar audit evidence is
 * retained as `unavailable`, never converted to zero by the aggregate producer.
 */
export function buildProductionGuardrailObservation(
  aux: AuxResult,
  mode: AppConfig["auxReMode"],
  gharBody: Record<string, unknown> | undefined,
  requestedIntendedDate: unknown,
): ProductionGuardrailObservation | undefined {
  if (mode === "off" || !aux.ok) return undefined;
  const body = gharBody ?? {};
  const audit = record(body.guardrail_audit);
  const selection = record(body.catalogue_selection);
  const nonnegativeInteger = (value: unknown): value is number =>
    typeof value === "number" && Number.isInteger(value) && value >= 0;
  const measured = audit.schema_version === "ghar-final-guardrail-audit-v1" &&
    audit.measurement_status === "measured" &&
    nonnegativeInteger(audit.served_dish_count) &&
    nonnegativeInteger(audit.hard_constraint_violations) &&
    nonnegativeInteger(audit.canonical_identity_failures);
  const active = mode === "active";
  const publicationMatches = selection.source === "published_candidates" &&
    selection.publication_version === aux.publicationVersion;
  const expectedDate = typeof requestedIntendedDate === "string" ? requestedIntendedDate : null;
  const observedDate = typeof audit.intended_meal_date === "string"
    ? audit.intended_meal_date
    : null;
  return {
    schema_version: "recommendation-serving-guardrail-observation-v1",
    measurement_status: measured ? "measured" : "unavailable",
    mode,
    publication_version: aux.publicationVersion,
    served_dish_count: measured ? Number(audit.served_dish_count) : 0,
    hard_constraint_violations: measured ? Number(audit.hard_constraint_violations) : 0,
    catalogue_version_mismatches: active && !publicationMatches ? 1 : 0,
    canonical_identity_failures: active && measured ? Number(audit.canonical_identity_failures) : 0,
    intended_date_integrity_failures: expectedDate !== observedDate ? 1 : 0,
    ghar_fallback_failures: active && !publicationMatches ? 1 : 0,
  };
}

export function buildAuxiliaryRequest(
  gharPayload: Record<string, unknown>,
  userId: string,
  householdId: string,
): Record<string, unknown> {
  const household = record(gharPayload.household);
  const context = record(gharPayload.context);
  const dishPreference = record(gharPayload.preference_by_dish);
  const preferences = Object.entries(dishPreference)
    .filter(([, score]) => typeof score === "number" && score > 0)
    .sort((left, right) => Number(right[1]) - Number(left[1]))
    .slice(0, 50)
    .map(([key]) => key);
  const restrictions: string[] = [];
  if (typeof household.q5_diet === "string") restrictions.push(household.q5_diet);
  if (household.q8_is_jain === true) restrictions.push("jain");
  const mealSlot = typeof context.slot === "string"
    ? context.slot
    : typeof gharPayload.slot === "string"
    ? gharPayload.slot
    : "dinner";
  return {
    user_id: userId,
    household_id: householdId,
    meal_slot: mealSlot,
    region: typeof household.q3_home_state === "string" ? household.q3_home_state : undefined,
    preferences,
    restrictions,
    allergies: strings(household.q9_allergies),
    pantry_items: strings(context.pantry_ingredient_names),
    leftover_items: strings(context.leftover_dish_names),
    recent_meals: strings(gharPayload.exclude_dish_names),
    governed_context_signals: Array.isArray(context.governed_context_signals)
      ? context.governed_context_signals
      : [],
    preference_by_class: record(gharPayload.preference_by_class),
    preference_by_direct_class: record(gharPayload.preference_by_direct_class),
    preference_by_projected_class: record(gharPayload.preference_by_projected_class),
    plan_date: typeof context.date === "string" ? context.date : undefined,
    day_type: dayType(context.date),
    available_cook_minutes: typeof context.time_budget_minutes === "number"
      ? context.time_budget_minutes
      : undefined,
    candidate_limit: 100,
    existing_result: {
      items: [],
      metrics: {
        quality_score: 0,
        confidence: 0,
        diversity_score: 0,
        safety_score: 1,
        alignment_score: 0,
      },
    },
    candidates: [],
  };
}

export async function callAuxiliaryEngine(
  payload: Record<string, unknown>,
  requestId: string,
  cfg: AppConfig,
  logger: Logger,
  fetchImpl: FetchLike = globalThis.fetch as FetchLike,
  now: () => number = Date.now,
): Promise<AuxResult> {
  if (cfg.auxReMode === "off" || !cfg.auxReServiceUrl || !cfg.auxReServiceSecret) {
    return { ok: false, reason: "disabled", latencyMs: 0 };
  }
  const body = JSON.stringify(payload);
  const timestamp = Math.floor(now() / 1000);
  const signature = await hmacHex(cfg.auxReServiceSecret, `${timestamp}.${body}`);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), AUX_TIMEOUT_MS);
  const started = performance.now();
  try {
    const response = await fetchImpl(
      `${cfg.auxReServiceUrl.replace(/\/$/, "")}/v1/recommendations`,
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-request-id": requestId,
          "x-aux-signature": `t=${timestamp},v1=${signature}`,
        },
        body,
        signal: controller.signal,
      },
    );
    const latencyMs = Math.round(performance.now() - started);
    if (!response.ok) return { ok: false, reason: "http", latencyMs };
    let result: Record<string, unknown>;
    try {
      result = await response.json() as Record<string, unknown>;
    } catch {
      return { ok: false, reason: "bad_body", latencyMs };
    }
    const metadata = record(record(result.model_metadata).catalogue_publication);
    const version = metadata.version;
    const items = record(result.auxiliary_result).items;
    if (
      typeof version !== "string" || !/^sha256:[0-9a-f]{64}$/.test(version) ||
      !Array.isArray(items)
    ) return { ok: false, reason: "bad_body", latencyMs };
    const candidateIds = [
      ...new Set(
        items.map((item) => record(item).id).filter(
          (id): id is string => typeof id === "string" && UUID.test(id),
        ),
      ),
    ].slice(0, 500);
    if (candidateIds.length === 0) return { ok: false, reason: "bad_body", latencyMs };
    return { ok: true, candidateIds, publicationVersion: version, latencyMs };
  } catch (error) {
    const latencyMs = Math.round(performance.now() - started);
    const reason = error instanceof Error && error.name === "AbortError" ? "timeout" : "network";
    logger.warn("aux_re.shadow_failed", { request_id: requestId, reason, latency_ms: latencyMs });
    return { ok: false, reason, latencyMs };
  } finally {
    clearTimeout(timer);
  }
}

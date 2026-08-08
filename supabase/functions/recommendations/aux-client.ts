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

/** Canonical meal-episode slate persistence. A meal-episode response is not served unless the
 * ordered exposure and its probabilities are durable, preserving replay and learning semantics. */
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";

interface EpisodePrediction {
  p_choose: number;
  p_execute: number;
  p_regret: number;
  p_success: number;
  model_version: string;
}

interface EpisodeResult {
  episode_hash: string;
  rank: number;
  source_plate_score: number;
  reasons?: string[];
  predictions: EpisodePrediction;
  intent_posterior?: Record<string, number>;
  practicality?: Record<string, unknown>;
  components?: Array<{ dish_id?: string | null }>;
  [key: string]: unknown;
}

export interface DishSlateItem {
  name: string;
  score: number;
  selectionPropensity?: number;
  slot?: string;
  mealClassCode?: string | null;
  reasons: string[];
  snapshot: Record<string, unknown>;
}

/** Normalize every dish-bearing planning response into one ordered learning slate.
 * Calibration uses a global rank while preserving each cell's own meal slot. */
export function extractDishSlateItems(
  surface: string,
  response: Record<string, unknown>,
): DishSlateItem[] {
  const located: Array<{ value: unknown; slot?: string }> = [];
  if (surface === "calibration") {
    const slots = response.slots && typeof response.slots === "object"
      ? response.slots as Record<string, unknown>
      : {};
    for (const [slot, values] of Object.entries(slots)) {
      if (Array.isArray(values)) {
        located.push(...values.map((value) => ({ value, slot })));
      }
    }
  } else if (surface === "recommendations") {
    const plates = Array.isArray(response.plates) ? response.plates : [];
    for (const value of plates) {
      if (!value || typeof value !== "object") continue;
      const plate = value as Record<string, unknown>;
      const names = Array.isArray(plate.hero_dish_names) ? plate.hero_dish_names : [];
      const score = typeof plate.plate_score === "number" ? plate.plate_score : Number.NaN;
      for (const name of names) {
        located.push({
          value: {
            ...plate,
            name,
            score,
            slot: typeof response.slot === "string" ? response.slot : undefined,
          },
        });
      }
    }
  } else {
    const values = surface === "cold_start" ? response.dishes : response.options;
    if (Array.isArray(values)) located.push(...values.map((value) => ({ value })));
  }

  return located.flatMap(({ value, slot }) => {
    if (!value || typeof value !== "object") return [];
    const dish = value as Record<string, unknown>;
    const name = typeof dish.name === "string" ? dish.name.trim() : "";
    const score = typeof dish.score === "number" ? dish.score : Number.NaN;
    if (!name || !Number.isFinite(score)) return [];
    const selectionPropensity = typeof dish.selection_propensity === "number" &&
        dish.selection_propensity > 0 && dish.selection_propensity <= 1
      ? dish.selection_propensity
      : undefined;
    const explanation = dish.explanation && typeof dish.explanation === "object"
      ? dish.explanation as Record<string, unknown>
      : {};
    const top = Array.isArray(explanation.top_contributors)
      ? explanation.top_contributors as Array<Record<string, unknown>>
      : [];
    const reasons = top.map((item) => item.module).filter(
      (item): item is string => typeof item === "string",
    );
    if (typeof dish.meal_class_name === "string") reasons.push(dish.meal_class_name);
    return [{
      name,
      score,
      selectionPropensity,
      slot: slot ?? (typeof dish.slot === "string" ? dish.slot : undefined),
      mealClassCode: typeof dish.meal_class_code === "string" ? dish.meal_class_code : null,
      reasons: [...new Set(reasons)],
      snapshot: dish,
    }];
  });
}

export function extractDishCandidateItems(
  surface: string,
  response: Record<string, unknown>,
): DishSlateItem[] {
  const privateCandidates = response._candidate_lineage;
  if (!Array.isArray(privateCandidates) || privateCandidates.length === 0) {
    return extractDishSlateItems(surface, response);
  }
  return extractDishSlateItems("meal_plan", { options: privateCandidates });
}

export async function buildDishLineageCandidates(
  surface: string,
  response: Record<string, unknown>,
): Promise<
  Array<{
    candidate_item_hash: string;
    episode_id: null;
    generator_codes: string[];
    generator_scores: Record<string, number | null>;
    reason_codes: string[];
    rank: number;
  }>
> {
  const candidates = await Promise.all(
    extractDishCandidateItems(surface, response).map(async (item, index) => ({
      candidate_item_hash: await snapshotHash({
        kind: "dish",
        surface,
        slot: item.slot ?? null,
        name: item.name.toLocaleLowerCase("en-IN"),
      }),
      episode_id: null,
      generator_codes: [surface, item.mealClassCode].filter(
        (value): value is string => typeof value === "string" && value.length > 0,
      ),
      generator_scores: {
        point_score: item.score,
        rerank_score: item.score,
        selection_propensity: item.selectionPropensity ?? null,
        shadow_preference_score: typeof item.snapshot.shadow_preference_score === "number"
          ? item.snapshot.shadow_preference_score
          : null,
      },
      reason_codes: item.reasons,
      rank: index + 1,
    })),
  );

  // A malformed/upstream duplicate must not make the normalized lineage RPC violate the
  // recommendation_candidates primary key after the exposure itself has already been stored.
  return [
    ...new Map(candidates.map((candidate) => [candidate.candidate_item_hash, candidate])).values(),
  ]
    .map((candidate, index) => ({ ...candidate, rank: index + 1 }));
}

export function stripPrivateCandidateLineage(
  response: Record<string, unknown>,
): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(response).filter(([key]) => key !== "_candidate_lineage"),
  );
}

/** Return the truthful displayed-item inclusion probability for one dish slate.
 * Direct recommendations fail closed when an older Ghar response lacks its randomized-policy
 * probability. Planning dish surfaces are deterministic conditional on their persisted request,
 * so each displayed winner has probability 1 and unselected candidates have no policy support. */
export function dishSlateSelectionPropensity(
  surface: string,
  item: DishSlateItem,
): number | null {
  if (item.selectionPropensity !== undefined) return item.selectionPropensity;
  return surface === "recommendations" ? null : 1;
}

function hex(bytes: ArrayBuffer): string {
  return [...new Uint8Array(bytes)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

export async function eligibleSetHash(episodeHashes: string[]): Promise<string> {
  const stable = [...episodeHashes].sort().join("|");
  return hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(stable)));
}

function stableJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (value && typeof value === "object") {
    const object = value as Record<string, unknown>;
    return `{${
      Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`)
        .join(",")
    }}`;
  }
  return JSON.stringify(value) ?? "null";
}

export async function snapshotHash(value: unknown): Promise<string> {
  return hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(stableJson(value))));
}

/** Persist the dish-card surfaces used by onboarding and the landing page with the same normalized
 * request/run/candidate lineage as meal episodes. This closes the learning blind spot where the
 * UI's primary surfaces emitted feedback_events but no slate or feature snapshot to attribute the
 * feedback to. No probabilities are invented: uncalibrated propensities and prediction columns
 * stay null. */
async function persistDishRecommendationSlate(
  ctx: RequestContext,
  input: {
    householdId: string;
    requestId: string;
    surface: "cold_start" | "calibration" | "meal_plan" | "class_dishes" | "recommendations";
    modelVersion: string;
    configVersion: string;
    catalogVersion?: string | null;
    policyCode: string;
    latencyMs: number;
    householdSnapshot: Record<string, unknown>;
    requestContext: Record<string, unknown>;
    response: Record<string, unknown>;
  },
): Promise<string | undefined> {
  const items = extractDishSlateItems(input.surface, input.response);
  if (!items.length) return undefined;
  const db = createServiceRoleClient(ctx.config);
  const hashed = await Promise.all(items.map(async (item) => ({
    ...item,
    itemHash: await snapshotHash({
      kind: "dish",
      surface: input.surface,
      slot: item.slot ?? null,
      name: item.name.toLocaleLowerCase("en-IN"),
    }),
  })));
  const candidates = await buildDishLineageCandidates(input.surface, input.response);
  const eligibleHash = await eligibleSetHash(
    candidates.map((candidate) => candidate.candidate_item_hash),
  );
  const householdHash = await snapshotHash(input.householdSnapshot);
  const context = { ...input.requestContext, surface: input.surface };
  const contextHash = await snapshotHash(context);

  const { data: slate, error: slateError } = await withTimeout(
    db.from("slates").upsert({
      request_id: input.requestId,
      household_id: input.householdId,
      surface: input.surface,
      policy_code: input.policyCode,
      model_version: input.modelVersion,
      config_version: input.configVersion,
      catalog_version: input.catalogVersion ?? null,
      eligible_set_hash: eligibleHash,
      household_snapshot_hash: householdHash,
      context_snapshot: context,
      intent_posterior: {},
    }, { onConflict: "household_id,request_id" }).select("id").single(),
    "plan.dishes.slate_upsert",
  );
  if (slateError || !slate) {
    throw new AppError(ERROR_CATALOGUE.INTERNAL, {
      detail: slateError?.message ?? "dish slate missing",
    });
  }

  const rows = hashed.map((item, index) => ({
    slate_id: slate.id,
    episode_id: null,
    episode_hash: item.itemHash,
    rank: index + 1,
    point_score: item.score,
    rerank_score: item.score,
    // Direct recommendations carry the exact epsilon-greedy design probability from Ghar. Other
    // dish surfaces are deterministic conditional on their persisted request snapshot, so their
    // displayed items have inclusion probability 1 (and no support for unselected alternatives).
    selection_propensity: dishSlateSelectionPropensity(input.surface, item),
    generator_codes: [input.surface, item.mealClassCode].filter(
      (value): value is string => typeof value === "string" && value.length > 0,
    ),
    reason_tags: item.reasons,
    predicted_choose: null,
    predicted_execute: null,
    predicted_regret: null,
    decision_trace: {
      dish_name: item.name,
      slot: item.slot ?? null,
      model_version: input.modelVersion,
      policy_code: input.policyCode,
      dish_snapshot: item.snapshot,
    },
  }));
  const { error: itemError } = await withTimeout(
    db.from("slate_items").upsert(rows, { onConflict: "slate_id,rank" }),
    "plan.dishes.items_upsert",
  );
  if (itemError) throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: itemError.message });

  const featureHash = await snapshotHash(candidates);
  const traceChecksum = await snapshotHash({
    request_id: input.requestId,
    eligible_set_hash: eligibleHash,
    household_snapshot_hash: householdHash,
    context_snapshot_hash: contextHash,
    feature_snapshot_hash: featureHash,
  });
  const { error: lineageError } = await withTimeout(
    db.rpc("record_episode_recommendation_lineage", {
      p_payload: {
        request_id: input.requestId,
        household_id: input.householdId,
        slate_id: slate.id,
        surface: input.surface,
        meal_slot_code: typeof input.requestContext.slot === "string"
          ? input.requestContext.slot
          : null,
        context,
        context_snapshot_hash: contextHash,
        household_snapshot_hash: householdHash,
        household_snapshot: input.householdSnapshot,
        feature_set_version: "dish-slate-online-v1",
        feature_snapshot_hash: featureHash,
        engine_version: input.modelVersion,
        model_version: input.modelVersion,
        config_version: input.configVersion,
        catalog_version: input.catalogVersion ?? null,
        policy_version: input.policyCode,
        latency_ms: input.latencyMs,
        trace_checksum: traceChecksum,
        candidates,
      },
    }),
    "plan.dishes.normalized_lineage",
  );
  if (lineageError) {
    throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: lineageError.message });
  }
  return slate.id as string;
}

type DishSlatePersistence = typeof persistDishRecommendationSlate;

/** Dish-card lineage is part of the feedback-capable response contract. Returning a dish slate
 * without this durable point-in-time record would let the UI accept feedback that can never be
 * attributed to what was served. Log the failure with bounded context and let the handler return
 * a retryable error instead of silently creating another learning blind spot. */
export async function recordDishRecommendationSlate(
  ctx: RequestContext,
  input: Parameters<DishSlatePersistence>[1],
  persist: DishSlatePersistence = persistDishRecommendationSlate,
): Promise<string | undefined> {
  try {
    return await persist(ctx, input);
  } catch (error) {
    ctx.logger.warn("plan.dishes.persist_failed", {
      request_id: input.requestId,
      household_id: input.householdId,
      surface: input.surface,
      detail: error instanceof Error ? error.message : String(error),
    });
    throw error;
  }
}

export async function recordMealEpisodeSlate(
  ctx: RequestContext,
  input: {
    householdId: string;
    requestId: string;
    slot?: string;
    weekday?: string;
    classCode?: string;
    modelVersion: string;
    configVersion: string;
    catalogVersion?: string | null;
    policyCode: string;
    latencyMs: number;
    eligibleEpisodeHashes: string[];
    householdSnapshot: Record<string, unknown>;
    requestContext: Record<string, unknown>;
    episodes: EpisodeResult[];
  },
): Promise<string> {
  const db = createServiceRoleClient(ctx.config);
  const eligibleHashes = input.eligibleEpisodeHashes.length
    ? input.eligibleEpisodeHashes
    : input.episodes.map((episode) => episode.episode_hash);
  const hash = await eligibleSetHash(eligibleHashes);
  const householdHash = await snapshotHash(input.householdSnapshot);
  const { data: slate, error: slateError } = await withTimeout(
    db.from("slates").upsert({
      request_id: input.requestId,
      household_id: input.householdId,
      surface: "today_meal_episode",
      policy_code: input.policyCode,
      model_version: input.modelVersion,
      config_version: input.configVersion,
      catalog_version: input.catalogVersion ?? null,
      eligible_set_hash: hash,
      household_snapshot_hash: householdHash,
      context_snapshot: {
        slot: input.slot ?? null,
        weekday: input.weekday ?? null,
        class_code: input.classCode ?? null,
      },
      intent_posterior: input.episodes[0]?.intent_posterior ?? {},
    }, { onConflict: "household_id,request_id" }).select("id").single(),
    "plan.episodes.slate_upsert",
  );
  if (slateError || !slate) {
    throw new AppError(ERROR_CATALOGUE.INTERNAL, {
      detail: slateError?.message ?? "slate missing",
    });
  }

  const dishIds = [
    ...new Set(
      input.episodes.flatMap((episode) =>
        (episode.components ?? []).map((component) => component.dish_id).filter(
          (value): value is string => typeof value === "string" && /^[0-9a-f-]{36}$/i.test(value),
        )
      ),
    ),
  ];
  const episodeByDish = new Map<string, string>();
  if (dishIds.length) {
    const { data: catalogEpisodes, error: episodeError } = await withTimeout(
      db.rpc("resolve_catalog_episode_ids", { p_dish_ids: dishIds }),
      "plan.episodes.resolve_catalog_ids",
    );
    if (episodeError) {
      throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: episodeError.message });
    }
    for (const row of catalogEpisodes ?? []) {
      episodeByDish.set(String(row.dish_id), String(row.episode_id));
    }
  }

  const rows = input.episodes.map((episode, index) => ({
    slate_id: slate.id,
    episode_hash: episode.episode_hash,
    episode_id: (episode.components ?? []).map((component) => component.dish_id)
      .map((dishId) => dishId ? episodeByDish.get(dishId) : undefined).find(Boolean) ?? null,
    rank: episode.rank || index + 1,
    point_score: episode.source_plate_score,
    rerank_score: episode.predictions.p_success,
    // The request seed makes replay deterministic, but it is not a calibrated policy probability.
    // Leave propensity unknown until the exploration policy exposes its true inclusion chance.
    selection_propensity: null,
    generator_codes: input.classCode ? ["finalized_class"] : ["safe_plate_pipeline"],
    reason_tags: episode.reasons ?? [],
    predicted_choose: episode.predictions.p_choose,
    predicted_execute: episode.predictions.p_execute,
    predicted_regret: episode.predictions.p_regret,
    decision_trace: {
      practicality: episode.practicality ?? {},
      model_version: episode.predictions.model_version,
      policy_code: input.policyCode,
      eligible_set_hash: hash,
      catalog_version: input.catalogVersion ?? null,
      config_version: input.configVersion,
      episode_snapshot: episode,
    },
  }));
  const { error: itemError } = await withTimeout(
    db.from("slate_items").upsert(rows, { onConflict: "slate_id,rank" }),
    "plan.episodes.items_upsert",
  );
  if (itemError) throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: itemError.message });

  const rowByHash = new Map(rows.map((row) => [row.episode_hash, row]));
  const lineageCandidates = [...new Set(eligibleHashes)].map((episodeHash) => {
    const row = rowByHash.get(episodeHash);
    return {
      candidate_item_hash: episodeHash,
      episode_id: row?.episode_id ?? null,
      generator_codes: row?.generator_codes ?? ["eligible_set"],
      generator_scores: row
        ? {
          point_score: row.point_score,
          rerank_score: row.rerank_score,
          predicted_choose: row.predicted_choose,
          predicted_execute: row.predicted_execute,
          predicted_regret: row.predicted_regret,
          selection_propensity: row.selection_propensity,
        }
        : {},
      reason_codes: row?.reason_tags ?? [],
      rank: row?.rank ?? null,
    };
  });
  const context = {
    ...input.requestContext,
    slot: input.slot ?? input.requestContext.slot ?? null,
    weekday: input.weekday ?? input.requestContext.weekday ?? null,
    class_code: input.classCode ?? null,
  };
  const contextHash = await snapshotHash(context);
  const featureHash = await snapshotHash(lineageCandidates);
  const traceChecksum = await snapshotHash({
    request_id: input.requestId,
    eligible_set_hash: hash,
    household_snapshot_hash: householdHash,
    context_snapshot_hash: contextHash,
    feature_snapshot_hash: featureHash,
  });
  const { error: lineageError } = await withTimeout(
    db.rpc("record_episode_recommendation_lineage", {
      p_payload: {
        request_id: input.requestId,
        household_id: input.householdId,
        slate_id: slate.id,
        surface: "today_meal_episode",
        meal_slot_code: input.slot ?? null,
        context,
        context_snapshot_hash: contextHash,
        household_snapshot_hash: householdHash,
        household_snapshot: input.householdSnapshot,
        feature_set_version: "episode-online-v1",
        feature_snapshot_hash: featureHash,
        engine_version: input.modelVersion,
        model_version: input.modelVersion,
        config_version: input.configVersion,
        catalog_version: input.catalogVersion ?? null,
        policy_version: input.policyCode,
        latency_ms: input.latencyMs,
        trace_checksum: traceChecksum,
        candidates: lineageCandidates,
      },
    }),
    "plan.episodes.normalized_lineage",
  );
  if (lineageError) {
    throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: lineageError.message });
  }
  return slate.id as string;
}

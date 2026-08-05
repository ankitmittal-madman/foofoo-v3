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
    // The current rule policy deterministically includes every returned episode. This is the
    // actual logging-policy probability, not a fabricated exploration propensity.
    selection_propensity: 1,
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

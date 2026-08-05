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
}

function hex(bytes: ArrayBuffer): string {
  return [...new Uint8Array(bytes)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

async function eligibleSetHash(episodes: EpisodeResult[]): Promise<string> {
  const stable = episodes.map((episode) => episode.episode_hash).sort().join("|");
  return hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(stable)));
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
    episodes: EpisodeResult[];
  },
): Promise<string> {
  const db = createServiceRoleClient(ctx.config);
  const hash = await eligibleSetHash(input.episodes);
  const { data: slate, error: slateError } = await withTimeout(
    db.from("slates").upsert({
      request_id: input.requestId,
      household_id: input.householdId,
      surface: "today_meal_episode",
      policy_code: "episode_success_rule_v1",
      model_version: input.modelVersion,
      config_version: input.modelVersion,
      eligible_set_hash: hash,
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
    },
  }));
  const { error: itemError } = await withTimeout(
    db.from("slate_items").upsert(rows, { onConflict: "slate_id,rank" }),
    "plan.episodes.items_upsert",
  );
  if (itemError) throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: itemError.message });
  return slate.id as string;
}

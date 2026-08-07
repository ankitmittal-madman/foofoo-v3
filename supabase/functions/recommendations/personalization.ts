/** Online recommendation state shared by every serving surface. */
import { createServiceRoleClient } from "../_shared/db/client.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";

export interface OnlineRecommendationState {
  interactionCount: number;
  excludeDishNames: string[];
  preferenceByDish: Record<string, number>;
  preferenceByClass: Record<string, number>;
  preferenceByTag: Record<string, number>;
  dishFeedbackCounts: Array<{ dish_name: string; served: number; rejected: number }>;
  /** Canonical names shown in recent successful slates. Used only for freshness/refresh
   * suppression; it is intentionally separate from durable Never/Not-Today intent. */
  recentExposureDishNames: string[];
  recentClassCounts: Record<string, number>;
  recentCuisineCounts: Record<string, number>;
  noveltyBudget: number;
  richnessDebt: number;
}

export function extractExposureDishNames(plates: unknown): string[] {
  if (!Array.isArray(plates)) return [];
  const names: string[] = [];
  for (const item of plates) {
    if (!item || typeof item !== "object") continue;
    const row = item as Record<string, unknown>;
    if (typeof row.name === "string") names.push(row.name);
    if (Array.isArray(row.hero_dish_names)) {
      for (const value of row.hero_dish_names) if (typeof value === "string") names.push(value);
    }
    if (Array.isArray(row.components)) {
      for (const component of row.components) {
        const name = component && typeof component === "object"
          ? (component as Record<string, unknown>).dish_name
          : null;
        if (typeof name === "string") names.push(name);
      }
    }
  }
  return names;
}

export function extractPersistedExposureDishNames(value: unknown): string[] {
  if (!value || typeof value !== "object") return [];
  const names = (value as Record<string, unknown>).recent_dish_names;
  if (!Array.isArray(names)) return [];
  return names.filter((name): name is string => typeof name === "string" && name.length > 0);
}

export function extractPersistedCadence(value: unknown): {
  noveltyBudget: number;
  richnessDebt: number;
} {
  const fallback = { noveltyBudget: 0.15, richnessDebt: 0 };
  if (!value || typeof value !== "object") return fallback;
  const cadence = (value as Record<string, unknown>).cadence;
  if (!cadence || typeof cadence !== "object") return fallback;
  const row = cadence as Record<string, unknown>;
  const novelty = typeof row.novelty_budget === "number" && Number.isFinite(row.novelty_budget)
    ? Math.max(0, Math.min(1, row.novelty_budget))
    : fallback.noveltyBudget;
  const richness = typeof row.richness_debt === "number" && Number.isFinite(row.richness_debt)
    ? Math.max(0, Math.min(1, row.richness_debt))
    : fallback.richnessDebt;
  return { noveltyBudget: novelty, richnessDebt: richness };
}

/** Read the materialized seven-day class/cuisine window used for cross-request diversity.
 * Values are bounded before they cross the service contract; duplicate rows keep the maximum
 * rather than being added (the RPC can evolve to expose overlapping windows). */
export function extractPersistedVarietyCounts(value: unknown): {
  recentClassCounts: Record<string, number>;
  recentCuisineCounts: Record<string, number>;
} {
  const result = {
    recentClassCounts: {} as Record<string, number>,
    recentCuisineCounts: {} as Record<string, number>,
  };
  if (!value || typeof value !== "object") return result;
  const dimensions = (value as Record<string, unknown>).dimensions;
  if (!Array.isArray(dimensions)) return result;
  for (const item of dimensions) {
    if (!item || typeof item !== "object") continue;
    const row = item as Record<string, unknown>;
    if (row.window_code !== "7d") continue;
    const key = typeof row.entity_key === "string" ? row.entity_key.trim() : "";
    const rawCount = row.count_in_window;
    if (!key || typeof rawCount !== "number" || !Number.isFinite(rawCount) || rawCount <= 0) {
      continue;
    }
    const count = Math.min(1_000, Math.trunc(rawCount));
    const target = row.dimension_code === "meal_class"
      ? result.recentClassCounts
      : row.dimension_code === "cuisine"
      ? result.recentCuisineCounts
      : null;
    if (target && (key in target || Object.keys(target).length < 100)) {
      target[key] = Math.max(target[key] ?? 0, count);
    }
  }
  return result;
}

/** Aggregate only explicit member affinities with Nash-style geometric welfare.
 * Members with no evidence for a dish are omitted; no demographic preference is invented. */
export function aggregateMemberAffinities(
  rows: Array<{ profile_id: string; dish_affinity: Record<string, number> | null }>,
): Record<string, number> {
  return aggregateAffinityMaps(rows.map((row) => row.dish_affinity));
}

/** Nash-style household aggregation for any sparse, explicitly-evidenced affinity map. */
export function aggregateAffinityMaps(
  maps: Array<Record<string, number> | null | undefined>,
): Record<string, number> {
  const byDish = new Map<string, number[]>();
  for (const affinities of maps) {
    for (const [dish, raw] of Object.entries(affinities ?? {})) {
      if (!Number.isFinite(raw)) continue;
      const affinity = Math.max(-1, Math.min(1, raw));
      byDish.set(dish, [...(byDish.get(dish) ?? []), affinity]);
    }
  }
  const aggregate: Record<string, number> = {};
  for (const [dish, affinities] of byDish) {
    const logWelfare = affinities.reduce(
      (total, affinity) => total + Math.log(Math.max(0.05, 1 + affinity)),
      0,
    ) / affinities.length;
    aggregate[dish] = Math.max(-1, Math.min(1, Math.exp(logWelfare) - 1));
  }
  return aggregate;
}

export async function loadOnlineRecommendationState(
  ctx: RequestContext,
  profileId: string,
): Promise<OnlineRecommendationState> {
  const db = createServiceRoleClient(ctx.config);
  try {
    const membershipRes = await withTimeout(
      db.from("household_memberships").select("user_id").eq("household_id", profileId)
        .eq("status", "active"),
      "personalization.memberships",
    );
    if (membershipRes.error) throw membershipRes.error;
    const memberIds = [...new Set((membershipRes.data ?? []).map((row) => String(row.user_id)))];
    if (memberIds.length === 0) memberIds.push(profileId);
    const [countRes, neverRes, todayRes, tasteRes, feedbackRes, varietyRes, exposureRes] =
      await Promise.all([
        withTimeout(
          db.from("feedback_events").select("id", { count: "exact", head: true })
            .eq("household_id", profileId).neq("event_type", "shown_not_tapped"),
          "personalization.count",
        ),
        withTimeout(
          db.from("never_list").select("dishes(name)").eq("profile_id", profileId)
            .eq("is_active", true),
          "personalization.never",
        ),
        withTimeout(
          db.from("not_today_suppression").select("dishes(name)").eq("profile_id", profileId)
            .eq("is_active", true).gt("effective_until", new Date().toISOString()),
          "personalization.not_today",
        ),
        withTimeout(
          db.from("user_taste_vectors").select(
            "profile_id,dish_affinity,class_affinity,tag_affinity",
          ).in(
            "profile_id",
            memberIds,
          ),
          "personalization.taste",
        ),
        withTimeout(
          db.from("feedback_events").select("event_type,created_at,detail,dishes(name)").eq(
            "household_id",
            profileId,
          )
            .order("created_at", { ascending: false }).limit(500),
          "personalization.feedback",
        ),
        withTimeout(
          db.rpc("get_recommendation_variety_state", { p_household_id: profileId }),
          "personalization.variety_state",
        ),
        withTimeout(
          db.from("recommendation_events").select("plates").eq("household_id", profileId)
            .in("outcome", ["success", "partial"]).order("created_at", { ascending: false })
            .limit(6),
          "personalization.recent_exposures",
        ),
      ]);
    for (const result of [countRes, neverRes, todayRes, tasteRes, feedbackRes, exposureRes]) {
      if (result.error) throw result.error;
    }
    if (varietyRes.error) {
      ctx.logger.warn("personalization.variety_state_unavailable", {
        profile_id: profileId,
        detail: varietyRes.error.message,
      });
    }
    const cadence = extractPersistedCadence(varietyRes.data);
    const variety = extractPersistedVarietyCounts(varietyRes.data);
    const joinedName = (row: Record<string, unknown>): string | null => {
      const joined = row.dishes as { name?: unknown } | Array<{ name?: unknown }> | null;
      const name = Array.isArray(joined) ? joined[0]?.name : joined?.name;
      return typeof name === "string" ? name : null;
    };
    const excluded = new Set<string>();
    for (
      const row of [...(neverRes.data ?? []), ...(todayRes.data ?? [])] as Record<string, unknown>[]
    ) {
      const name = joinedName(row);
      if (name) excluded.add(name);
    }
    const counts = new Map<string, { served: number; rejected: number }>();
    for (const row of (feedbackRes.data ?? []) as Record<string, unknown>[]) {
      const detail = row.detail && typeof row.detail === "object"
        ? row.detail as Record<string, unknown>
        : null;
      const fallbackName = typeof detail?.dish_name === "string" ? detail.dish_name : null;
      const name = joinedName(row) ?? fallbackName;
      if (!name) continue;
      const eventType = String(row.event_type);
      if (eventType === "never") excluded.add(name);
      if (eventType === "not_today") {
        const occurred = new Date(String(row.created_at));
        if (
          Number.isFinite(occurred.getTime()) &&
          Date.now() - occurred.getTime() < 24 * 60 * 60 * 1000
        ) {
          excluded.add(name);
        }
      }
      const current = counts.get(name) ?? { served: 0, rejected: 0 };
      if (["accept", "like", "make_this", "cooked", "completed"].includes(eventType)) {
        current.served++;
      }
      if (["dislike", "never", "not_today", "shown_not_tapped"].includes(eventType)) {
        current.rejected++;
      }
      counts.set(name, current);
    }
    return {
      interactionCount: countRes.count ?? 0,
      // Durable/intentional suppression stays separate from recent exposure. The plan handler
      // combines the latter only for an unlocked/refreshable surface; otherwise a locked slot
      // could silently change merely because its previous slate was recorded successfully.
      excludeDishNames: [...excluded].slice(0, 50),
      preferenceByDish: aggregateMemberAffinities(
        (tasteRes.data ?? []) as Array<{
          profile_id: string;
          dish_affinity: Record<string, number> | null;
        }>,
      ),
      preferenceByClass: aggregateAffinityMaps(
        (tasteRes.data ?? []).map((row) =>
          (row as { class_affinity?: Record<string, number> | null }).class_affinity
        ),
      ),
      preferenceByTag: aggregateAffinityMaps(
        (tasteRes.data ?? []).map((row) =>
          (row as { tag_affinity?: Record<string, number> | null }).tag_affinity
        ),
      ),
      dishFeedbackCounts: [...counts].map(([name, value]) => ({ dish_name: name, ...value })),
      recentExposureDishNames: (() => {
        const persisted = extractPersistedExposureDishNames(varietyRes.data);
        const eventFallback = (exposureRes.data ?? []).flatMap((row) =>
          extractExposureDishNames(row.plates)
        );
        return [...new Set(persisted.length > 0 ? persisted : eventFallback)].slice(0, 50);
      })(),
      ...variety,
      ...cadence,
    };
  } catch (error) {
    ctx.logger.warn("personalization.load_failed", {
      profile_id: profileId,
      detail: error instanceof Error ? error.message : String(error),
    });
    return {
      interactionCount: 0,
      excludeDishNames: [],
      preferenceByDish: {},
      preferenceByClass: {},
      preferenceByTag: {},
      dishFeedbackCounts: [],
      recentExposureDishNames: [],
      recentClassCounts: {},
      recentCuisineCounts: {},
      noveltyBudget: 0.15,
      richnessDebt: 0,
    };
  }
}

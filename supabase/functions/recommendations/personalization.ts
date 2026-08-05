/** Online recommendation state shared by every serving surface. */
import { createServiceRoleClient } from "../_shared/db/client.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";

export interface OnlineRecommendationState {
  interactionCount: number;
  excludeDishNames: string[];
  preferenceByDish: Record<string, number>;
  dishFeedbackCounts: Array<{ dish_name: string; served: number; rejected: number }>;
}

/** Aggregate only explicit member affinities with Nash-style geometric welfare.
 * Members with no evidence for a dish are omitted; no demographic preference is invented. */
export function aggregateMemberAffinities(
  rows: Array<{ profile_id: string; dish_affinity: Record<string, number> | null }>,
): Record<string, number> {
  const byDish = new Map<string, number[]>();
  for (const row of rows) {
    for (const [dish, raw] of Object.entries(row.dish_affinity ?? {})) {
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
    const [countRes, neverRes, todayRes, tasteRes, feedbackRes] = await Promise.all([
      withTimeout(
        db.from("feedback_events").select("id", { count: "exact", head: true })
          .eq("household_id", profileId),
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
        db.from("user_taste_vectors").select("profile_id,dish_affinity").in(
          "profile_id",
          memberIds,
        ),
        "personalization.taste",
      ),
      withTimeout(
        db.from("feedback_events").select("event_type,dishes(name)").eq(
          "household_id",
          profileId,
        )
          .not("dish_id", "is", null).order("created_at", { ascending: false }).limit(500),
        "personalization.feedback",
      ),
    ]);
    for (const result of [countRes, neverRes, todayRes, tasteRes, feedbackRes]) {
      if (result.error) throw result.error;
    }
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
      const name = joinedName(row);
      if (!name) continue;
      const current = counts.get(name) ?? { served: 0, rejected: 0 };
      if (["accept", "like"].includes(String(row.event_type))) current.served++;
      if (["dislike", "never", "not_today", "shown_not_tapped"].includes(String(row.event_type))) {
        current.rejected++;
      }
      counts.set(name, current);
    }
    return {
      interactionCount: countRes.count ?? 0,
      excludeDishNames: [...excluded],
      preferenceByDish: aggregateMemberAffinities(
        (tasteRes.data ?? []) as Array<{
          profile_id: string;
          dish_affinity: Record<string, number> | null;
        }>,
      ),
      dishFeedbackCounts: [...counts].map(([name, value]) => ({ dish_name: name, ...value })),
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
      dishFeedbackCounts: [],
    };
  }
}

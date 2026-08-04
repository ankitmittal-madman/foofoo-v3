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

export async function loadOnlineRecommendationState(
  ctx: RequestContext,
  profileId: string,
): Promise<OnlineRecommendationState> {
  const db = createServiceRoleClient(ctx.config);
  try {
    const [countRes, neverRes, todayRes, tasteRes, feedbackRes] = await Promise.all([
      withTimeout(
        db.from("feedback_events").select("id", { count: "exact", head: true })
          .eq("profile_id", profileId),
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
        db.from("user_taste_vectors").select("dish_affinity").eq("profile_id", profileId)
          .maybeSingle(),
        "personalization.taste",
      ),
      withTimeout(
        db.from("feedback_events").select("event_type,dishes(name)").eq("profile_id", profileId)
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
      preferenceByDish: (tasteRes.data?.dish_affinity ?? {}) as Record<string, number>,
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

/** Consent-aware first-party product analytics and deterministic experiment assignment. */
import { createServiceRoleClient } from "../db/client.ts";
import type { RequestContext } from "../types/context.ts";
import { withTimeout } from "../utils/timeout.ts";

function bucket(profileId: string, experimentKey: string): number {
  let hash = 2166136261;
  for (const char of `${profileId}:${experimentKey}`) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) % 10000;
}

export async function activeAssignments(
  ctx: RequestContext,
  profileId: string,
): Promise<Record<string, string>> {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await withTimeout(
    db.from("experiments").select("experiment_key,variants,allocation_pct").eq("is_active", true),
    "analytics.assignments",
  );
  if (error) throw error;
  const assignments: Record<string, string> = {};
  for (const row of data ?? []) {
    const variants = row.variants as string[];
    const value = bucket(profileId, row.experiment_key as string);
    if (value >= Number(row.allocation_pct) * 100 || variants.length === 0) continue;
    assignments[row.experiment_key as string] = variants[value % variants.length];
  }
  return assignments;
}

export async function recordProductEvent(
  ctx: RequestContext,
  input: {
    /** Authenticated person whose analytics consent governs this event. */
    profileId: string;
    /** Household tenant the product action affected; may differ for a shared-household member. */
    householdId: string;
    eventName: string;
    requestId?: string;
    dishId?: string | null;
    properties?: Record<string, unknown>;
  },
): Promise<void> {
  try {
    const db = createServiceRoleClient(ctx.config);
    const { data: consent } = await withTimeout(
      db.from("consent_records").select("granted").eq("profile_id", input.profileId)
        .eq("consent_type", "analytics").order("granted_at", { ascending: false }).limit(1)
        .maybeSingle(),
      "analytics.consent",
    );
    // Operational recommendation/feedback rows remain canonical regardless of analytics consent;
    // this additional behavioral analytics stream is opt-in only.
    if (!consent?.granted) return;
    const assignments = await activeAssignments(ctx, input.profileId);
    const { error } = await withTimeout(
      db.from("product_events").insert({
        profile_id: input.profileId,
        household_id: input.householdId,
        event_name: input.eventName,
        request_id: input.requestId ?? null,
        dish_id: input.dishId ?? null,
        properties: input.properties ?? {},
        experiment_assignments: assignments,
      }),
      "analytics.record",
    );
    if (error) throw error;
  } catch (error) {
    ctx.logger.warn("analytics.record_failed", {
      event_name: input.eventName,
      detail: error instanceof Error ? error.message : String(error),
    });
  }
}

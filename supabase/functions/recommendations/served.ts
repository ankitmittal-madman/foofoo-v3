/**
 * shown_not_tapped emission helpers (§0.1 of the RE plumbing plan).
 *
 * Mirrors feedback/events.ts's dish-name -> public.dishes.id resolution: public.dishes and the
 * RE's own catalogue are two separately-synced data sources, so a miss is expected (dish_id left
 * null, logged), never an error — the same discipline that file's module doc already states. This
 * module BATCHES the lookup (one `IN` query for every hero dish name served across every plate in
 * a request) instead of one query per dish, since recordRecommendationEvent may need to resolve
 * many names at once, unlike feedback/events.ts's single-dish-per-call shape.
 */
import type { SupabaseClient } from "../_shared/db/client.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";

/** One served dish, as flattened out of any supported recommendation response shape. */
export interface ServedDish {
  dishName: string;
  mealClassCode?: string;
  cuisineFamily?: string;
  heaviness?: number;
  totalMins?: number;
  richnessScore?: number;
}

function boundedNumber(value: unknown, minimum: number, maximum?: number): number | undefined {
  if (typeof value !== "number" || !Number.isFinite(value) || value < minimum) return undefined;
  if (maximum !== undefined && value > maximum) return undefined;
  return value;
}

function text(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  const normalized = value.trim();
  return normalized || undefined;
}

/**
 * Resolve a batch of dish names to public.dishes.id in one query. Names with no matching row are
 * simply absent from the returned map (never an error) — same miss-is-expected discipline as
 * feedback/events.ts's single-name lookup.
 * @param ctx - request context (used only for logging a lookup failure)
 * @param db - service-role client (caller already created it; this module has no data-ownership
 *   surface of its own — RE-DOC-10 §1 keeps DB construction at the compose/events call sites)
 * @param names - deduplicated-by-caller-or-not dish names to resolve; duplicates cost nothing extra
 * @returns map of dish name -> public.dishes.id, containing only names that actually resolved
 */
export async function resolveDishIdsByName(
  ctx: RequestContext,
  db: SupabaseClient,
  names: string[],
): Promise<Map<string, string>> {
  const unique = Array.from(new Set(names));
  const resolved = new Map<string, string>();
  if (unique.length === 0) return resolved;

  const { data, error } = await withTimeout(
    db.from("dishes").select("id, name").in("name", unique),
    "recommendations.served.resolveDishIdsByName",
  );
  if (error) {
    // A resolution failure must not block the recommendation_events write it accompanies — log
    // and return an empty map, same "don't lose the primary write over a secondary lookup"
    // principle as feedback/events.ts's per-dish miss handling.
    ctx.logger.warn("shown_not_tapped.dish_lookup_failed", { detail: error.message });
    return resolved;
  }
  for (const row of (data ?? []) as Array<{ id: string; name: string }>) {
    resolved.set(row.name, row.id);
  }
  return resolved;
}

/** One row ready to insert into public.feedback_events for a served-but-not-yet-acted-on dish. */
export interface ShownNotTappedRow {
  profile_id: string;
  household_id: string;
  recommendation_event_id: string;
  dish_id: string | null;
  event_type: "shown_not_tapped";
  data_source: "real";
}

/**
 * Build one `shown_not_tapped` feedback_events row per served hero dish. Pure/no I/O, so it is
 * unit-testable independent of the DB — the resolver above is the only I/O boundary.
 * @param profileId - the household the recommendation was served to
 * @param recommendationEventId - the just-inserted recommendation_events row's id
 * @param served - every hero dish served this request (flattened across all plates — a "pair"
 *   plate contributes 2 rows, a "single"/"standalone" plate contributes 1)
 * @param dishIds - name -> uuid map from resolveDishIdsByName; a miss yields dish_id: null rather
 *   than dropping the row, so the shown-not-tapped signal is never silently lost over a catalogue
 *   sync gap
 */
export function buildShownNotTappedRows(
  profileId: string,
  recommendationEventId: string,
  served: ServedDish[],
  dishIds: Map<string, string>,
): ShownNotTappedRow[] {
  return served.map((s) => ({
    profile_id: profileId,
    household_id: profileId,
    recommendation_event_id: recommendationEventId,
    dish_id: dishIds.get(s.dishName) ?? null,
    event_type: "shown_not_tapped" as const,
    data_source: "real" as const,
  }));
}

/**
 * Flatten every serving shape into one ServedDish per displayed dish:
 * - v1 RE plates expose `hero_dish_names[]`;
 * - plan/onboarding surfaces expose direct dish cards with `name`;
 * - episode surfaces expose `components[].dish_name`.
 *
 * Keeping these shapes together prevents a surface-specific telemetry blind spot: all displayed
 * dishes must contribute to the shown denominator used by feedback and preference evaluation.
 */
export function flattenServedDishes(plates: unknown): ServedDish[] {
  if (!Array.isArray(plates)) return [];
  const out: ServedDish[] = [];
  for (const p of plates) {
    if (!p || typeof p !== "object") continue;
    const row = p as Record<string, unknown>;
    const directName = text(row.name);
    if (directName) {
      out.push({
        dishName: directName,
        mealClassCode: text(row.meal_class_code),
        cuisineFamily: text(row.cuisine_family) ?? text(row.cuisine),
        heaviness: boundedNumber(row.heaviness, 0, 3),
        totalMins: boundedNumber(row.total_mins, 0),
        richnessScore: boundedNumber(row.richness_score, 0, 1),
      });
    }
    if (Array.isArray(row.hero_dish_names)) {
      for (const value of row.hero_dish_names) {
        const name = text(value);
        if (name) out.push({ dishName: name });
      }
    }
    if (Array.isArray(row.components)) {
      const practicality = row.practicality && typeof row.practicality === "object"
        ? row.practicality as Record<string, unknown>
        : {};
      for (const component of row.components) {
        if (!component || typeof component !== "object") continue;
        const item = component as Record<string, unknown>;
        const name = text(item.dish_name);
        if (name) {
          out.push({
            dishName: name,
            mealClassCode: text(item.meal_class_code),
            cuisineFamily: text(item.cuisine_family) ?? text(item.cuisine),
            totalMins: boundedNumber(practicality.active_minutes, 0),
            richnessScore: boundedNumber(row.richness_score, 0, 1),
          });
        }
      }
    }
  }
  return out;
}

/** RPC payload uses snake_case to match the database boundary. Undefined evidence is omitted. */
export function toExposureItems(served: ServedDish[]): Array<Record<string, string | number>> {
  return served.map((item) => ({
    dish_name: item.dishName,
    ...(item.mealClassCode ? { meal_class_code: item.mealClassCode } : {}),
    ...(item.cuisineFamily ? { cuisine_family: item.cuisineFamily } : {}),
    ...(item.heaviness !== undefined ? { heaviness: item.heaviness } : {}),
    ...(item.totalMins !== undefined ? { total_mins: item.totalMins } : {}),
    ...(item.richnessScore !== undefined ? { richness_score: item.richnessScore } : {}),
  }));
}

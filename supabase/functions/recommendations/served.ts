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
  richness?: string[];
  cookingMethod?: string[];
}

export interface ServedMealClass {
  classCode: string;
  mealSlot: "breakfast" | "lunch" | "dinner";
  intendedMealDate: string;
  dayType: "weekday" | "weekend";
  shownRank: number;
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

function textArray(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const values = value.map(text).filter((item): item is string => item !== undefined).slice(0, 20);
  return values.length ? values : undefined;
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
  schema_version: "1";
  target_type: "dish";
  target_id: string;
  target_identity_status: "resolved" | "unresolved";
  target_snapshot: { display_name: string };
  evidence_kind: "integration";
  source_surface: "recommendation_served";
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
  return served.map((s) => {
    const dishId = dishIds.get(s.dishName) ?? null;
    return {
      profile_id: profileId,
      household_id: profileId,
      recommendation_event_id: recommendationEventId,
      dish_id: dishId,
      event_type: "shown_not_tapped" as const,
      schema_version: "1" as const,
      target_type: "dish" as const,
      target_id: dishId ?? s.dishName,
      target_identity_status: dishId ? "resolved" as const : "unresolved" as const,
      target_snapshot: { display_name: s.dishName },
      evidence_kind: "integration" as const,
      source_surface: "recommendation_served" as const,
      data_source: "real" as const,
    };
  });
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
        richness: textArray(row.richness),
        cookingMethod: textArray(row.cooking_method),
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
            richness: textArray(item.richness),
            cookingMethod: textArray(item.cooking_method),
          });
        }
      }
    }
  }
  return out;
}

/** Extract dated weekly class impressions without treating them as selections or acceptance. */
export function flattenServedMealClasses(plates: unknown): ServedMealClass[] {
  if (!Array.isArray(plates)) return [];
  const out: ServedMealClass[] = [];
  for (const value of plates) {
    if (!value || typeof value !== "object") continue;
    const row = value as Record<string, unknown>;
    const classCode = text(row.class_code);
    const mealSlot = text(row.meal_slot);
    const intendedMealDate = text(row.intended_meal_date);
    const dayType = text(row.day_type);
    const shownRank = boundedNumber(row.shown_rank, 1, 100);
    if (
      classCode && (mealSlot === "breakfast" || mealSlot === "lunch" || mealSlot === "dinner") &&
      intendedMealDate && (dayType === "weekday" || dayType === "weekend") && shownRank
    ) {
      out.push({
        classCode,
        mealSlot,
        intendedMealDate,
        dayType,
        shownRank: Math.trunc(shownRank),
      });
    }
  }
  return out;
}

export function toMealClassExposureItems(
  served: ServedMealClass[],
): Array<Record<string, string | number>> {
  return served.map((item) => ({
    class_code: item.classCode,
    meal_slot: item.mealSlot,
    intended_meal_date: item.intendedMealDate,
    day_type: item.dayType,
    shown_rank: item.shownRank,
  }));
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

export interface ServedMealMoment {
  mealSlot: "breakfast" | "lunch" | "dinner";
  intendedMealDate: string;
  dayType: "weekday" | "weekend";
}

/** Add the requested meal moment to point-in-time dish attributes for temporal exposure replay. */
export function toMealAttributeExposureItems(
  served: ServedDish[],
  moment: ServedMealMoment,
): Array<Record<string, unknown>> {
  return served.map((item) => ({
    dish_name: item.dishName,
    meal_slot: moment.mealSlot,
    intended_meal_date: moment.intendedMealDate,
    day_type: moment.dayType,
    ...(item.cuisineFamily ? { cuisine: item.cuisineFamily } : {}),
    ...(item.richness ? { richness: item.richness } : {}),
    ...(item.cookingMethod ? { cooking_method: item.cookingMethod } : {}),
  }));
}

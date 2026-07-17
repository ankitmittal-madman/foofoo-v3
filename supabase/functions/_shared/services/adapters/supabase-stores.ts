/**
 * Concrete Supabase adapters — persistence + caller-load path (WP-8E).
 *
 * Repository layer ONLY (DOC-P4-00 §4): thin query wrappers, zero business logic, no scoring, no
 * filtering. Columns match the verified DDL (migrations 005/006/007/011; DOC-P3-04 §03.1–03.13).
 * Because Edge Functions run under service_role (RLS bypassed), authorization is enforced upstream
 * (the ownership check in the handler) — these adapters trust the caller-verified profile id.
 *
 * NOTE (atomicity): the Supabase JS client does not wrap multi-statement transactions; production
 * should move persistWeekPlan into a Postgres RPC for the atomic slate write (DOC-P4-00 §16). This
 * adapter performs sequential upserts and is flagged as technical debt (WP-8E work package §debt).
 * These adapters are type-checked but NOT live-DB validated here (no live Supabase, per WP pattern).
 */
import type { SupabaseClient } from "../../db/client.ts";
import { PUBLIC_SCHEMA, RE_ENGINE_SCHEMA } from "../../constants/schemas.ts";
import { AppError } from "../../errors/app-error.ts";
import { ERROR_CATALOGUE } from "../../errors/catalogue.ts";
import type { PlanSlotRow, WeekPlanRow, WeekPlanStore } from "../planning/persistence.ts";
import type {
  HouseholdMemberRow,
  OnboardingSessionRow,
  OnboardingStore,
  ProfileRow,
  UserReStateRow,
} from "../onboarding/orchestrator.ts";
import type { PlanSlotStore, ReStateStore } from "../recommendations/service.ts";
import type { EligibleUser, EligibleUsersStore } from "../scheduler/nightly-plan.ts";
import type { DietType, DishCandidate, MealSlot } from "../re/types.ts";
import type { CandidateRepository } from "../re/ports.ts";

/** Raise a 500 without leaking the raw DB error to the client (DOC-P3-07). */
function dbFail(op: string, message: string): never {
  throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: `${op}: ${message}` });
}

// ── Plan persistence (public.week_plans + public.plan_slots) ─────────────────────────────────────

export class SupabaseWeekPlanStore implements WeekPlanStore {
  constructor(private readonly db: SupabaseClient) {}

  async persistWeekPlan(
    header: WeekPlanRow,
    slots: PlanSlotRow[],
  ): Promise<{ weekPlanId: string; weekStartDate: string }> {
    // Upsert the header on the natural key (profile_id, week_start_date) — DOC-P3-04 §03.12 UNIQUE.
    const { data: wp, error: wpErr } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("week_plans")
      .upsert({
        profile_id: header.profile_id,
        week_start_date: header.week_start_date,
        re_version: header.re_version,
      }, { onConflict: "profile_id,week_start_date" })
      .select("id")
      .single();
    if (wpErr || !wp) dbFail("persist week_plans", wpErr?.message ?? "no row");

    const weekPlanId = (wp as { id: string }).id;
    const slotRows = slots.map((s) => ({
      week_plan_id: weekPlanId,
      slot_date: s.slot_date,
      meal_slot: s.meal_slot,
      class_code: s.class_code,
      selected_dish_id: s.selected_dish_id,
      slate_dish_ids: s.slate_dish_ids,
      slate_reasons: s.slate_reasons,
      slate_confidence: s.slate_confidence,
      slate_generated_at: new Date().toISOString(),
      cold_start_mode: s.cold_start_mode,
    }));
    const { error: slotErr } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("plan_slots")
      .upsert(slotRows, { onConflict: "week_plan_id,slot_date,meal_slot" });
    if (slotErr) dbFail("persist plan_slots", slotErr.message);

    return { weekPlanId, weekStartDate: header.week_start_date };
  }

  async updateSlotSlate(weekPlanId: string, slot: PlanSlotRow): Promise<{ slotId: string }> {
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("plan_slots")
      .update({
        selected_dish_id: slot.selected_dish_id,
        slate_dish_ids: slot.slate_dish_ids,
        slate_reasons: slot.slate_reasons,
        slate_confidence: slot.slate_confidence,
        slate_generated_at: new Date().toISOString(),
      })
      .eq("week_plan_id", weekPlanId)
      .eq("slot_date", slot.slot_date)
      .eq("meal_slot", slot.meal_slot)
      .select("id")
      .single();
    if (error || !data) dbFail("update plan_slots slate", error?.message ?? "no row");
    return { slotId: (data as { id: string }).id };
  }
}

// ── Onboarding writes (profiles, household_members, onboarding_sessions, user_re_state/vectors) ──

export class SupabaseOnboardingStore implements OnboardingStore {
  constructor(private readonly db: SupabaseClient) {}

  async isPersonalizationGranted(profileId: string): Promise<boolean> {
    // Latest 'personalization' consent row for this profile (append-only history, DOC-P3-04 §03.4).
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("consent_records")
      .select("granted, granted_at")
      .eq("profile_id", profileId)
      .eq("consent_type", "personalization")
      .order("granted_at", { ascending: false })
      .limit(1)
      .maybeSingle();
    if (error) dbFail("read consent", error.message);
    return data ? (data as { granted: boolean }).granted === true : false;
  }

  async isOnboardingComplete(profileId: string): Promise<boolean> {
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("profiles")
      .select("onboarding_completed")
      .eq("id", profileId)
      .maybeSingle();
    if (error) dbFail("read profile", error.message);
    return data ? (data as { onboarding_completed: boolean }).onboarding_completed === true : false;
  }

  async persistProfile(row: ProfileRow): Promise<void> {
    const { error } = await this.db.schema(PUBLIC_SCHEMA).from("profiles").upsert({
      id: row.id,
      primary_cook_name: row.primary_cook_name,
      home_state: row.home_state,
      current_city: row.current_city,
      migration_duration_band: row.migration_duration_band,
      city_overlay_weight: row.city_overlay_weight,
      diet_type: row.diet_type,
      religious_pref: row.religious_pref,
      allergen_flags: row.allergen_flags,
      cook_capability: row.cook_capability,
      push_notification_time: row.push_notification_time,
      onboarding_completed: row.onboarding_completed,
      updated_at: new Date().toISOString(),
    }, { onConflict: "id" });
    if (error) dbFail("persist profile", error.message);
  }

  async persistHouseholdMembers(profileId: string, members: HouseholdMemberRow[]): Promise<void> {
    if (members.length === 0) return;
    const { error } = await this.db.schema(PUBLIC_SCHEMA).from("household_members").insert(
      members.map((m) => ({
        profile_id: profileId,
        member_name: m.member_name,
        segment: m.segment,
        allergen_flags: m.allergen_flags,
      })),
    );
    if (error) dbFail("persist household_members", error.message);
  }

  async persistOnboardingSessions(
    profileId: string,
    sessions: OnboardingSessionRow[],
  ): Promise<void> {
    if (sessions.length === 0) return;
    const { error } = await this.db.schema(PUBLIC_SCHEMA).from("onboarding_sessions").insert(
      sessions.map((s) => ({
        profile_id: profileId,
        screen_id: s.screen_id,
        question_key: s.question_key,
        answer_value: s.answer_value ?? null,
        skipped: s.skipped,
      })),
    );
    if (error) dbFail("persist onboarding_sessions", error.message);
  }

  async persistUserReState(row: UserReStateRow): Promise<void> {
    const { error } = await this.db.schema(RE_ENGINE_SCHEMA).from("user_re_state").upsert({
      profile_id: row.profile_id,
      persona_id: row.persona_id,
      overlay_persona_ids: row.overlay_persona_ids,
      confidence_score: row.confidence_score,
      interaction_count: row.interaction_count,
      cold_start_mode: row.cold_start_mode,
      re_engine_version: row.re_engine_version,
      city_overlay_weight: row.city_overlay_weight,
      updated_at: new Date().toISOString(),
    }, { onConflict: "profile_id" });
    if (error) dbFail("persist user_re_state", error.message);
  }

  async persistTasteVector(
    profileId: string,
    classAffinity: Record<string, number>,
  ): Promise<void> {
    const { error } = await this.db.schema(RE_ENGINE_SCHEMA).from("user_taste_vectors").upsert({
      profile_id: profileId,
      class_affinity: classAffinity,
      updated_at: new Date().toISOString(),
    }, { onConflict: "profile_id" });
    if (error) dbFail("persist user_taste_vectors", error.message);
  }
}

// ── Recommendations caller-load path ─────────────────────────────────────────────────────────────

export class SupabasePlanSlotStore implements PlanSlotStore {
  constructor(private readonly db: SupabaseClient) {}

  async getSlotClass(
    profileId: string,
    slotDate: string,
    mealSlot: MealSlot,
  ): Promise<{ weekPlanId: string; classCode: string } | null> {
    // Join plan_slots → week_plans to scope by owner (service_role bypasses RLS; owner asserted upstream).
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("plan_slots")
      .select("class_code, week_plan_id, week_plans!inner(profile_id)")
      .eq("slot_date", slotDate)
      .eq("meal_slot", mealSlot)
      .eq("week_plans.profile_id", profileId)
      .maybeSingle();
    if (error) dbFail("read plan_slot class", error.message);
    if (!data) return null;
    const row = data as { class_code: string; week_plan_id: string };
    return { weekPlanId: row.week_plan_id, classCode: row.class_code };
  }
}

/** Loads eligible users for the nightly job (last_active_at within 7 days, DOC-P3-03 §14). */
export class SupabaseEligibleUsersStore implements EligibleUsersStore {
  constructor(private readonly db: SupabaseClient, private readonly loadUser: ReStateStore) {}

  async getEligibleUsers(): Promise<EligibleUser[]> {
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString();
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("profiles")
      .select("id")
      .eq("onboarding_completed", true)
      .is("deleted_at", null)
      .gte("last_active_at", sevenDaysAgo);
    if (error) dbFail("read eligible users", error.message);

    const weekStartDate = nextMonday();
    const out: EligibleUser[] = [];
    for (const r of (data ?? []) as Array<{ id: string }>) {
      const loaded = await this.loadUser.loadUser(r.id);
      if (loaded) out.push({ ...loaded, weekStartDate });
    }
    return out;
  }
}

/** Monday of next week (YYYY-MM-DD), UTC. */
function nextMonday(): string {
  const d = new Date();
  const day = d.getUTCDay(); // 0=Sun
  const add = ((8 - day) % 7) || 7;
  d.setUTCDate(d.getUTCDate() + add);
  return d.toISOString().slice(0, 10);
}

// ── Candidate repository (LF-D01 / LF-D07) ──────────────────────────────────────────────────────
//
// No FK constraints exist between dishes/dish_ingredients/dish_tags/re_class_dish_options and their
// reference tables (verified against pg_constraint — only re_class_dish_options.meal_class_code has
// one). PostgREST relational embedding (`.select("cuisines(cuisine_group)")`) depends on discoverable
// FK metadata, so it is NOT used here — every join below is a flat query, combined in TypeScript.
// This is a data-integrity observation worth a future migration, not something fixed in this adapter.

/** DOC-P3-13 §1 priority for collapsing a dish's (possibly multi-row) main_ingredient_class tags to
 * the single value the engine's variety guard (LF-F01/F02) needs. Protein/pulse beats grain beats
 * everything else — the same order DOC-P3-13 documents for identifying "the" dominant ingredient. */
const MAIN_INGREDIENT_CLASS_PRIORITY = [
  "meat",
  "seafood",
  "egg",
  "legume_lentil",
  "dairy",
  "grain",
  "vegetable",
  "leafy_vegetable",
  "coconut",
  "nut_dry_fruit",
  "fruit",
  "condiment",
  "oil_fat",
  "sweetener",
];

/** Tag dimensions the candidate needs, each collapsed to one value per dish. */
const CANDIDATE_TAG_DIMENSIONS = ["cooking_method", "texture", "main_ingredient_class"] as const;
type CandidateTagDimension = typeof CANDIDATE_TAG_DIMENSIONS[number];

interface DishRow {
  id: string;
  diet_type: string | null;
  is_jain: boolean | null;
  meal_occasion: string[];
  genome_vector: number[] | null;
  cook_time_minutes: number;
  cuisine_id: string | null;
}

interface AllergenMarks {
  union: number;
  hasBeef: boolean;
  hasPork: boolean;
}

/** Picks one tag_name per (dish, dimension), tie-breaking deterministically instead of by DB-return
 * order. `main_ingredient_class` uses the documented DOC-P3-13 priority; the two Tier-2 dimensions
 * with no equivalent spec (`cooking_method`, `texture`) fall back to lowest `vector_position` —
 * arbitrary but deterministic and documented, not silent. */
function pickTag(
  dimension: CandidateTagDimension,
  rows: Array<{ tag_name: string; vector_position: number }>,
): string {
  if (rows.length === 1) return rows[0].tag_name;
  if (dimension === "main_ingredient_class") {
    const sorted = [...rows].sort((a, b) => {
      const pa = MAIN_INGREDIENT_CLASS_PRIORITY.indexOf(a.tag_name);
      const pb = MAIN_INGREDIENT_CLASS_PRIORITY.indexOf(b.tag_name);
      return (pa === -1 ? Infinity : pa) - (pb === -1 ? Infinity : pb);
    });
    return sorted[0].tag_name;
  }
  return [...rows].sort((a, b) => a.vector_position - b.vector_position)[0].tag_name;
}

/** Fail loudly rather than default a safety-relevant field the DB should never actually leave null. */
function assertNotNull<T>(value: T | null, field: string, dishId: string): T {
  if (value === null) {
    throw new AppError(ERROR_CATALOGUE.INTERNAL, {
      detail:
        `dish ${dishId}: required field '${field}' is null (should be trigger-derived, never null)`,
    });
  }
  return value;
}

export class SupabaseCandidateRepository implements CandidateRepository {
  constructor(private readonly db: SupabaseClient) {}

  /** LF-D01: candidates for a meal class (re_class_dish_options ⨝ dishes ⨝ ingredients ⨝ tags). */
  async getClassCandidates(classCode: string): Promise<DishCandidate[]> {
    const { data, error } = await this.db
      .schema(RE_ENGINE_SCHEMA)
      .from("re_class_dish_options")
      .select("dish_id, base_score, meal_class_code")
      .eq("meal_class_code", classCode);
    if (error) dbFail("read re_class_dish_options", error.message);

    const options = (data ?? []) as Array<
      { dish_id: string; base_score: number; meal_class_code: string }
    >;
    if (options.length === 0) return [];

    const dishIds = options.map((o) => o.dish_id);
    const [dishes, allergens, tags] = await Promise.all([
      this.loadDishes(dishIds),
      this.loadAllergenMarks(dishIds),
      this.loadTags(dishIds),
    ]);
    const cuisineGroups = await this.loadCuisineGroups(
      [...dishes.values()].map((d) => d.cuisine_id),
    );

    const out: DishCandidate[] = [];
    for (const opt of options) {
      const dish = dishes.get(opt.dish_id);
      if (!dish) continue; // inactive or otherwise excluded — never fabricated
      out.push(this.assemble(
        dish,
        opt.base_score,
        opt.meal_class_code,
        allergens.get(opt.dish_id) ?? { union: 0, hasBeef: false, hasPork: false },
        tags.get(opt.dish_id),
        cuisineGroups,
      ));
    }
    return out;
  }

  /** LF-D07 fallback: 8 most-popular dishes filtered by diet_type only (RE-DOC-01 §05 / DOC-P3-03
   * LF-D07: "no class constraint, no other filters"). `dietType` is matched by EXACT equality against
   * `dishes.diet_type`, not the broadened Hard-Constraint-1 set membership `passesDietType` applies
   * (veg → veg/vegan/jain) — duplicating that rule here would put business logic in the adapter.
   * Flagged: this can make the fallback narrower than the broadened rule would allow, never wrong. */
  async getPopularFallback(dietType: string, limit: number): Promise<DishCandidate[]> {
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("dishes")
      .select(
        "id, diet_type, is_jain, meal_occasion, genome_vector, cook_time_minutes, cuisine_id, popularity_score, is_active",
      )
      .eq("diet_type", dietType)
      .eq("is_active", true)
      .order("popularity_score", { ascending: false })
      .limit(limit);
    if (error) dbFail("read popular fallback dishes", error.message);

    const rows = (data ?? []) as Array<DishRow & { popularity_score: number; is_active: boolean }>;
    if (rows.length === 0) return [];

    const dishIds = rows.map((r) => r.id);
    const [allergens, tags] = await Promise.all([
      this.loadAllergenMarks(dishIds),
      this.loadTags(dishIds),
    ]);
    const cuisineGroups = await this.loadCuisineGroups(rows.map((r) => r.cuisine_id));

    return rows.map((dish) =>
      this.assemble(
        dish,
        dish.popularity_score, // substitute for class base_score — LF-D07 has no class ranking
        "", // LF-D07: fallback is diet-only, no class constraint — never fabricate a class
        allergens.get(dish.id) ?? { union: 0, hasBeef: false, hasPork: false },
        tags.get(dish.id),
        cuisineGroups,
      )
    );
  }

  private assemble(
    dish: DishRow,
    baseScore: number,
    classCode: string,
    marks: AllergenMarks,
    tagRow: Map<CandidateTagDimension, string> | undefined,
    cuisineGroups: Map<string, string>,
  ): DishCandidate {
    const dietType = assertNotNull(dish.diet_type, "diet_type", dish.id) as DietType;
    const isJain = assertNotNull(dish.is_jain, "is_jain", dish.id);
    const cuisineFamily = dish.cuisine_id ? cuisineGroups.get(dish.cuisine_id) : undefined;
    if (!cuisineFamily) {
      throw new AppError(ERROR_CATALOGUE.INTERNAL, {
        detail: `dish ${dish.id}: no cuisine_group resolved for cuisine_id ${dish.cuisine_id}`,
      });
    }
    const mainIngredientClass = tagRow?.get("main_ingredient_class") ?? "";
    const isMeatClass = mainIngredientClass === "meat";

    return {
      dishId: dish.id,
      baseScore,
      dietType,
      isJain,
      ingredientAllergenUnion: marks.union,
      mealOccasions: dish.meal_occasion,
      classCode,
      genomeVector: dish.genome_vector ?? [],
      cookTimeBandMinutes: dish.cook_time_minutes,
      // BLOCKER 8F-04 (WP-8FA): no seasonal dish data exists anywhere — documented MVP deferral.
      seasonalAffinity: [],
      cuisineFamily,
      cookingMethod: tagRow?.get("cooking_method") ?? "",
      mainIngredientClass,
      texture: tagRow?.get("texture") ?? "",
      // BLOCKER 8F-03 (WP-8FA): halal certification is unmodelled anywhere; conservative fail-closed
      // proxy per WP-8FA's own recommendation, updated to use the now-populated main_ingredient_class
      // tag (WP-8FA predates it): pork OR dish's main ingredient class is 'meat'.
      hasNonHalalMeat: marks.hasPork || isMeatClass,
      hasBeef: marks.hasBeef,
      hasPork: marks.hasPork,
    };
  }

  private async loadDishes(dishIds: string[]): Promise<Map<string, DishRow>> {
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("dishes")
      .select("id, diet_type, is_jain, meal_occasion, genome_vector, cook_time_minutes, cuisine_id")
      .in("id", dishIds)
      .eq("is_active", true);
    if (error) dbFail("read dishes", error.message);
    const map = new Map<string, DishRow>();
    for (const row of (data ?? []) as DishRow[]) map.set(row.id, row);
    return map;
  }

  private async loadAllergenMarks(dishIds: string[]): Promise<Map<string, AllergenMarks>> {
    const { data: links, error: linkErr } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("dish_ingredients")
      .select("dish_id, ingredient_id")
      .in("dish_id", dishIds);
    if (linkErr) dbFail("read dish_ingredients", linkErr.message);
    const linkRows = (links ?? []) as Array<{ dish_id: string; ingredient_id: string }>;
    if (linkRows.length === 0) return new Map();

    const ingredientIds = [...new Set(linkRows.map((r) => r.ingredient_id))];
    const { data: ingredientRows, error: ingErr } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("ingredients")
      .select("id, name, allergen_flags")
      .in("id", ingredientIds);
    if (ingErr) dbFail("read ingredients", ingErr.message);
    const ingredientById = new Map(
      ((ingredientRows ?? []) as Array<{ id: string; name: string; allergen_flags: number }>)
        .map((i) => [i.id, i]),
    );

    const map = new Map<string, AllergenMarks>();
    for (const link of linkRows) {
      const ingredient = ingredientById.get(link.ingredient_id);
      const cur = map.get(link.dish_id) ?? { union: 0, hasBeef: false, hasPork: false };
      if (ingredient) {
        cur.union |= ingredient.allergen_flags;
        if (ingredient.name === "beef") cur.hasBeef = true;
        if (ingredient.name === "pork") cur.hasPork = true;
      }
      map.set(link.dish_id, cur);
    }
    return map;
  }

  private async loadTags(
    dishIds: string[],
  ): Promise<Map<string, Map<CandidateTagDimension, string>>> {
    const { data: links, error: linkErr } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("dish_tags")
      .select("dish_id, tag_id")
      .in("dish_id", dishIds);
    if (linkErr) dbFail("read dish_tags", linkErr.message);
    const linkRows = (links ?? []) as Array<{ dish_id: string; tag_id: string }>;
    if (linkRows.length === 0) return new Map();

    const tagIds = [...new Set(linkRows.map((r) => r.tag_id))];
    const { data: tagRows, error: tagErr } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("tags")
      .select("id, tag_name, dimension, vector_position")
      .in("id", tagIds)
      .in("dimension", [...CANDIDATE_TAG_DIMENSIONS]);
    if (tagErr) dbFail("read tags", tagErr.message);
    const tagById = new Map(
      ((tagRows ?? []) as Array<
        { id: string; tag_name: string; dimension: string; vector_position: number }
      >).map((t) => [t.id, t]),
    );

    const byDishDimension = new Map<
      string,
      Map<CandidateTagDimension, Array<{ tag_name: string; vector_position: number }>>
    >();
    for (const link of linkRows) {
      const tag = tagById.get(link.tag_id);
      if (!tag) continue; // not one of the 3 candidate dimensions
      const dim = tag.dimension as CandidateTagDimension;
      const perDish = byDishDimension.get(link.dish_id) ?? new Map();
      const list = perDish.get(dim) ?? [];
      list.push({ tag_name: tag.tag_name, vector_position: tag.vector_position });
      perDish.set(dim, list);
      byDishDimension.set(link.dish_id, perDish);
    }

    const out = new Map<string, Map<CandidateTagDimension, string>>();
    for (const [dishId, perDish] of byDishDimension) {
      const resolved = new Map<CandidateTagDimension, string>();
      for (const [dim, rows] of perDish) resolved.set(dim, pickTag(dim, rows));
      out.set(dishId, resolved);
    }
    return out;
  }

  private async loadCuisineGroups(cuisineIds: Array<string | null>): Promise<Map<string, string>> {
    const ids = [...new Set(cuisineIds.filter((id): id is string => id !== null))];
    if (ids.length === 0) return new Map();
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("cuisines")
      .select("id, cuisine_group")
      .in("id", ids);
    if (error) dbFail("read cuisines", error.message);
    const map = new Map<string, string>();
    for (const row of (data ?? []) as Array<{ id: string; cuisine_group: string }>) {
      map.set(row.id, row.cuisine_group);
    }
    return map;
  }
}

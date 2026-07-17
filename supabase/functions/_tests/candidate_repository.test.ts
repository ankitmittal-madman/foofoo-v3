/**
 * SupabaseCandidateRepository adapter tests (Wave 3).
 *
 * Fakes the Supabase query-builder chain only (no live DB — matches the WP-8E convention that
 * adapters are type-checked but not live-DB validated here). Proves: (1) all 17 DishCandidate
 * fields hydrate correctly against a small fixture, (2) the multi-valued dish_tags dimensions
 * (main_ingredient_class / cooking_method / texture) collapse to one value via the documented
 * tie-break rather than DB-return order, and (3) the actual hexagonal-architecture claim — that
 * applyHardConstraints() and the scoring.ts functions accept this adapter's output unmodified.
 */
import { assertEquals } from "@std/assert";
import { SupabaseCandidateRepository } from "../_shared/services/adapters/supabase-stores.ts";
import type { SupabaseClient } from "../_shared/db/client.ts";
import { applyHardConstraints, contentMatch, contextFit } from "../_shared/services/re/index.ts";

// ── fake query builder (thenable chain; routes on table name only) ─────────────────────────────

// deno-lint-ignore no-explicit-any
type Row = Record<string, any>;

class FakeQuery implements PromiseLike<{ data: Row[]; error: null }> {
  constructor(private rows: Row[]) {}
  select(_cols: string) {
    return this;
  }
  eq(col: string, val: unknown) {
    this.rows = this.rows.filter((r) => r[col] === val);
    return this;
  }
  in(col: string, vals: unknown[]) {
    const set = new Set(vals);
    this.rows = this.rows.filter((r) => set.has(r[col]));
    return this;
  }
  order(_col: string, _opts?: unknown) {
    return this;
  }
  limit(_n: number) {
    return this;
  }
  then<TResult1, TResult2>(
    onfulfilled?: (value: { data: Row[]; error: null }) => TResult1 | PromiseLike<TResult1>,
  ): PromiseLike<TResult1 | TResult2> {
    return Promise.resolve({ data: this.rows, error: null }).then(onfulfilled) as PromiseLike<
      TResult1 | TResult2
    >;
  }
}

class FakeSupabaseClient {
  constructor(private tables: Record<string, Row[]>) {}
  schema(_name: string) {
    return this;
  }
  from(table: string) {
    return new FakeQuery(this.tables[table] ?? []);
  }
}

function fakeClient(tables: Record<string, Row[]>): SupabaseClient {
  return new FakeSupabaseClient(tables) as unknown as SupabaseClient;
}

// ── fixture: 3 dishes covering the multi-class tie-break, halal/pork proxy, and cuisine join ───

const TAGS = [
  { id: "t-grain", tag_name: "grain", dimension: "main_ingredient_class", vector_position: 1 },
  { id: "t-meat", tag_name: "meat", dimension: "main_ingredient_class", vector_position: 2 },
  {
    id: "t-legume",
    tag_name: "legume_lentil",
    dimension: "main_ingredient_class",
    vector_position: 3,
  },
  { id: "t-dum", tag_name: "dum_cooked", dimension: "cooking_method", vector_position: 10 },
  { id: "t-boiled", tag_name: "boiled", dimension: "cooking_method", vector_position: 11 },
  { id: "t-roasted", tag_name: "roasted", dimension: "cooking_method", vector_position: 12 },
  { id: "t-fluffy", tag_name: "fluffy", dimension: "texture", vector_position: 20 },
  { id: "t-soft", tag_name: "soft", dimension: "texture", vector_position: 21 },
  { id: "t-chewy", tag_name: "chewy", dimension: "texture", vector_position: 22 },
];

const INGREDIENTS = [
  { id: "i-rice", name: "rice_basmati", allergen_flags: 0 },
  { id: "i-chicken", name: "chicken", allergen_flags: 0 },
  { id: "i-chana", name: "chana_dal", allergen_flags: 1 },
  { id: "i-pork", name: "pork", allergen_flags: 0 },
];

const TABLES: Record<string, Row[]> = {
  re_class_dish_options: [
    { dish_id: "d1", base_score: 0.7, meal_class_code: "TEST_CLASS" },
    { dish_id: "d2", base_score: 0.6, meal_class_code: "TEST_CLASS" },
    { dish_id: "d3", base_score: 0.5, meal_class_code: "TEST_CLASS" },
  ],
  dishes: [
    {
      id: "d1",
      diet_type: "non_veg",
      is_jain: false,
      meal_occasion: ["dinner", "any"],
      genome_vector: [1, 0],
      cook_time_minutes: 45,
      cuisine_id: "c1",
      is_active: true,
      popularity_score: 0.9,
    },
    {
      id: "d2",
      diet_type: "veg",
      is_jain: true,
      meal_occasion: ["lunch", "any"],
      genome_vector: [0, 1],
      cook_time_minutes: 20,
      cuisine_id: "c2",
      is_active: true,
      popularity_score: 0.8,
    },
    {
      id: "d3",
      diet_type: "non_veg",
      is_jain: false,
      meal_occasion: ["dinner", "any"],
      genome_vector: [0.5, 0.5],
      cook_time_minutes: 60,
      cuisine_id: "c1",
      is_active: true,
      popularity_score: 0.4,
    },
  ],
  cuisines: [
    { id: "c1", cuisine_group: "mughlai_nawabi" },
    { id: "c2", cuisine_group: "south_indian" },
  ],
  dish_ingredients: [
    { dish_id: "d1", ingredient_id: "i-rice" },
    { dish_id: "d1", ingredient_id: "i-chicken" },
    { dish_id: "d2", ingredient_id: "i-chana" },
    { dish_id: "d3", ingredient_id: "i-pork" },
  ],
  ingredients: INGREDIENTS,
  dish_tags: [
    // d1: Biryani-like — grain + meat (the documented 40-dish multi-class case, DOC-P3-13 §2)
    { dish_id: "d1", tag_id: "t-grain" },
    { dish_id: "d1", tag_id: "t-meat" },
    { dish_id: "d1", tag_id: "t-dum" },
    { dish_id: "d1", tag_id: "t-fluffy" },
    // d2: single-valued everywhere
    { dish_id: "d2", tag_id: "t-legume" },
    { dish_id: "d2", tag_id: "t-boiled" },
    { dish_id: "d2", tag_id: "t-soft" },
    // d3: pork dish, single-valued
    { dish_id: "d3", tag_id: "t-meat" },
    { dish_id: "d3", tag_id: "t-roasted" },
    { dish_id: "d3", tag_id: "t-chewy" },
  ],
  tags: TAGS,
};

Deno.test("getClassCandidates — hydrates all 17 DishCandidate fields correctly", async () => {
  const repo = new SupabaseCandidateRepository(fakeClient(TABLES));
  const result = await repo.getClassCandidates("TEST_CLASS");
  assertEquals(result.length, 3);

  const d1 = result.find((c) => c.dishId === "d1")!;
  assertEquals(d1.baseScore, 0.7);
  assertEquals(d1.dietType, "non_veg");
  assertEquals(d1.isJain, false);
  assertEquals(d1.ingredientAllergenUnion, 0);
  assertEquals(d1.mealOccasions, ["dinner", "any"]);
  assertEquals(d1.classCode, "TEST_CLASS");
  assertEquals(d1.genomeVector, [1, 0]);
  assertEquals(d1.cookTimeBandMinutes, 45);
  assertEquals(d1.seasonalAffinity, []); // BLOCKER 8F-04 — documented deferral, always empty
  assertEquals(d1.cuisineFamily, "mughlai_nawabi");
  assertEquals(d1.cookingMethod, "dum_cooked");
  assertEquals(d1.texture, "fluffy");
  assertEquals(d1.hasBeef, false);
  assertEquals(d1.hasPork, false);
});

Deno.test("getClassCandidates — multi-class dish (grain+meat) collapses to 'meat' per DOC-P3-13 priority", async () => {
  const repo = new SupabaseCandidateRepository(fakeClient(TABLES));
  const result = await repo.getClassCandidates("TEST_CLASS");
  const d1 = result.find((c) => c.dishId === "d1")!;
  // d1 carries BOTH grain and meat dish_tags rows (like the real Biryani (Mughlai Chicken) case) —
  // must not silently take DB-return order; must apply the documented protein-over-grain priority.
  assertEquals(d1.mainIngredientClass, "meat");
});

Deno.test("getClassCandidates — single-valued dish preserves its one tag with no tie-break needed", async () => {
  const repo = new SupabaseCandidateRepository(fakeClient(TABLES));
  const result = await repo.getClassCandidates("TEST_CLASS");
  const d2 = result.find((c) => c.dishId === "d2")!;
  assertEquals(d2.mainIngredientClass, "legume_lentil");
  assertEquals(d2.cookingMethod, "boiled");
  assertEquals(d2.texture, "soft");
  assertEquals(d2.ingredientAllergenUnion, 1); // chana_dal carries allergen flag 1
});

Deno.test("getClassCandidates — hasPork true and hasNonHalalMeat proxy fires for a pork dish", async () => {
  const repo = new SupabaseCandidateRepository(fakeClient(TABLES));
  const result = await repo.getClassCandidates("TEST_CLASS");
  const d3 = result.find((c) => c.dishId === "d3")!;
  assertEquals(d3.hasPork, true);
  assertEquals(d3.hasBeef, false);
  // hasNonHalalMeat proxy (WP-8FA 8F-03, documented MVP limitation): hasPork OR meat-class.
  assertEquals(d3.hasNonHalalMeat, true);
});

Deno.test("getClassCandidates — unknown class code returns an empty array, not an error", async () => {
  const repo = new SupabaseCandidateRepository(fakeClient(TABLES));
  const result = await repo.getClassCandidates("NO_SUCH_CLASS");
  assertEquals(result, []);
});

Deno.test("getPopularFallback — diet-filtered (exact match), classCode empty (LF-D07: no class constraint)", async () => {
  const repo = new SupabaseCandidateRepository(fakeClient(TABLES));
  const result = await repo.getPopularFallback("non_veg", 8);
  // Only d1 and d3 are diet_type='non_veg' in the fixture — d2 ('veg') must be excluded by the
  // adapter's .eq("diet_type", dietType) filter, which the fake now genuinely applies.
  assertEquals(result.map((c) => c.dishId).sort(), ["d1", "d3"]);
  for (const c of result) {
    assertEquals(c.classCode, ""); // LF-D07: fallback has no class — never fabricated
  }
  const d1 = result.find((c) => c.dishId === "d1")!;
  assertEquals(d1.baseScore, 0.9); // substituted with popularity_score, not re_class_dish_options
});

Deno.test("getPopularFallback — diet_type is an EXACT match, not the broadened hard-constraint-1 set", async () => {
  const repo = new SupabaseCandidateRepository(fakeClient(TABLES));
  // A 'veg' request must not pull in 'vegan'/'jain' dishes here (that broadening lives only in
  // constraints.ts passesDietType, deliberately not duplicated into this adapter).
  const result = await repo.getPopularFallback("veg", 8);
  assertEquals(result.map((c) => c.dishId), ["d2"]);
});

// ── the actual hexagonal-architecture claim: downstream code accepts this output unmodified ────

Deno.test("hexagonal architecture holds — applyHardConstraints runs on adapter output unmodified", async () => {
  const repo = new SupabaseCandidateRepository(fakeClient(TABLES));
  const candidates = await repo.getClassCandidates("TEST_CLASS");

  // A "veg" household: d1 (non_veg) and d3 (non_veg) must be excluded; d2 (veg) survives.
  const survivors = applyHardConstraints(candidates, {
    dietType: "veg",
    religiousPref: "all",
    combinedAllergenFlags: 0,
    mealSlot: "lunch",
    activeNeverIds: new Set(),
  });
  assertEquals(survivors.map((s) => s.dishId), ["d2"]);
});

Deno.test("hexagonal architecture holds — scoring.ts functions accept adapter output unmodified", async () => {
  const repo = new SupabaseCandidateRepository(fakeClient(TABLES));
  const candidates = await repo.getClassCandidates("TEST_CLASS");
  const d1 = candidates.find((c) => c.dishId === "d1")!;

  // contentMatch (LF-E03) reads genomeVector directly off the candidate — no adapter-side shim.
  const cm = contentMatch([1, 0], d1.genomeVector);
  assertEquals(cm, 1); // identical vectors → cosine similarity 1

  // contextFit (LF-E05) reads cookTimeBandMinutes directly off the candidate.
  const cf = contextFit(d1, [], "weekday");
  assertEquals(cf, 0); // 45 min > 30 min weekday threshold — no boost, no error
});

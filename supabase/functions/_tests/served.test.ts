/**
 * §0.1 tests — shown_not_tapped emission helpers (recommendations/served.ts).
 *
 * Pure-logic coverage only (buildShownNotTappedRows / flattenServedDishes): no DB required,
 * since resolveDishIdsByName's only job is a batched lookup already covered in spirit by
 * feedback/events.ts's equivalent single-name lookup. This asserts the core §0.1 requirement:
 * N served hero dishes across the response's plates[] produce exactly N shown_not_tapped rows.
 */
import { assertEquals } from "@std/assert";
import {
  buildShownNotTappedRows,
  flattenServedDishes,
  toExposureItems,
} from "../recommendations/served.ts";

Deno.test("flattenServedDishes: a mix of pair (2 heroes) and single (1 hero) plates flattens to one entry per served dish", () => {
  const plates = [
    { plate_id: "p1", form: "pair", hero_dish_names: ["Onion Pakora", "Roti"] },
    { plate_id: "p2", form: "single", hero_dish_names: ["Chole"] },
    { plate_id: "p3", form: "standalone", hero_dish_names: ["Khichdi"] },
  ];
  const served = flattenServedDishes(plates);
  assertEquals(served.map((s) => s.dishName), ["Onion Pakora", "Roti", "Chole", "Khichdi"]);
});

Deno.test("flattenServedDishes: plan dish cards contribute to the shown denominator", () => {
  const served = flattenServedDishes([
    { id: "dish-1", name: "Indori Poha" },
    { id: "dish-2", name: "  Daal Bafla  " },
  ]);
  assertEquals(served.map((s) => s.dishName), ["Indori Poha", "Daal Bafla"]);
});

Deno.test("toExposureItems: preserves observed plan metadata without inventing missing values", () => {
  const served = flattenServedDishes([
    {
      name: "Indori Poha",
      cuisine: "madhya_pradesh",
      meal_class_code: "BF_POHA",
      heaviness: 1,
      total_mins: 25,
    },
    { name: "Daal Bafla" },
  ]);
  assertEquals(toExposureItems(served), [
    {
      dish_name: "Indori Poha",
      meal_class_code: "BF_POHA",
      cuisine_family: "madhya_pradesh",
      heaviness: 1,
      total_mins: 25,
    },
    { dish_name: "Daal Bafla" },
  ]);
});

Deno.test("flattenServedDishes: episode components contribute to the shown denominator", () => {
  const served = flattenServedDishes([
    {
      episode_id: "episode-1",
      components: [
        { dish_name: "Pav Bhaji" },
        { dish_name: "Mawa Bati" },
        { dish_name: " " },
      ],
    },
  ]);
  assertEquals(served.map((s) => s.dishName), ["Pav Bhaji", "Mawa Bati"]);
  assertEquals(toExposureItems(served), [
    { dish_name: "Pav Bhaji" },
    { dish_name: "Mawa Bati" },
  ]);
});

Deno.test("toExposureItems: episode cadence metadata is copied to displayed components", () => {
  const served = flattenServedDishes([{
    components: [{ dish_name: "Pav Bhaji" }],
    richness_score: 0.8,
    practicality: { active_minutes: 35 },
  }]);
  assertEquals(toExposureItems(served), [{
    dish_name: "Pav Bhaji",
    total_mins: 35,
    richness_score: 0.8,
  }]);
});

Deno.test("flattenServedDishes: non-array / malformed input yields zero served dishes, never throws", () => {
  assertEquals(flattenServedDishes(undefined), []);
  assertEquals(flattenServedDishes(null), []);
  assertEquals(flattenServedDishes([{ plate_id: "p1" }]), []);
});

Deno.test("buildShownNotTappedRows: N served dishes across plates produce exactly N shown_not_tapped rows", () => {
  const plates = [
    { plate_id: "p1", form: "pair", hero_dish_names: ["Onion Pakora", "Roti"] },
    { plate_id: "p2", form: "single", hero_dish_names: ["Chole"] },
  ];
  const served = flattenServedDishes(plates);
  const dishIds = new Map([["Onion Pakora", "dish-uuid-1"], ["Chole", "dish-uuid-3"]]);
  const rows = buildShownNotTappedRows("profile-1", "rec-event-1", served, dishIds);

  assertEquals(rows.length, served.length);
  assertEquals(rows.length, 3);
  for (const row of rows) {
    assertEquals(row.profile_id, "profile-1");
    assertEquals(row.household_id, "profile-1");
    assertEquals(row.recommendation_event_id, "rec-event-1");
    assertEquals(row.event_type, "shown_not_tapped");
    assertEquals(row.data_source, "real");
  }
  // Resolved dish -> real uuid; unresolved dish ("Roti" not in the map) -> null, never dropped.
  assertEquals(rows[0].dish_id, "dish-uuid-1");
  assertEquals(rows[1].dish_id, null);
  assertEquals(rows[2].dish_id, "dish-uuid-3");
});

Deno.test("buildShownNotTappedRows: zero served dishes produces zero rows", () => {
  const rows = buildShownNotTappedRows("profile-1", "rec-event-1", [], new Map());
  assertEquals(rows.length, 0);
});

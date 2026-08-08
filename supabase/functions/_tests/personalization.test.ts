import { assertEquals } from "@std/assert";
import {
  aggregateAffinityMaps,
  extractExposureDishNames,
  extractExposurePrimaryNames,
  extractPersistedCadence,
  extractPersistedExposureDishNames,
  extractPersistedVarietyCounts,
  extractTemporalAttributeState,
  extractTemporalClassState,
  selectImmediateRefreshExclusions,
} from "../recommendations/personalization.ts";

Deno.test("extractTemporalClassState: keeps canonical slot and rhythm rows", () => {
  assertEquals(
    extractTemporalClassState([
      { meal_slot: "lunch", day_type: "weekday", class_code: "LD_DAL_ROTI" },
      { meal_slot: "snacks", day_type: "weekday", class_code: "BAD" },
      { meal_slot: "dinner", day_type: "holiday", class_code: "BAD" },
    ]),
    [{ meal_slot: "lunch", day_type: "weekday", class_code: "LD_DAL_ROTI" }],
  );
  assertEquals(extractTemporalClassState(null), []);
});

Deno.test("extractTemporalAttributeState: keeps only bounded supported dimensions", () => {
  assertEquals(
    extractTemporalAttributeState([
      {
        meal_slot: "lunch",
        day_type: "weekday",
        dimension_code: "richness",
        entity_key: "creamy",
      },
      {
        meal_slot: "snacks",
        day_type: "weekday",
        dimension_code: "dish",
        entity_key: "poha",
      },
      {
        meal_slot: "dinner",
        day_type: "weekend",
        dimension_code: "nutrition",
        entity_key: "protein",
      },
    ]),
    [{
      meal_slot: "lunch",
      day_type: "weekday",
      dimension_code: "richness",
      entity_key: "creamy",
    }],
  );
});

Deno.test("aggregateAffinityMaps combines only members with evidence", () => {
  const result = aggregateAffinityMaps([
    { "dish_category:whole_meal": 0.8 },
    null,
    { "dish_category:whole_meal": -0.2, "richness:light": 0.4 },
  ]);
  assertEquals(result["dish_category:whole_meal"] > 0, true);
  assertEquals(Math.round(result["richness:light"] * 10), 4);
});

Deno.test("extractPersistedVarietyCounts: reads only bounded seven-day class/cuisine state", () => {
  assertEquals(
    extractPersistedVarietyCounts({
      dimensions: [
        {
          dimension_code: "meal_class",
          entity_key: "LD_DAL_RICE",
          window_code: "7d",
          count_in_window: 4,
        },
        {
          dimension_code: "cuisine",
          entity_key: "Maharashtrian",
          window_code: "7d",
          count_in_window: 2,
        },
        {
          dimension_code: "dish_name",
          entity_key: "poha",
          window_code: "30d",
          count_in_window: 99,
        },
        {
          dimension_code: "cuisine",
          entity_key: "ignored",
          window_code: "30d",
          count_in_window: 3,
        },
      ],
    }),
    {
      recentClassCounts: { LD_DAL_RICE: 4 },
      recentCuisineCounts: { Maharashtrian: 2 },
    },
  );
  assertEquals(extractPersistedVarietyCounts(null), {
    recentClassCounts: {},
    recentCuisineCounts: {},
  });
});

Deno.test("extractPersistedExposureDishNames: reads the private variety RPC response", () => {
  assertEquals(
    extractPersistedExposureDishNames({
      recent_dish_names: ["Indori Poha", "Daal Bafla"],
      cadence: { novelty_budget: 0.15 },
    }),
    ["Indori Poha", "Daal Bafla"],
  );
  assertEquals(extractPersistedExposureDishNames(null), []);
  assertEquals(extractPersistedExposureDishNames({ recent_dish_names: "not-an-array" }), []);
});

Deno.test("extractPersistedCadence: validates bounds and supplies neutral defaults", () => {
  assertEquals(
    extractPersistedCadence({ cadence: { novelty_budget: 0.45, richness_debt: 0.2 } }),
    { noveltyBudget: 0.45, richnessDebt: 0.2 },
  );
  assertEquals(extractPersistedCadence(null), { noveltyBudget: 0.15, richnessDebt: 0 });
  assertEquals(
    extractPersistedCadence({ cadence: { novelty_budget: 5, richness_debt: -2 } }),
    { noveltyBudget: 1, richnessDebt: 0 },
  );
});

Deno.test("extractExposureDishNames: event-history fallback supports every serving shape", () => {
  assertEquals(
    extractExposureDishNames([
      { name: "Indori Poha" },
      { hero_dish_names: ["Daal Bafla", "Mawa Bati"] },
      { components: [{ dish_name: "Pav Bhaji" }] },
    ]),
    ["Indori Poha", "Daal Bafla", "Mawa Bati", "Pav Bhaji"],
  );
});

Deno.test("extractExposurePrimaryNames: selects one lead dish for every serving shape", () => {
  assertEquals(
    extractExposurePrimaryNames([
      { name: "Indori Poha" },
      { hero_dish_names: ["Daal Bafla", "Mawa Bati"] },
      {
        components: [
          { dish_name: "Roti", grammar_role: "side", component_role: "staple" },
          { dish_name: "Bhindi", grammar_role: "primary", component_role: "dry_hero" },
        ],
      },
    ]),
    ["Indori Poha", "Daal Bafla", "Bhindi"],
  );
});

Deno.test(
  "selectImmediateRefreshExclusions: latest slate per slot wins and stays bounded",
  () => {
    const persisted = Array.from({ length: 50 }, (_, index) => `Old ${index}`);
    const selected = selectImmediateRefreshExclusions(persisted, [
      {
        slot: "dinner",
        plates: [{
          components: [
            { dish_name: "Latest Dinner", grammar_role: "primary" },
            { dish_name: "Dinner Side", grammar_role: "side" },
          ],
        }],
      },
      {
        slot: "dinner",
        plates: [{ components: [{ dish_name: "Stale Dinner", grammar_role: "primary" }] }],
      },
      {
        slot: "lunch",
        plates: [{
          components: [
            { dish_name: "Latest Lunch", grammar_role: "primary" },
            { dish_name: "Lunch Side", grammar_role: "side" },
          ],
        }],
      },
      {
        slot: "breakfast",
        plates: [{
          components: [
            { dish_name: "Latest Breakfast", grammar_role: "primary" },
            { dish_name: "Breakfast Side", grammar_role: "side" },
          ],
        }],
      },
    ]);
    assertEquals(selected, [
      "Latest Dinner",
      "Latest Lunch",
      "Latest Breakfast",
      "Dinner Side",
      "Lunch Side",
      "Breakfast Side",
    ]);
    assertEquals(selectImmediateRefreshExclusions(persisted, [], 16).length, 16);
  },
);

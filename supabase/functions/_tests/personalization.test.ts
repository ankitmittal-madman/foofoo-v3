import { assertEquals } from "@std/assert";
import {
  aggregateAffinityMaps,
  extractExposureDishNames,
  extractPersistedCadence,
  extractPersistedExposureDishNames,
} from "../recommendations/personalization.ts";

Deno.test("aggregateAffinityMaps combines only members with evidence", () => {
  const result = aggregateAffinityMaps([
    { "dish_category:whole_meal": 0.8 },
    null,
    { "dish_category:whole_meal": -0.2, "richness:light": 0.4 },
  ]);
  assertEquals(result["dish_category:whole_meal"] > 0, true);
  assertEquals(Math.round(result["richness:light"] * 10), 4);
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

import { assertEquals } from "@std/assert";
import {
  extractExposureDishNames,
  extractPersistedExposureDishNames,
} from "../recommendations/personalization.ts";

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

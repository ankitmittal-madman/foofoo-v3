/** Unit coverage for external food research parsing and conservative confidence behavior. */
import { assertEquals } from "@std/assert";
import {
  externalMatchConfidence,
  normalizeFoodName,
  researchDish,
  searchFoodOn,
} from "../dish-ontology/research.ts";

Deno.test("food-name normalization is Unicode-aware and whitespace-stable", () => {
  assertEquals(normalizeFoodName("  Kanda   Poha "), "kanda poha");
});

Deno.test("exact external labels are high-confidence but never canonical-confidence", () => {
  assertEquals(externalMatchConfidence("Poha", "poha"), 0.9);
  assertEquals(externalMatchConfidence("Poha", "Rice flakes", 0.99), 0.8);
});

Deno.test("FoodOn parsing retains raw provider evidence and identifier", async () => {
  const fetcher = () =>
    Promise.resolve(
      new Response(
        JSON.stringify({
          response: { docs: [{ label: "Poha", iri: "http://purl.obolibrary.org/obo/FOODON_123" }] },
        }),
        { status: 200 },
      ),
    );
  const result = await searchFoodOn("Poha", fetcher);
  assertEquals(result?.provider, "foodon_ols");
  assertEquals(result?.confidence, 0.9);
  assertEquals(result?.providerRecordId, "http://purl.obolibrary.org/obo/FOODON_123");
});

Deno.test("one provider failure yields partial research instead of throwing", async () => {
  let calls = 0;
  const fetcher = () => {
    calls += 1;
    if (calls === 1) return Promise.reject(new Error("OLS unavailable"));
    return Promise.resolve(
      new Response(JSON.stringify({ foods: [{ fdcId: 1, description: "Poha" }] }), { status: 200 }),
    );
  };
  const result = await researchDish("Poha", "test-key", fetcher);
  assertEquals(result.records.length, 1);
  assertEquals(result.failedProviders, ["foodon_ols"]);
});

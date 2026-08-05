/** Unit coverage for external food research parsing and conservative confidence behavior. */
import { assertEquals } from "@std/assert";
import {
  externalMatchConfidence,
  normalizeFoodName,
  researchDish,
  searchFoodOn,
} from "../dish-ontology/research.ts";
import { normalizeFoodOn, normalizeUsda } from "../dish-ontology/normalization.ts";

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

Deno.test("FoodOn evidence normalizes identifier and aliases as provisional facts", () => {
  const term = normalizeFoodOn({
    provider: "foodon_ols",
    providerRecordId: "http://purl.obolibrary.org/obo/FOODON_123",
    sourceUrl: "https://example.test",
    confidence: 0.8,
    payload: {
      response: {
        docs: [{
          label: "Flattened rice dish",
          iri: "http://purl.obolibrary.org/obo/FOODON_123",
          synonym: ["Poha", "Aval upma"],
        }],
      },
    },
  });
  assertEquals(term?.code, "FOODON_FOODON_123");
  assertEquals(term?.aliases, ["Poha", "Aval upma"]);
});

Deno.test("USDA evidence normalizes only supported macros with units", () => {
  const nutrients = normalizeUsda({
    provider: "usda_fdc",
    providerRecordId: "42",
    sourceUrl: "https://fdc.nal.usda.gov/",
    confidence: 0.7,
    payload: {
      foods: [{
        foodNutrients: [
          { nutrientName: "Energy", unitName: "KCAL", value: 130 },
          { nutrientName: "Protein", unitName: "G", value: 4.2 },
          { nutrientName: "Sodium, Na", unitName: "MG", value: 100 },
        ],
      }],
    },
  });
  assertEquals(nutrients.map((item) => item.code), ["energy_kcal", "protein_g"]);
  assertEquals(nutrients[0].servingBasis, "100 g");
});

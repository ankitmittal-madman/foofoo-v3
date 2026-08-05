/** Unit coverage for external food research parsing and conservative confidence behavior. */
import { assertEquals } from "@std/assert";
import {
  externalMatchConfidence,
  normalizeFoodName,
  researchDish,
  searchFoodOn,
} from "../dish-ontology/research.ts";
import { normalizeFoodOn, normalizeUsda } from "../dish-ontology/normalization.ts";
import { generateGroqDishEnrichment, sanitizeGroqEnrichment } from "../dish-ontology/ai.ts";

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

Deno.test("Groq parsing accepts structured low-risk ontology fields and records token usage", async () => {
  const fetcher = (_input: string, init?: RequestInit) => {
    const request = JSON.parse(String(init?.body));
    assertEquals(request.model, "openai/gpt-oss-120b");
    assertEquals(request.response_format.type, "json_schema");
    return Promise.resolve(
      new Response(
        JSON.stringify({
          id: "chatcmpl-test",
          choices: [{
            message: {
              content: JSON.stringify({
                aliases: [{
                  name: "Kanda Poha",
                  language: "marathi",
                  region: "maharashtra",
                  alias_type: "regional_name",
                  confidence: 0.91,
                }],
                taxonomy: [{
                  dimension: "texture",
                  code: "soft_fluffy",
                  label: "Soft and fluffy",
                  confidence: 0.84,
                }],
                regional_affinities: [{
                  region_code: "maharashtra",
                  affinity_score: 0.95,
                  confidence: 0.93,
                }],
              }),
            },
          }],
          usage: { prompt_tokens: 100, completion_tokens: 80, total_tokens: 180 },
        }),
        { status: 200 },
      ),
    );
  };
  const result = await generateGroqDishEnrichment(
    "Poha",
    "test-key",
    "openai/gpt-oss-120b",
    fetcher,
  );
  assertEquals(result.record.provider, "groq");
  assertEquals(result.record.providerRecordId, "chatcmpl-test");
  assertEquals(result.enrichment.aliases[0].name, "Kanda Poha");
  assertEquals(result.usage.totalTokens, 180);
});

Deno.test("Groq adapter exposes provider HTTP failures without leaking response content", async () => {
  let message = "";
  try {
    await generateGroqDishEnrichment(
      "Poha",
      "test-key",
      "openai/gpt-oss-120b",
      () => Promise.resolve(new Response("secret provider details", { status: 429 })),
    );
  } catch (error) {
    message = error instanceof Error ? error.message : String(error);
  }
  assertEquals(message, "groq_http_429:provider_error");
});

Deno.test("Groq sanitizer rejects canonical/component aliases and normalizes region codes", () => {
  const result = sanitizeGroqEnrichment("Baati Chokha", {
    aliases: [
      {
        name: "Baati Chokha",
        language: "en",
        region: null,
        alias_type: "common_name",
        confidence: 0.99,
      },
      {
        name: "Baati",
        language: "en",
        region: null,
        alias_type: "spelling_variant",
        confidence: 0.9,
      },
      {
        name: "बाती चोखा",
        language: "hi",
        region: "rajasthan",
        alias_type: "regional_name",
        confidence: 0.9,
      },
    ],
    taxonomy: [],
    regional_affinities: [
      { region_code: "in_rajasthan", affinity_score: 0.9, confidence: 0.9 },
      { region_code: "in_rajasthan", affinity_score: 0.8, confidence: 0.8 },
    ],
  });
  assertEquals(result.aliases.map((item) => item.name), ["बाती चोखा"]);
  assertEquals(result.regional_affinities.map((item) => item.region_code), ["rajasthan"]);
});

import { assertEquals, assertNotEquals } from "@std/assert";
import {
  buildDishLineageCandidates,
  eligibleSetHash,
  extractDishCandidateItems,
  extractDishSlateItems,
  recordDishRecommendationSlate,
  snapshotHash,
  stripPrivateCandidateLineage,
} from "../plan/episodes.ts";
import type { RequestContext } from "../_shared/types/context.ts";

Deno.test("eligible episode hash includes the full deterministic set independent of order", async () => {
  assertEquals(await eligibleSetHash(["b", "a", "c"]), await eligibleSetHash(["c", "b", "a"]));
  assertNotEquals(await eligibleSetHash(["a", "b"]), await eligibleSetHash(["a", "b", "c"]));
});

Deno.test("household snapshot hash is stable across object key order", async () => {
  assertEquals(
    await snapshotHash({ diet: "veg", members: [{ id: "one", age: 30 }] }),
    await snapshotHash({ members: [{ age: 30, id: "one" }], diet: "veg" }),
  );
});

Deno.test("dish slate normalization covers landing-page options without inventing scores", () => {
  const items = extractDishSlateItems("meal_plan", {
    options: [
      { name: "Poha", score: 4.2, meal_class_code: "INDIAN_BREAKFAST" },
      { name: "Upma", score: 3.8, meal_class_code: "INDIAN_BREAKFAST" },
      { name: "missing score" },
    ],
  });
  assertEquals(items.map((item) => item.name), ["Poha", "Upma"]);
  assertEquals(items.map((item) => item.score), [4.2, 3.8]);
});

Deno.test("private candidate lineage keeps the full eligible pool separate from served items", () => {
  const response = {
    options: [{ name: "Poha", score: 3, slot: "breakfast" }],
    _candidate_lineage: [
      { name: "Poha", score: 3, slot: "breakfast" },
      { name: "Upma", score: 2.5, slot: "breakfast", shadow_preference_score: 0.61 },
    ],
  };
  assertEquals(extractDishSlateItems("meal_plan", response).length, 1);
  const candidates = extractDishCandidateItems("meal_plan", response);
  assertEquals(candidates.length, 2);
  assertEquals(candidates[1].snapshot.shadow_preference_score, 0.61);
  assertEquals(
    extractDishCandidateItems("meal_plan", { ...response, _candidate_lineage: [] }).length,
    1,
  );
  assertEquals(stripPrivateCandidateLineage(response), {
    options: [{ name: "Poha", score: 3, slot: "breakfast" }],
  });
});

Deno.test("dish lineage supports a larger private candidate pool than the served slate", async () => {
  const candidates = await buildDishLineageCandidates("calibration", {
    slots: { breakfast: [{ name: "Poha", score: 4.2 }] },
    _candidate_lineage: [
      { name: "Poha", score: 4.2, slot: "breakfast", meal_class_code: "INDIAN_BREAKFAST" },
      { name: "Upma", score: 3.9, slot: "breakfast", meal_class_code: "INDIAN_BREAKFAST" },
      // Duplicate candidates can occur when generators overlap. They must collapse before the
      // database primary key is applied.
      { name: "Upma", score: 3.9, slot: "breakfast", meal_class_code: "INDIAN_BREAKFAST" },
    ],
  });

  assertEquals(candidates.length, 2);
  assertEquals(candidates.map((candidate) => candidate.rank), [1, 2]);
  assertEquals(candidates[1].generator_codes, ["calibration", "INDIAN_BREAKFAST"]);
  assertEquals(candidates[1].generator_scores.point_score, 3.9);
});

Deno.test("calibration slate preserves each cell slot in one globally ordered slate", () => {
  const items = extractDishSlateItems("calibration", {
    slots: {
      breakfast: [{ name: "Poha", score: 4.2 }],
      lunch: [{ name: "Dal", score: 4.0 }],
      dinner: [{ name: "Khichdi", score: 3.9 }],
    },
  });
  assertEquals(items.map((item) => [item.name, item.slot]), [
    ["Poha", "breakfast"],
    ["Dal", "lunch"],
    ["Khichdi", "dinner"],
  ]);
});

Deno.test("calibration remains available when optional slate persistence fails", async () => {
  const warnings: Array<{ message: string; fields?: Record<string, unknown> }> = [];
  const logger = {
    debug: () => {},
    info: () => {},
    warn: (message: string, fields?: Record<string, unknown>) => {
      warnings.push({ message, fields });
    },
    error: () => {},
    child: () => logger,
  };
  const ctx = { logger } as unknown as RequestContext;

  const slateId = await recordDishRecommendationSlate(
    ctx,
    {
      householdId: "11111111-1111-1111-1111-111111111111",
      requestId: "calibration-request",
      surface: "calibration",
      modelVersion: "test",
      configVersion: "test",
      policyCode: "test",
      latencyMs: 1,
      householdSnapshot: {},
      requestContext: {},
      response: { slots: {} },
    },
    () => Promise.reject(new Error("lineage RPC is not deployed")),
  );

  assertEquals(slateId, undefined);
  assertEquals(warnings, [{
    message: "plan.dishes.persist_failed",
    fields: {
      request_id: "calibration-request",
      household_id: "11111111-1111-1111-1111-111111111111",
      surface: "calibration",
      detail: "lineage RPC is not deployed",
    },
  }]);
});

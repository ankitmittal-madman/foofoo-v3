import { assertEquals, assertNotEquals } from "@std/assert";
import { eligibleSetHash, extractDishSlateItems, snapshotHash } from "../plan/episodes.ts";

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

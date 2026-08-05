import { assertEquals, assertNotEquals } from "@std/assert";
import { eligibleSetHash, snapshotHash } from "../plan/episodes.ts";

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

import { assertEquals, assertStringIncludes } from "@std/assert";
import type { AppConfig } from "../_shared/config/config.ts";
import type { Logger } from "../_shared/logging/logger.ts";
import { buildAuxiliaryRequest, callAuxiliaryEngine } from "../recommendations/aux-client.ts";

const DISH_ID = "11111111-1111-4111-8111-111111111111";
const VERSION = `sha256:${"a".repeat(64)}`;

function logger(): Logger {
  const value: Logger = {
    debug() {},
    info() {},
    warn() {},
    error() {},
    child() {
      return value;
    },
  };
  return value;
}

function config(enabled = true): AppConfig {
  return {
    auxReMode: enabled ? "shadow" : "off",
    auxReServiceUrl: enabled ? "http://aux.local" : null,
    auxReServiceSecret: enabled ? "test-secret" : null,
  } as unknown as AppConfig;
}

Deno.test("Aux request carries household, history, class and governed context without dish facts", () => {
  const payload = buildAuxiliaryRequest(
    {
      household: {
        q3_home_state: "Maharashtra",
        q5_diet: "veg",
        q8_is_jain: true,
        q9_allergies: ["nuts"],
      },
      context: {
        slot: "lunch",
        date: "2026-08-10",
        pantry_ingredient_names: ["spinach"],
        governed_context_signals: [{ feature_code: "health_objective" }],
      },
      exclude_dish_names: ["Poha"],
      preference_by_dish: { "Palak Paneer": 0.8, Karela: -0.5 },
      preference_by_class: { LIGHT_VEG_ROTI: 0.4 },
      preference_by_direct_class: { LIGHT_VEG_ROTI: 0.9 },
      preference_by_projected_class: { LIGHT_VEG_ROTI: 0.2 },
    },
    "user-1",
    "household-1",
  );

  assertEquals(payload.meal_slot, "lunch");
  assertEquals(payload.restrictions, ["veg", "jain"]);
  assertEquals(payload.allergies, ["nuts"]);
  assertEquals(payload.preferences, ["Palak Paneer"]);
  assertEquals(payload.recent_meals, ["Poha"]);
  assertEquals(payload.preference_by_direct_class, { LIGHT_VEG_ROTI: 0.9 });
  assertEquals(payload.candidates, []);
});

Deno.test("signed Aux shadow call returns only canonical IDs from one publication", async () => {
  let sentBody = "";
  let sentSignature = "";
  const fetchImpl = (_url: string, init: RequestInit) => {
    sentBody = String(init.body);
    sentSignature = String((init.headers as Record<string, string>)["x-aux-signature"]);
    return Promise.resolve(
      new Response(
        JSON.stringify({
          auxiliary_result: {
            items: [{ id: DISH_ID }, { id: DISH_ID }, { id: "not-canonical" }],
          },
          model_metadata: { catalogue_publication: { version: VERSION } },
        }),
        { status: 200 },
      ),
    );
  };

  const result = await callAuxiliaryEngine(
    { household_id: "h" },
    "request-1",
    config(),
    logger(),
    fetchImpl,
    () => 1_700_000_000_000,
  );

  assertEquals(result.ok, true);
  if (!result.ok) throw new Error("expected Aux success");
  assertEquals(result.candidateIds, [DISH_ID]);
  assertEquals(result.publicationVersion, VERSION);
  assertStringIncludes(sentSignature, "t=1700000000,v1=");
  assertStringIncludes(sentBody, "household_id");
});

Deno.test("Aux shadow fails open on disabled configuration and malformed lineage", async () => {
  let calls = 0;
  const fetchImpl = () => {
    calls += 1;
    return Promise.resolve(
      new Response(
        JSON.stringify({
          auxiliary_result: { items: [{ id: DISH_ID }] },
          model_metadata: { catalogue_publication: { version: "wrong" } },
        }),
        { status: 200 },
      ),
    );
  };
  const disabled = await callAuxiliaryEngine(
    {},
    "request-1",
    config(false),
    logger(),
    fetchImpl,
  );
  assertEquals(disabled, { ok: false, reason: "disabled", latencyMs: 0 });
  assertEquals(calls, 0);

  const malformed = await callAuxiliaryEngine(
    {},
    "request-1",
    config(),
    logger(),
    fetchImpl,
  );
  assertEquals(malformed.ok, false);
  if (malformed.ok) throw new Error("expected malformed Aux response");
  assertEquals(malformed.reason, "bad_body");
});

Deno.test("Aux timeout aborts once and fails open without retrying", async () => {
  let calls = 0;
  const fetchImpl = (_url: string, init: RequestInit) => {
    calls += 1;
    return new Promise<Response>((_resolve, reject) => {
      init.signal?.addEventListener("abort", () => {
        reject(new DOMException("aborted", "AbortError"));
      });
    });
  };

  const result = await callAuxiliaryEngine(
    {},
    "request-timeout",
    config(),
    logger(),
    fetchImpl,
  );

  assertEquals(result.ok, false);
  if (result.ok) throw new Error("expected timeout");
  assertEquals(result.reason, "timeout");
  assertEquals(calls, 1);
});

Deno.test("Aux network failure makes one attempt and fails open", async () => {
  let calls = 0;
  const result = await callAuxiliaryEngine(
    {},
    "request-network",
    config(),
    logger(),
    () => {
      calls += 1;
      return Promise.reject(new TypeError("network unavailable"));
    },
  );

  assertEquals(result.ok, false);
  if (result.ok) throw new Error("expected network failure");
  assertEquals(result.reason, "network");
  assertEquals(calls, 1);
});

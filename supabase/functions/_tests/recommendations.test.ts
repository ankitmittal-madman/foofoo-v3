/**
 * Phase C tests — POST /v1/recommendations (the orchestration Edge Function that calls the RE).
 *
 * Covers, with an injected fake RE call / fake fetch (no live RE or GoTrue required):
 *   - successful call → 200, RE plates[]/contributions[] passed through as-is
 *   - timeout → fallback (valid 200 with a warning; NOT retried)
 *   - retry-then-succeed on a network-level failure (fetch throws once, then 200)
 *   - no retry on timeout (re-client)
 *   - schema-validation rejection of a malformed payload BEFORE it is sent (RE never called)
 * Mirrors the WP-8C test style (withEnv + injected fakes + assembled pipeline).
 */
import { assertEquals, assertStringIncludes } from "@std/assert";
import {
  API_ERRORS,
  authenticate,
  defineHandler,
  resetConfigCacheForTests,
} from "../_shared/mod.ts";
import type { AuthClaims, Logger } from "../_shared/mod.ts";
import { makeRecommendationsHandler, type RecommendationDeps } from "../recommendations/handler.ts";
import { callRecommendationEngine, type FetchLike } from "../recommendations/re-client.ts";
import type { HouseholdRaw } from "../recommendations/compose.ts";

const REQUIRED_ENV = {
  SUPABASE_URL: "http://localhost:54321",
  SUPABASE_ANON_KEY: "anon-test-key",
  SUPABASE_SERVICE_ROLE_KEY: "service-test-key",
  FOOFOO_ENV: "local",
};

function withEnv(vars: Record<string, string>, fn: () => void | Promise<void>) {
  const prev: Record<string, string | undefined> = {};
  for (const [k, v] of Object.entries(vars)) {
    prev[k] = Deno.env.get(k);
    Deno.env.set(k, v);
  }
  try {
    return fn();
  } finally {
    for (const k of Object.keys(vars)) {
      if (prev[k] === undefined) Deno.env.delete(k);
      else Deno.env.set(k, prev[k]!);
    }
    resetConfigCacheForTests();
  }
}

const USER_ID = "11111111-1111-1111-1111-111111111111";
const CFG = { gharReServiceUrl: "http://re.local", gharReServiceSecret: "s3cr3t" };

/** A no-op Logger for the re-client tests. */
function fakeLogger(): Logger {
  const l: Logger = {
    debug() {},
    info() {},
    warn() {},
    error() {},
    child() {
      return l;
    },
  };
  return l;
}

/** A valid ghar-re-v1 response body (what the RE would return for the stub household). */
function fakeReResponse(requestId: string) {
  return {
    request_id: requestId,
    api_version: "v1",
    engine_version: "1.0.0",
    config_version: "Config v1.0",
    plates: [
      {
        plate_id: "p1",
        form: "pair",
        hero_dish_ids: ["md5:Onion Pakora", "md5:Chole"],
        hero_dish_names: ["Onion Pakora", "Chole"],
        support: "Poori",
        is_standalone: false,
        plate_score: 6.9,
        base_total: 2.35,
        gain_multiplier: 1.21,
        final_score: 6.9,
        contributions: [
          { module: "m_palette", value: 0.4, weight: 1.0, confidence: 1.0 },
          { module: "m_weather", value: 1.0, weight: 0.4, confidence: 1.0 },
          { module: "sig", value: 0.6, weight: 0.3, confidence: 1.0 },
          { module: "prior_boost", value: 0.0, weight: 1.0, confidence: 1.0 },
        ],
      },
    ],
    warnings: [],
  };
}

/** Build the assembled production pipeline with a fake JWT verifier + injected RE deps. */
function pipeline(deps: RecommendationDeps) {
  const handler = makeRecommendationsHandler(deps);
  const verifier = () => Promise.resolve({ userId: USER_ID, role: "authenticated" } as AuthClaims);
  return defineHandler(handler, { middleware: [authenticate(verifier)] });
}

function post(body: unknown = {}) {
  return new Request("http://localhost/v1/recommendations", {
    method: "POST",
    headers: { Authorization: "Bearer good", "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

// ── 1. success → passthrough ────────────────────────────────────────────────────────────────────
Deno.test("POST /v1/recommendations success passes RE plates[]/contributions[] through as-is", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    let called = 0;
    const deps: RecommendationDeps = {
      callRe: (_payload, requestId) => {
        called++;
        return Promise.resolve({ ok: true, status: 200, body: fakeReResponse(requestId) });
      },
    };
    const res = await pipeline(deps)(post());
    assertEquals(res.status, 200);
    const json = await res.json();
    assertEquals(called, 1);
    assertEquals(json.engine_version, "1.0.0"); // not the fallback
    assertEquals(json.plates.length, 1);
    assertEquals(json.plates[0].contributions.length, 4); // passed through unchanged (>3 fixed fields)
    assertEquals(json.plates[0].hero_dish_names[0], "Onion Pakora");
    assertEquals(typeof json.trace_id, "string");
  });
});

// ── 2. timeout → fallback (no retry) ─────────────────────────────────────────────────────────────
Deno.test("POST /v1/recommendations timeout returns a fallback plate (valid 200, not retried)", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    let called = 0;
    const deps: RecommendationDeps = {
      callRe: () => {
        called++;
        return Promise.resolve({
          ok: false as const,
          kind: "timeout" as const,
          detail: "exceeded 2500ms",
        });
      },
    };
    const res = await pipeline(deps)(post());
    assertEquals(res.status, 200);
    const json = await res.json();
    assertEquals(called, 1); // timeout is NOT retried at the handler level
    assertEquals(json.engine_version, "fallback");
    assertEquals(json.plates.length, 1);
    assertEquals(json.plates[0].is_standalone, true);
    assertStringIncludes(json.warnings[0], "RE unavailable");
  });
});

// ── 3. retry-then-succeed on network failure (exercises re-client retry) ──────────────────────────
Deno.test("re-client retries ONCE on a network error then succeeds", async () => {
  let attempts = 0;
  const flakyFetch: FetchLike = (_url, _init) => {
    attempts++;
    if (attempts === 1) return Promise.reject(new TypeError("connection refused")); // network-level
    return Promise.resolve(new Response(JSON.stringify(fakeReResponse("req-1")), { status: 200 }));
  };
  const result = await callRecommendationEngine(
    { request_id: "req-1" },
    "req-1",
    CFG,
    fakeLogger(),
    {
      fetchImpl: flakyFetch,
    },
  );
  assertEquals(attempts, 2); // failed once, retried once
  assertEquals(result.ok, true);
  if (result.ok) assertEquals((result.body.plates as unknown[]).length, 1);
});

// ── 4. no retry on timeout ───────────────────────────────────────────────────────────────────────
Deno.test("re-client does NOT retry on timeout", async () => {
  let attempts = 0;
  const timingOutFetch: FetchLike = (_url, init) => {
    attempts++;
    // emulate an aborted fetch: reject with an AbortError when the signal fires
    return new Promise((_resolve, reject) => {
      init.signal?.addEventListener("abort", () => {
        const e = new Error("aborted");
        e.name = "AbortError";
        reject(e);
      });
    });
  };
  const result = await callRecommendationEngine({}, "req-2", CFG, fakeLogger(), {
    fetchImpl: timingOutFetch,
    timeoutMs: 20,
  });
  assertEquals(attempts, 1); // timeout → no retry
  assertEquals(result.ok, false);
  if (!result.ok) assertEquals(result.kind, "timeout");
});

// ── 5. schema-validation rejection BEFORE send ───────────────────────────────────────────────────
Deno.test("malformed composed payload is rejected before the RE is called (400, RE never hit)", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    let called = 0;
    // household loader returns an INVALID household (missing required q5_diet) to force a
    // contract-validation failure at the compose→validate step.
    const invalidHousehold = {
      q1_household_type: "couple",
      q2_working_professionals: 2,
      q3_home_state: "Delhi",
      q4_current_city: "Delhi",
      // q5_diet intentionally omitted → violates the contract
      q8_is_jain: false,
      q12_member_ages: [{ role: "adult", age: 30 }],
      q13_who_cooks: "self",
      q15_objective: "awesome_taste",
    } as unknown as HouseholdRaw;
    const deps: RecommendationDeps = {
      loadHousehold: () =>
        Promise.resolve({ household: invalidHousehold, householdId: "stub", stubbed: true }),
      callRe: () => {
        called++;
        return Promise.resolve({ ok: true as const, status: 200, body: fakeReResponse("x") });
      },
    };
    const res = await pipeline(deps)(post());
    assertEquals(res.status, API_ERRORS.ERR_VALIDATION_FAILED.httpStatus); // 400
    const json = await res.json();
    assertEquals(json.error.code, API_ERRORS.ERR_VALIDATION_FAILED.code);
    assertEquals(called, 0); // the RE was NEVER called — validation happened first
  });
});

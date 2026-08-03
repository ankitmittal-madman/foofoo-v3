/**
 * Phase C tests — POST /v1/recommendations (the orchestration Edge Function that calls the RE).
 *
 * Covers, with an injected fake RE call / fake fetch (no live RE or GoTrue required):
 *   - successful call → 200, RE plates[]/contributions[] passed through as-is
 *   - timeout → 503 retryable error, no guessed plate (WP-21); NOT retried at the handler level
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
import {
  allergenTokens,
  composeHouseholdRaw,
  type HouseholdRaw,
  memberRole,
  toMemberAge,
} from "../recommendations/compose.ts";

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

/**
 * A fixed, contract-valid household injected in place of the live Postgres read.
 *
 * These are ORCHESTRATION tests (does the handler call the RE, pass plates through, fall back on
 * timeout) — not data-access tests. Since Phase C.5 wired loadHouseholdRaw to real `public` tables,
 * leaving it un-injected would make every test below depend on a live database, which is exactly
 * the coupling the injectable-deps design exists to avoid.
 */
const TEST_HOUSEHOLD: HouseholdRaw = {
  q1_household_type: "couple",
  q2_working_professionals: 2,
  q3_home_state: "Delhi",
  q4_current_city: "Delhi",
  q5_diet: "veg",
  q6_nonveg_types: [],
  q7_veg_days: [],
  q8_is_jain: false,
  q9_allergies: [],
  q10_allergy_other: null,
  q11_conditions: [],
  q12_member_ages: [{ role: "adult", age: 32 }, { role: "adult", age: 30 }],
  q13_who_cooks: "self",
  q14_eat_out_per_week: 2,
  q15_objective: "awesome_taste",
};

/** Inject the fixed household above, so no test below touches a database. */
const loadTestHousehold = () =>
  Promise.resolve({ household: TEST_HOUSEHOLD, householdId: USER_ID, stubbed: false });

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
      loadHousehold: loadTestHousehold,
      recordEvent: () => Promise.resolve(),
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
Deno.test("POST /v1/recommendations timeout returns a retryable error, not a guessed plate", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    let called = 0;
    const deps: RecommendationDeps = {
      loadHousehold: loadTestHousehold,
      recordEvent: () => Promise.resolve(),
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
    assertEquals(res.status, 503);
    const json = await res.json();
    assertEquals(called, 1); // timeout is NOT retried at the handler level
    assertEquals(json.engine_version, "fallback");
    assertEquals(json.plates, undefined);
    assertEquals(json.error.code, "recommendation_engine_unavailable");
    assertStringIncludes(json.error.reason, "timeout");
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
      recordEvent: () => Promise.resolve(),
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

// ── 5b. ownership — a household_id the caller does not own is rejected before compose.ts runs ────
Deno.test("household_id owned by another user is rejected before loadHousehold/compose runs (403)", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    let loadCalled = 0;
    let reCalled = 0;
    let eventCalled = 0;
    const deps: RecommendationDeps = {
      loadHousehold: () => {
        loadCalled++;
        return Promise.resolve({ household: TEST_HOUSEHOLD, householdId: USER_ID, stubbed: false });
      },
      recordEvent: () => {
        eventCalled++;
        return Promise.resolve();
      },
      callRe: (_payload, requestId) => {
        reCalled++;
        return Promise.resolve({ ok: true as const, status: 200, body: fakeReResponse(requestId) });
      },
    };
    // The authenticated caller is USER_ID (see pipeline()'s fake verifier); this request asks for
    // a DIFFERENT household's data.
    const res = await pipeline(deps)(post({
      household_id: "22222222-2222-2222-2222-222222222222",
    }));
    assertEquals(res.status, API_ERRORS.ERR_OWNERSHIP_MISMATCH.httpStatus); // 403
    const json = await res.json();
    assertEquals(json.error.code, API_ERRORS.ERR_OWNERSHIP_MISMATCH.code);
    // Nothing downstream of the ownership check ran: no household load, no RE call, no event write.
    assertEquals(loadCalled, 0);
    assertEquals(reCalled, 0);
    assertEquals(eventCalled, 0);
  });
});

Deno.test("household_id equal to the caller's own id is allowed through", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const deps: RecommendationDeps = {
      loadHousehold: loadTestHousehold,
      recordEvent: () => Promise.resolve(),
      callRe: (_payload, requestId) =>
        Promise.resolve({ ok: true as const, status: 200, body: fakeReResponse(requestId) }),
    };
    const res = await pipeline(deps)(post({ household_id: USER_ID }));
    assertEquals(res.status, 200);
  });
});

Deno.test("omitting household_id defaults to the caller's own id and is allowed through", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const deps: RecommendationDeps = {
      loadHousehold: loadTestHousehold,
      recordEvent: () => Promise.resolve(),
      callRe: (_payload, requestId) =>
        Promise.resolve({ ok: true as const, status: 200, body: fakeReResponse(requestId) }),
    };
    const res = await pipeline(deps)(post());
    assertEquals(res.status, 200);
  });
});

// ── 5. Phase C.5 composition — live-table row shapes → contract-valid Q1–Q15 ─────────────────────
// These exercise the PURE mapping functions only (no Supabase client, no database): the row shapes
// they take are exactly what compose.ts selects from public.profiles / household_answers /
// household_members, so a drift between the migration and the mapping shows up here.
Deno.test("allergenTokens decodes the frozen 7-bit allergen model", () => {
  assertEquals(allergenTokens(0), []);
  assertEquals(allergenTokens(1), ["nuts"]);
  assertEquals(allergenTokens(2 | 4), ["dairy", "gluten"]);
  assertEquals(allergenTokens(64), ["sesame"]);
  // every bit set → all seven, in bit order
  assertEquals(allergenTokens(127), [
    "nuts",
    "dairy",
    "gluten",
    "shellfish",
    "egg",
    "soy",
    "sesame",
  ]);
});

Deno.test("memberRole maps the live conditions[] vocabulary to RE roles, strictest first", () => {
  assertEquals(memberRole([]), "adult");
  assertEquals(memberRole(["baby_6_18m"]), "weaning");
  assertEquals(memberRole(["toddler"]), "toddler");
  assertEquals(memberRole(["elderly_member"]), "senior");
  assertEquals(memberRole(["school_child"]), "child");
  assertEquals(memberRole(["teen_high_appetite"]), "teen");
  // a member carrying several tags resolves to the most food-safety-constraining one
  assertEquals(memberRole(["picky_child", "baby_6_18m"]), "weaning");
});

Deno.test("toMemberAge uses the real age when present and a role default when NULL", () => {
  assertEquals(toMemberAge({ age: 71, conditions: ["elderly_member"] }), {
    role: "senior",
    age: 71,
  });
  // age is nullable in the live schema (migration 038 does not fabricate one) — the role-derived
  // default keeps the payload contract-valid without inventing a specific user's age.
  assertEquals(toMemberAge({ age: null, conditions: ["baby_6_18m"] }), { role: "weaning", age: 1 });
  assertEquals(toMemberAge({ age: null, conditions: [] }), { role: "adult", age: 32 });
});

Deno.test("composeHouseholdRaw joins the three live sources into one contract payload", () => {
  const hh = composeHouseholdRaw(
    {
      id: USER_ID,
      home_state: "Gujarat",
      current_city: "Ahmedabad",
      diet_type: "veg",
      religious_pref: "jain",
      allergen_flags: 2, // dairy
    },
    {
      q1_household_type: "couple",
      q2_working_professionals: 2,
      q6_nonveg_types: [],
      q7_veg_days: [],
      q10_allergy_other: null,
      q11_conditions: [],
      q13_who_cooks: "self",
      q14_eat_out_per_week: 2,
      q15_objective: "healthy_living",
    },
    [{ age: 34, conditions: [] }, { age: 32, conditions: [] }],
  );
  assertEquals(hh.q3_home_state, "Gujarat"); // from profiles
  assertEquals(hh.q8_is_jain, true); // derived from religious_pref
  assertEquals(hh.q9_allergies, ["dairy"]); // derived from the bitfield
  assertEquals(hh.q15_objective, "healthy_living"); // from household_answers
  assertEquals(hh.q12_member_ages.length, 2); // from household_members
});

Deno.test("composeHouseholdRaw serves neutral defaults when onboarding is incomplete", () => {
  // A profile exists but household_answers does not yet — a half-onboarded user must still get a
  // usable payload rather than an error.
  const hh = composeHouseholdRaw(
    {
      id: USER_ID,
      home_state: "Delhi",
      current_city: "Delhi",
      diet_type: "non_veg",
      religious_pref: "all",
      allergen_flags: 0,
    },
    null,
    [],
  );
  assertEquals(hh.q5_diet, "non_veg"); // the real answer still wins where one exists
  assertEquals(hh.q15_objective, "awesome_taste"); // neutral default
  assertEquals(hh.q8_is_jain, false);
  assertEquals(hh.q12_member_ages, [{ role: "adult", age: 32 }]); // never an empty member list
});

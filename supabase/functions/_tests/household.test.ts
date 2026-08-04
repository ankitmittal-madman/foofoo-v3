/**
 * household/ tests — POST /v1/household, the onboarding write path.
 *
 * Same rigor as the requireOwnership fix in _tests/recommendations.test.ts: an ownership-mismatch
 * request must be rejected BEFORE any store function runs (assert every write-path function stays
 * uncalled, not just that the HTTP response is a 403). Mirrors that file's style — injected fakes,
 * `pipeline()` wiring a fake JWT verifier, no live database or GoTrue required.
 *
 * Two layers:
 *   - pure-function tests over schema.ts/store.ts (parseHouseholdWriteRequest, targetFor,
 *     buildHouseholdAnswersPatch, missingRequiredProfileFields) — no I/O, no HTTP;
 *   - HTTP tests through the assembled pipeline, using a small in-memory fake store shared across
 *     multiple calls to the SAME handler instance, so resume-after-partial-completion and
 *     repeat-call-after-creation can be tested as what they actually are: a sequence of real calls
 *     against consistent state, not isolated single-call assertions.
 */
import { assertEquals } from "@std/assert";
import {
  API_ERRORS,
  authenticate,
  defineHandler,
  resetConfigCacheForTests,
} from "../_shared/mod.ts";
import type { AuthClaims } from "../_shared/mod.ts";
import { type HouseholdDeps, makeHouseholdHandler } from "../household/handler.ts";
import { buildHouseholdAnswersPatch, missingRequiredProfileFields } from "../household/store.ts";
import {
  type MemberWrite,
  parseHouseholdWriteRequest,
  type ScreenAnswer,
  targetFor,
} from "../household/schema.ts";

const REQUIRED_ENV = {
  SUPABASE_URL: "http://localhost:54321",
  SUPABASE_ANON_KEY: "anon-test-key",
  SUPABASE_SERVICE_ROLE_KEY: "service-test-key",
  FOOFOO_ENV: "local",
};

async function withEnv(vars: Record<string, string>, fn: () => void | Promise<void>) {
  const prev: Record<string, string | undefined> = {};
  for (const [k, v] of Object.entries(vars)) {
    prev[k] = Deno.env.get(k);
    Deno.env.set(k, v);
  }
  try {
    return await fn();
  } finally {
    for (const k of Object.keys(vars)) {
      if (prev[k] === undefined) Deno.env.delete(k);
      else Deno.env.set(k, prev[k]!);
    }
    resetConfigCacheForTests();
  }
}

const USER_ID = "11111111-1111-1111-1111-111111111111";
const OTHER_USER_ID = "22222222-2222-2222-2222-222222222222";

function screen(questionKey: string, answerValue: unknown, skipped = false) {
  return {
    screen_id: `screen_${questionKey}`,
    question_key: questionKey,
    answer_value: answerValue,
    skipped,
  };
}

function post(body: unknown = {}) {
  return new Request("http://localhost/v1/household", {
    method: "POST",
    headers: { Authorization: "Bearer good", "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

/** Build the assembled production pipeline with a fake JWT verifier + injected deps. */
function pipeline(deps: HouseholdDeps) {
  const handler = makeHouseholdHandler(deps);
  const verifier = () => Promise.resolve({ userId: USER_ID, role: "authenticated" } as AuthClaims);
  return defineHandler(handler, { middleware: [authenticate(verifier)] });
}

// ---------------------------------------------------------------------------
// A small in-memory fake store — mirrors the REAL store.ts functions' signatures exactly, so it
// can be passed as HouseholdDeps and exercised across multiple calls with consistent state, the
// same way real Postgres rows persist across calls.
// ---------------------------------------------------------------------------
function fakeStore() {
  const sessions: { question_key: string; answer_value: unknown; skipped: boolean }[] = [];
  const answers: Record<string, unknown> = {};
  let profile: Record<string, unknown> | null = null;
  const members: MemberWrite[] = [];
  const calls = {
    insertScreens: 0,
    upsertAnswers: 0,
    loadAccumulated: 0,
    checkProfileExists: 0,
    upsertProfileRow: 0,
    upsertMembers: 0,
  };

  const deps: HouseholdDeps = {
    insertScreens: (_ctx, _id, screens: ScreenAnswer[]) => {
      calls.insertScreens++;
      for (const s of screens) {
        sessions.push({
          question_key: s.questionKey,
          answer_value: s.answerValue,
          skipped: s.skipped,
        });
      }
      return Promise.resolve();
    },
    upsertAnswers: (_ctx, _id, patch) => {
      calls.upsertAnswers++;
      Object.assign(answers, patch);
      return Promise.resolve();
    },
    loadAccumulated: (_ctx, _id) => {
      calls.loadAccumulated++;
      const acc: Record<string, unknown> = {};
      for (const s of sessions) {
        if (!s.skipped) acc[s.question_key] = s.answer_value;
      }
      return Promise.resolve(acc);
    },
    checkProfileExists: (_ctx, _id) => {
      calls.checkProfileExists++;
      return Promise.resolve(profile !== null);
    },
    upsertProfileRow: (_ctx, callerUserId, fields) => {
      calls.upsertProfileRow++;
      // Mirrors the real atomic upsert's semantics: only report `created` when no row existed yet.
      const created = profile === null;
      profile = { id: callerUserId, ...fields };
      return Promise.resolve(created);
    },
    upsertMembers: (_ctx, _id, memberList) => {
      calls.upsertMembers++;
      members.push(...memberList);
      return Promise.resolve(memberList.length);
    },
  };

  return { deps, calls, sessions, answers, members, getProfile: () => profile };
}

const COMPLETE_ANSWERS = [
  screen("primary_cook_name", "Meera"),
  screen("home_state", "MH"),
  screen("current_city", "Mumbai"),
  screen("diet_type", "veg"),
  screen("cook_capability", "intermediate"),
];

// ---------------------------------------------------------------------------
// 1. Ownership — the auth-fix rigor, applied to this endpoint
// ---------------------------------------------------------------------------
Deno.test("household_id owned by another user is rejected before ANY store function runs (403)", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const { deps, calls } = fakeStore();
    const res = await pipeline(deps)(post({
      household_id: OTHER_USER_ID,
      screens: [screen("primary_cook_name", "Someone Else")],
    }));
    assertEquals(res.status, API_ERRORS.ERR_OWNERSHIP_MISMATCH.httpStatus); // 403
    const json = await res.json();
    assertEquals(json.error.code, API_ERRORS.ERR_OWNERSHIP_MISMATCH.code);
    // Nothing downstream of the ownership check ran — same assertion pattern as the
    // recommendations auth fix: every write-path function stayed at zero calls.
    assertEquals(calls.insertScreens, 0);
    assertEquals(calls.upsertAnswers, 0);
    assertEquals(calls.loadAccumulated, 0);
    assertEquals(calls.checkProfileExists, 0);
    assertEquals(calls.upsertProfileRow, 0);
    assertEquals(calls.upsertMembers, 0);
  });
});

Deno.test("household_id equal to the caller's own id is allowed through", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const { deps, calls } = fakeStore();
    const res = await pipeline(deps)(
      post({ household_id: USER_ID, screens: [screen("primary_cook_name", "Meera")] }),
    );
    assertEquals(res.status, 200);
    assertEquals(calls.insertScreens, 1);
  });
});

Deno.test("omitting household_id defaults to the caller's own id and is allowed through", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const { deps, calls } = fakeStore();
    const res = await pipeline(deps)(post({ screens: [screen("current_city", "Pune")] }));
    assertEquals(res.status, 200);
    assertEquals(calls.insertScreens, 1);
  });
});

// ---------------------------------------------------------------------------
// 2. No fabricated defaults — profile is never created with a missing required field
// ---------------------------------------------------------------------------
Deno.test("profile is NOT created while a required field is still missing (no fabricated default)", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const { deps, calls, getProfile } = fakeStore();
    // 4 of 5 required fields — cook_capability deliberately withheld.
    const res = await pipeline(deps)(post({
      screens: [
        screen("primary_cook_name", "Meera"),
        screen("home_state", "MH"),
        screen("current_city", "Mumbai"),
        screen("diet_type", "veg"),
      ],
    }));
    assertEquals(res.status, 200);
    const json = await res.json();
    assertEquals(json.profile_created, false);
    assertEquals(json.profile_exists, false);
    assertEquals(json.missing_required_fields, ["cook_capability"]);
    assertEquals(calls.upsertProfileRow, 0); // never called — no value was invented
    assertEquals(getProfile(), null);
  });
});

// ---------------------------------------------------------------------------
// 3. Resume-after-partial-completion — the multi-call scenario the scoping note called for
// ---------------------------------------------------------------------------
Deno.test("a household can be created across multiple calls (resume-after-partial-completion)", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const { deps, calls, getProfile } = fakeStore();
    const app = pipeline(deps);

    // Call 1: two of five required fields.
    const r1 = await app(
      post({ screens: [screen("primary_cook_name", "Meera"), screen("home_state", "MH")] }),
    );
    assertEquals(r1.status, 200);
    const j1 = await r1.json();
    assertEquals(j1.profile_created, false);
    assertEquals(j1.missing_required_fields.sort(), [
      "cook_capability",
      "current_city",
      "diet_type",
    ]);

    // Call 2: two more (a DIFFERENT session/screen than call 1 — resume, not a repeat).
    const r2 = await app(
      post({ screens: [screen("current_city", "Mumbai"), screen("diet_type", "veg")] }),
    );
    const j2 = await r2.json();
    assertEquals(j2.profile_created, false);
    assertEquals(j2.missing_required_fields, ["cook_capability"]);
    assertEquals(calls.upsertProfileRow, 0); // still not created — 4 of 5 known

    // Call 3: the final field completes the set.
    const r3 = await app(post({ screens: [screen("cook_capability", "intermediate")] }));
    const j3 = await r3.json();
    assertEquals(j3.profile_created, true);
    assertEquals(j3.profile_exists, true);
    assertEquals(j3.missing_required_fields, []);
    assertEquals(calls.upsertProfileRow, 1);

    const profile = getProfile() as Record<string, unknown>;
    assertEquals(profile.id, USER_ID); // claims.userId, not anything client-supplied
    assertEquals(profile.primary_cook_name, "Meera");
    assertEquals(profile.home_state, "MH");
    assertEquals(profile.current_city, "Mumbai");
    assertEquals(profile.diet_type, "veg");
    assertEquals(profile.cook_capability, "intermediate");
    // onboarding_completed previously stayed false forever (never set anywhere) — all five
    // required fields being known on this call is the moment onboarding actually completes.
    assertEquals(profile.onboarding_completed, true);
  });
});

// ---------------------------------------------------------------------------
// 4. Repeat call after profile already exists — updates rather than duplicates
// ---------------------------------------------------------------------------
Deno.test("a repeat call after the profile already exists does not re-create it", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const { deps, calls } = fakeStore();
    const app = pipeline(deps);

    await app(post({ screens: COMPLETE_ANSWERS }));
    assertEquals(calls.upsertProfileRow, 1);

    // Repeat the SAME complete payload again — must not create a second profile.
    const res = await app(post({ screens: COMPLETE_ANSWERS }));
    const json = await res.json();
    assertEquals(res.status, 200);
    assertEquals(json.profile_created, false); // already existed BEFORE this call
    assertEquals(json.profile_exists, true);
    assertEquals(calls.upsertProfileRow, 1); // still exactly one, never two
  });
});

Deno.test("members can be written on a later call once the profile exists", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const { deps, calls, members } = fakeStore();
    const app = pipeline(deps);

    await app(post({ screens: COMPLETE_ANSWERS }));
    const res = await app(post({
      members: [{ member_name: "Baby Aarav", conditions: ["baby_6_18m"] }],
    }));
    const json = await res.json();
    assertEquals(res.status, 200);
    assertEquals(json.members_written, 1);
    assertEquals(calls.upsertMembers, 1);
    assertEquals(members[0].memberName, "Baby Aarav");
  });
});

// ---------------------------------------------------------------------------
// 5. household_members before a profile exists — clean 422, not a raw FK-violation 500
// ---------------------------------------------------------------------------
Deno.test("household_members supplied before the profile exists is rejected (422), upsertMembers never called", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const { deps, calls } = fakeStore();
    const res = await pipeline(deps)(post({
      screens: [screen("primary_cook_name", "Meera")], // incomplete on purpose
      members: [{ member_name: "Someone" }],
    }));
    assertEquals(res.status, API_ERRORS.ERR_HOUSEHOLD_INCOMPLETE.httpStatus); // 422
    const json = await res.json();
    assertEquals(json.error.code, API_ERRORS.ERR_HOUSEHOLD_INCOMPLETE.code);
    assertEquals(calls.upsertMembers, 0);
  });
});

// ---------------------------------------------------------------------------
// 6. Structural / semantic validation (schema.ts, pure — no I/O)
// ---------------------------------------------------------------------------
Deno.test("targetFor resolves household_answers keys, profiles keys, and rejects unknown keys", () => {
  assertEquals(targetFor("q1_household_type"), "household_answers");
  assertEquals(targetFor("q15_objective"), "household_answers");
  assertEquals(targetFor("home_state"), "profiles");
  assertEquals(targetFor("cook_capability"), "profiles");
  assertEquals(targetFor("q8_is_jain"), null); // derived, not a raw writable key
  assertEquals(targetFor("q12_member_ages"), null); // members[] instead
  assertEquals(targetFor("not_a_real_field"), null);
});

Deno.test("parseHouseholdWriteRequest rejects a structurally malformed body (400)", () => {
  let threw = false;
  try {
    parseHouseholdWriteRequest({ screens: "not an array" });
  } catch (e) {
    threw = true;
    assertEquals((e as { code: string }).code, API_ERRORS.ERR_VALIDATION_FAILED.code);
  }
  assertEquals(threw, true);
});

Deno.test("parseHouseholdWriteRequest rejects an unrecognized question_key (422)", () => {
  let threw = false;
  try {
    parseHouseholdWriteRequest({ screens: [screen("children_ages", ["3", "7"])] }); // legacy vocabulary
  } catch (e) {
    threw = true;
    assertEquals((e as { code: string }).code, API_ERRORS.ERR_HOUSEHOLD_FIELD_INVALID.code);
  }
  assertEquals(threw, true);
});

Deno.test("parseHouseholdWriteRequest rejects an answer_value outside its field's vocabulary (422)", () => {
  let threw = false;
  try {
    parseHouseholdWriteRequest({ screens: [screen("q15_objective", "not_a_real_objective")] });
  } catch (e) {
    threw = true;
    assertEquals((e as { code: string }).code, API_ERRORS.ERR_HOUSEHOLD_FIELD_INVALID.code);
  }
  assertEquals(threw, true);
});

Deno.test("a skipped screen's answer_value is not validated", () => {
  // "skipped" means asked-not-answered; the malformed value here must not throw.
  const parsed = parseHouseholdWriteRequest({
    screens: [screen("q15_objective", "garbage-value-nobody-checks", true)],
  });
  assertEquals(parsed.screens[0].skipped, true);
});

Deno.test("parseHouseholdWriteRequest rejects a member condition outside the 15-value vocabulary", () => {
  let threw = false;
  try {
    parseHouseholdWriteRequest({ members: [{ conditions: ["not_a_real_condition"] }] });
  } catch (e) {
    threw = true;
    assertEquals((e as { code: string }).code, API_ERRORS.ERR_HOUSEHOLD_FIELD_INVALID.code);
  }
  assertEquals(threw, true);
});

Deno.test("buildHouseholdAnswersPatch keeps only non-skipped household_answers-targeted screens", () => {
  const parsed = parseHouseholdWriteRequest({
    screens: [
      screen("q15_objective", "awesome_taste"), // household_answers
      screen("home_state", "MH"), // profiles — excluded
      screen("q13_who_cooks", "self", true), // skipped — excluded
    ],
  });
  const patch = buildHouseholdAnswersPatch(parsed.screens);
  assertEquals(patch, { q15_objective: "awesome_taste" });
});

Deno.test("missingRequiredProfileFields reports exactly the unknown required fields", () => {
  assertEquals(
    missingRequiredProfileFields({ primary_cook_name: "Meera", home_state: "MH" }).sort(),
    ["cook_capability", "current_city", "diet_type"],
  );
  assertEquals(
    missingRequiredProfileFields({
      primary_cook_name: "Meera",
      home_state: "MH",
      current_city: "Mumbai",
      diet_type: "veg",
      cook_capability: "beginner",
    }),
    [],
  );
});

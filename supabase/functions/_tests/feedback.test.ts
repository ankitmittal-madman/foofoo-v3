/**
 * WP-15 feedback tests (POST /v1/feedback) — the instrumentation prerequisite WP-14 identified
 * for the Core Spine's `w_pref·S_pref` term. Covers validation, the assembled pipeline with an
 * injected fake `recordEvent` (no live database or GoTrue required), and error propagation from
 * events.ts's ownership/ not-found checks. Mirrors the consent.test.ts / recommendations.test.ts
 * style (withEnv + injected fakes + assembled pipeline).
 */
import { assertEquals, assertObjectMatch, assertThrows } from "@std/assert";
import {
  API_ERRORS,
  authenticate,
  defineHandler,
  FEEDBACK_EVENT_TYPES,
  parseFeedbackRequest,
  resetConfigCacheForTests,
} from "../_shared/mod.ts";
import type { AuthClaims } from "../_shared/mod.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { feedbackAllowedRoles, makeFeedbackHandler } from "../feedback/handler.ts";
import { slateItemMatchesDish } from "../feedback/events.ts";
import type { FeedbackEventInput, FeedbackEventResult } from "../feedback/events.ts";

const REQUIRED_ENV = {
  SUPABASE_URL: "http://localhost:54321",
  SUPABASE_ANON_KEY: "anon-test-key",
  SUPABASE_SERVICE_ROLE_KEY: "service-test-key",
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
const REQUEST_ID = "22222222-2222-2222-2222-222222222222";

function validBody(overrides: Record<string, unknown> = {}) {
  return {
    request_id: REQUEST_ID,
    event_type: "like",
    dish_name: "Masala Dosa",
    slot: "breakfast",
    ...overrides,
  };
}

// ── Validation ────────────────────────────────────────────────────────────────────────────────

Deno.test("parseFeedbackRequest accepts a well-formed body", () => {
  const req = parseFeedbackRequest(validBody());
  assertEquals(req.requestId, REQUEST_ID);
  assertEquals(req.eventType, "like");
  assertEquals(req.dishName, "Masala Dosa");
  assertEquals(req.schemaVersion, "1");
});

Deno.test("parseFeedbackRequest accepts canonical meal-class interaction v2", () => {
  const req = parseFeedbackRequest({
    schema_version: "2",
    idempotency_key: "weekly-1:event-1",
    request_id: REQUEST_ID,
    event_type: "selected",
    target: {
      type: "meal_class",
      id: "LD_DAL_ROTI",
      identity_status: "resolved",
      display_name: "Dal + Roti",
    },
    moment: {
      occurred_at: "2026-08-07T10:00:00.000Z",
      local_timezone: "Asia/Kolkata",
      intended_meal_date: "2026-08-12",
      meal_slot: "lunch",
      weekday: "Wednesday",
      day_type: "weekday",
    },
    evidence: { kind: "explicit", source_surface: "weekly_plan", shown_rank: 2 },
    versions: { catalog: "catalogue-v1", config: "config-v1", feature: "event-v2" },
  });
  assertEquals(req.schemaVersion, "2");
  assertEquals(req.target?.id, "LD_DAL_ROTI");
  assertEquals(req.moment?.intendedMealDate, "2026-08-12");
});

Deno.test("parseFeedbackRequest rejects incomplete or forged v2 evidence", () => {
  assertEquals(
    assertThrows(() => parseFeedbackRequest({ ...validBody(), schema_version: "2" }), AppError)
      .httpStatus,
    400,
  );
  assertEquals(
    assertThrows(() =>
      parseFeedbackRequest({
        ...validBody(),
        schema_version: "2",
        idempotency_key: "event-1",
        target: { type: "dish", id: "dish-1", identity_status: "unresolved" },
        moment: {
          occurred_at: "2026-08-07T10:00:00.000Z",
          local_timezone: "Asia/Kolkata",
          meal_slot: "breakfast",
        },
        evidence: { kind: "inferred", source_surface: "weekly_plan" },
      }), AppError).httpStatus,
    400,
  );
});

Deno.test("served dish feedback resolves both dish-card and episode decision traces", () => {
  assertEquals(
    slateItemMatchesDish(
      { dish_name: "Poha Jalebi (Indori)", dish_snapshot: { name: "Poha Jalebi (Indori)" } },
      "poha jalebi (indori)",
    ),
    true,
  );
  assertEquals(
    slateItemMatchesDish(
      { episode_snapshot: { components: [{ dish_name: "Daal Bafla" }] } },
      "Daal Bafla",
    ),
    true,
  );
  assertEquals(slateItemMatchesDish({}, "Daal Bafla"), false);
});

Deno.test("parseFeedbackRequest accepts a body with no dish_name (e.g. 'accept' the whole plate)", () => {
  const req = parseFeedbackRequest({ request_id: REQUEST_ID, event_type: "accept" });
  assertEquals(req.dishName, undefined);
});

Deno.test("parseFeedbackRequest rejects a missing request_id (400)", () => {
  const body = validBody();
  // deno-lint-ignore no-explicit-any
  delete (body as any).request_id;
  const e = assertThrows(() => parseFeedbackRequest(body), AppError);
  assertEquals(e.code, API_ERRORS.ERR_VALIDATION_FAILED.code);
  assertEquals(e.httpStatus, 400);
});

Deno.test("parseFeedbackRequest rejects an empty request_id (400)", () => {
  const e = assertThrows(
    () => parseFeedbackRequest(validBody({ request_id: "" })),
    AppError,
  );
  assertEquals(e.httpStatus, 400);
});

Deno.test("parseFeedbackRequest rejects an unknown event_type with ERR_FEEDBACK_EVENT_TYPE_INVALID (422)", () => {
  const e = assertThrows(
    () => parseFeedbackRequest(validBody({ event_type: "super_like" })),
    AppError,
  );
  assertEquals(e.code, API_ERRORS.ERR_FEEDBACK_EVENT_TYPE_INVALID.code);
  assertEquals(e.httpStatus, 422);
});

Deno.test("FEEDBACK_EVENT_TYPES matches the feedback_events CHECK constraint (migration 092)", () => {
  assertEquals(
    [...FEEDBACK_EVENT_TYPES].sort(),
    [
      "accept",
      "add_to_date",
      "completed",
      "cooked",
      "dislike",
      "edit",
      "like",
      "lock",
      "make_this",
      "member_objection",
      "missing_ingredient",
      "never",
      "not_today",
      "opened",
      "ordered",
      "regretted",
      "replaced",
      "search",
      "selected",
      "shown_not_tapped",
      "swap",
      "too_much_work",
      "unlock",
    ].sort(),
  );
});

// ── Assembled pipeline (authenticate → handler → injected recordEvent) ──────────────────────────

function fakeRecordEvent(
  result: FeedbackEventResult | (() => never),
): (ctx: unknown, ev: FeedbackEventInput) => Promise<FeedbackEventResult> {
  return (_ctx, _ev) => {
    if (typeof result === "function") result();
    return Promise.resolve(result as FeedbackEventResult);
  };
}

function buildPipeline(recordEvent: ReturnType<typeof fakeRecordEvent>) {
  const handler = makeFeedbackHandler({
    recordEvent,
    authorizeHousehold: () => Promise.resolve("owner"),
  });
  const verifier = () => Promise.resolve({ userId: USER_ID, role: "authenticated" } as AuthClaims);
  return defineHandler(handler, { middleware: [authenticate(verifier)] });
}

Deno.test("POST /v1/feedback happy path returns 201 with contract-shaped body", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    let seenInput: FeedbackEventInput | undefined;
    const recordEvent = (_ctx: unknown, ev: FeedbackEventInput) => {
      seenInput = ev;
      return Promise.resolve({
        id: "33333333-3333-3333-3333-333333333333",
        createdAt: "2026-08-02T00:00:00.000Z",
        dishResolved: true,
      });
    };
    const pipeline = buildPipeline(recordEvent);
    const req = new Request("http://localhost/v1/feedback", {
      method: "POST",
      headers: { Authorization: "Bearer good", "content-type": "application/json" },
      body: JSON.stringify(validBody()),
    });
    const res = await pipeline(req);
    assertEquals(res.status, 201);
    const json = await res.json();
    assertObjectMatch(json, { event_type: "like" });
    assertEquals(typeof json.id, "string");
    assertEquals(typeof json.trace_id, "string");
    // profile_id passed to the writer is the JWT user_id, never a client-supplied field —
    // feedback is always about the caller's own recommendation, so there is nothing to spoof.
    assertEquals(seenInput?.actorProfileId, USER_ID);
    assertEquals(seenInput?.householdId, USER_ID);
    assertEquals(seenInput?.requestId, REQUEST_ID);
  });
});

Deno.test("POST /v1/feedback returns 422 for an unknown event_type before recordEvent is ever called", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const recordEvent = fakeRecordEvent(() => {
      throw new Error("recordEvent must not be called when validation fails");
    });
    const pipeline = buildPipeline(recordEvent);
    const req = new Request("http://localhost/v1/feedback", {
      method: "POST",
      headers: { Authorization: "Bearer good", "content-type": "application/json" },
      body: JSON.stringify(validBody({ event_type: "super_like" })),
    });
    const res = await pipeline(req);
    assertEquals(res.status, 422);
    const json = await res.json();
    assertEquals(json.error.code, API_ERRORS.ERR_FEEDBACK_EVENT_TYPE_INVALID.code);
  });
});

Deno.test("POST /v1/feedback propagates ERR_RECOMMENDATION_EVENT_NOT_FOUND (404) from the writer", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const recordEvent = () =>
      Promise.reject(
        new AppError(API_ERRORS.ERR_RECOMMENDATION_EVENT_NOT_FOUND, {
          context: { request_id: REQUEST_ID },
        }),
      );
    const pipeline = buildPipeline(recordEvent);
    const req = new Request("http://localhost/v1/feedback", {
      method: "POST",
      headers: { Authorization: "Bearer good", "content-type": "application/json" },
      body: JSON.stringify(validBody()),
    });
    const res = await pipeline(req);
    assertEquals(res.status, 404);
    const json = await res.json();
    assertEquals(json.error.code, API_ERRORS.ERR_RECOMMENDATION_EVENT_NOT_FOUND.code);
  });
});

Deno.test("POST /v1/feedback propagates ERR_OWNERSHIP_MISMATCH (403) when the recommendation_event belongs to another profile", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const recordEvent = () =>
      Promise.reject(
        new AppError(API_ERRORS.ERR_OWNERSHIP_MISMATCH, {
          detail: "recommendation_event belongs to a different profile",
        }),
      );
    const pipeline = buildPipeline(recordEvent);
    const req = new Request("http://localhost/v1/feedback", {
      method: "POST",
      headers: { Authorization: "Bearer good", "content-type": "application/json" },
      body: JSON.stringify(validBody()),
    });
    const res = await pipeline(req);
    assertEquals(res.status, 403);
  });
});

Deno.test("POST /v1/feedback returns 401 when unauthenticated", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const handler = makeFeedbackHandler({
      recordEvent: fakeRecordEvent(() => {
        throw new Error("must not be called");
      }),
      authorizeHousehold: () => Promise.resolve("owner"),
    });
    const pipeline = defineHandler(handler, {
      middleware: [authenticate(() => Promise.reject(new Error("no token")))],
    });
    const req = new Request("http://localhost/v1/feedback", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(validBody()),
    });
    const res = await pipeline(req);
    assertEquals(res.status, 401);
  });
});

Deno.test("feedback role matrix keeps viewers read-only and plan control owner/planner-only", () => {
  assertEquals(feedbackAllowedRoles("lock"), ["owner", "planner"]);
  assertEquals(feedbackAllowedRoles("selected"), ["owner", "planner"]);
  assertEquals(feedbackAllowedRoles("missing_ingredient"), ["owner", "planner", "cook"]);
  assertEquals(feedbackAllowedRoles("like"), ["owner", "planner", "cook", "member"]);
});

Deno.test("POST /v1/feedback forwards a selected household separately from actor identity", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const householdId = "44444444-4444-4444-4444-444444444444";
    let seenInput: FeedbackEventInput | undefined;
    const handler = makeFeedbackHandler({
      authorizeHousehold: (_ctx, selected, actor) => {
        assertEquals(selected, householdId);
        assertEquals(actor, USER_ID);
        return Promise.resolve("member");
      },
      recordEvent: (_ctx, input) => {
        seenInput = input;
        return Promise.resolve({
          id: "33333333-3333-3333-3333-333333333333",
          createdAt: "2026-08-02T00:00:00.000Z",
          dishResolved: true,
        });
      },
    });
    const pipeline = defineHandler(handler, {
      middleware: [authenticate(() =>
        Promise.resolve({
          userId: USER_ID,
          role: "authenticated",
        } as AuthClaims)
      )],
    });
    const res = await pipeline(
      new Request("http://localhost/v1/feedback", {
        method: "POST",
        headers: { Authorization: "Bearer good", "content-type": "application/json" },
        body: JSON.stringify(validBody({ household_id: householdId, event_type: "like" })),
      }),
    );
    assertEquals(res.status, 201);
    assertEquals(seenInput?.actorProfileId, USER_ID);
    assertEquals(seenInput?.householdId, householdId);
  });
});

Deno.test("member cannot perform planner-only feedback actions", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    let recordCalled = false;
    const handler = makeFeedbackHandler({
      authorizeHousehold: () => Promise.resolve("member"),
      recordEvent: () => {
        recordCalled = true;
        return Promise.resolve({ id: "x", createdAt: "now", dishResolved: false });
      },
    });
    const pipeline = defineHandler(handler, {
      middleware: [authenticate(() =>
        Promise.resolve({
          userId: USER_ID,
          role: "authenticated",
        } as AuthClaims)
      )],
    });
    const res = await pipeline(
      new Request("http://localhost/v1/feedback", {
        method: "POST",
        headers: { Authorization: "Bearer good", "content-type": "application/json" },
        body: JSON.stringify(validBody({ event_type: "lock" })),
      }),
    );
    assertEquals(res.status, 403);
    assertEquals(recordCalled, false);
  });
});

Deno.test("POST /v1/feedback returns 405 for a non-POST method", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const pipeline = buildPipeline(
      fakeRecordEvent(() => {
        throw new Error("must not be called");
      }),
    );
    const req = new Request("http://localhost/v1/feedback", {
      method: "GET",
      headers: { Authorization: "Bearer good" },
    });
    const res = await pipeline(req);
    assertEquals(res.status, 405);
  });
});

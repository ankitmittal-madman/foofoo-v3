/**
 * WP-8C consent tests (POST /v1/consent, LF-M01, DOC-P3-06 §06.1).
 *
 * Covers the layers independently (validation, authorization, JWT middleware, service) and then
 * the assembled pipeline end-to-end with a fake JWT verifier and a fake repository — so no live
 * GoTrue or database is required. Mirrors the WP-8B test style (withEnv + injected fakes).
 */
import { assertEquals, assertObjectMatch, assertRejects, assertThrows } from "@std/assert";
import {
  API_ERRORS,
  AppError,
  authenticate,
  buildContext,
  ConsentService,
  defineHandler,
  parseConsentRequest,
  requireOwnership,
  resetConfigCacheForTests,
} from "../_shared/mod.ts";
import type {
  AuthClaims,
  ConsentRequest,
  IConsentRepository,
  RecordedConsent,
} from "../_shared/mod.ts";
import type { ConsentInsertRow } from "../_shared/mod.ts";
import { makeConsentHandler } from "../consent/handler.ts";

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

function validBody(profileId = USER_ID) {
  return {
    profile_id: profileId,
    consents: [
      { consent_type: "personalization", granted: true },
      { consent_type: "analytics", granted: false },
    ],
    privacy_policy_version: "2026-07-01",
  };
}

/** Fake repository: echoes inserted rows back as recorded consents with a fixed granted_at. */
function fakeRepo(): IConsentRepository {
  return {
    insertConsents(rows: ConsentInsertRow[]): Promise<RecordedConsent[]> {
      return Promise.resolve(
        rows.map((r) => ({
          consent_type: r.consent_type,
          granted: r.granted,
          granted_at: "2026-07-14T00:00:00.000Z",
        })),
      );
    },
  };
}

// ── Validation ────────────────────────────────────────────────────────────────────────────────

Deno.test("parseConsentRequest accepts a well-formed body", () => {
  const req = parseConsentRequest(validBody());
  assertEquals(req.profileId, USER_ID);
  assertEquals(req.consents.length, 2);
  assertEquals(req.consents[0].consentType, "personalization");
});

Deno.test("parseConsentRequest rejects a missing profile_id with ERR_VALIDATION_FAILED (400)", () => {
  const body = validBody();
  // deno-lint-ignore no-explicit-any
  delete (body as any).profile_id;
  const e = assertThrows(() => parseConsentRequest(body), AppError);
  assertEquals(e.code, API_ERRORS.ERR_VALIDATION_FAILED.code);
  assertEquals(e.httpStatus, 400);
});

Deno.test("parseConsentRequest rejects an empty consents array (400)", () => {
  const body = { ...validBody(), consents: [] };
  const e = assertThrows(() => parseConsentRequest(body), AppError);
  assertEquals(e.httpStatus, 400);
});

Deno.test("parseConsentRequest rejects a non-boolean granted (400)", () => {
  const body = {
    ...validBody(),
    consents: [{ consent_type: "personalization", granted: "yes" }],
  };
  const e = assertThrows(() => parseConsentRequest(body), AppError);
  assertEquals(e.code, API_ERRORS.ERR_VALIDATION_FAILED.code);
});

Deno.test("parseConsentRequest rejects an unknown consent_type with ERR_CONSENT_TYPE_INVALID (422)", () => {
  const body = {
    ...validBody(),
    consents: [{ consent_type: "marketing", granted: true }],
  };
  const e = assertThrows(() => parseConsentRequest(body), AppError);
  assertEquals(e.code, API_ERRORS.ERR_CONSENT_TYPE_INVALID.code);
  assertEquals(e.httpStatus, 422);
});

// ── Authorization ─────────────────────────────────────────────────────────────────────────────

Deno.test("requireOwnership passes when JWT user_id matches the resource owner", () => {
  const claims: AuthClaims = { userId: USER_ID, role: "authenticated" };
  requireOwnership(claims, USER_ID); // no throw
});

Deno.test("requireOwnership throws ERR_OWNERSHIP_MISMATCH (403) on mismatch", () => {
  const claims: AuthClaims = { userId: USER_ID, role: "authenticated" };
  const e = assertThrows(
    () => requireOwnership(claims, "22222222-2222-2222-2222-222222222222"),
    AppError,
  );
  assertEquals(e.code, API_ERRORS.ERR_OWNERSHIP_MISMATCH.code);
  assertEquals(e.httpStatus, 403);
});

// ── authenticate() middleware ─────────────────────────────────────────────────────────────────

Deno.test("authenticate attaches verified claims to the context", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const verifier = (_jwt: string, _cfg: unknown) =>
      Promise.resolve({ userId: USER_ID, role: "authenticated" } as AuthClaims);
    let seen: AuthClaims | undefined;
    const wrapped = authenticate(verifier)((_req, ctx) => {
      seen = ctx.claims;
      return new Response("ok");
    });
    const req = new Request("http://localhost/v1/consent", {
      headers: { Authorization: "Bearer good-token" },
    });
    await wrapped(req, buildContext(req));
    assertEquals(seen?.userId, USER_ID);
  });
});

Deno.test("authenticate throws ERR_UNAUTHENTICATED (401) when the bearer header is missing", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const wrapped = authenticate(() => Promise.reject(new Error("unused")))(() =>
      new Response("ok")
    );
    const req = new Request("http://localhost/v1/consent");
    const e = await assertRejects(() => Promise.resolve(wrapped(req, buildContext(req))), AppError);
    assertEquals(e.code, API_ERRORS.ERR_UNAUTHENTICATED.code);
  });
});

Deno.test("authenticate throws ERR_UNAUTHENTICATED (401) when the verifier rejects", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const wrapped = authenticate(() => Promise.reject(new Error("bad signature")))(() =>
      new Response("ok")
    );
    const req = new Request("http://localhost/v1/consent", {
      headers: { Authorization: "Bearer forged" },
    });
    const e = await assertRejects(() => Promise.resolve(wrapped(req, buildContext(req))), AppError);
    assertEquals(e.code, API_ERRORS.ERR_UNAUTHENTICATED.code);
    assertEquals(e.httpStatus, 401);
  });
});

// ── ConsentService (LF-M01) ───────────────────────────────────────────────────────────────────

Deno.test("captureConsent records rows and resolves personalization_granted = true", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const req = new Request("http://localhost/v1/consent");
    const svc = new ConsentService(buildContext(req), fakeRepo());
    const request: ConsentRequest = {
      profileId: USER_ID,
      consents: [
        { consentType: "personalization", granted: true },
        { consentType: "data_retention", granted: true },
      ],
      privacyPolicyVersion: "2026-07-01",
    };
    const res = await svc.captureConsent(request, null);
    assertEquals(res.recorded.length, 2);
    assertEquals(res.personalization_granted, true);
  });
});

Deno.test("captureConsent resolves personalization_granted = false when personalization denied", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const req = new Request("http://localhost/v1/consent");
    const svc = new ConsentService(buildContext(req), fakeRepo());
    const request: ConsentRequest = {
      profileId: USER_ID,
      consents: [{ consentType: "personalization", granted: false }],
      privacyPolicyVersion: "2026-07-01",
    };
    const res = await svc.captureConsent(request, null);
    assertEquals(res.personalization_granted, false);
  });
});

Deno.test("captureConsent resolves personalization_granted = false when personalization absent", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const req = new Request("http://localhost/v1/consent");
    const svc = new ConsentService(buildContext(req), fakeRepo());
    const request: ConsentRequest = {
      profileId: USER_ID,
      consents: [{ consentType: "analytics", granted: true }],
      privacyPolicyVersion: "2026-07-01",
    };
    const res = await svc.captureConsent(request, null);
    assertEquals(res.personalization_granted, false);
  });
});

// ── Assembled pipeline (authenticate → handler → service) ───────────────────────────────────────

/** Full production pipeline: infra (error-boundary/logging) → authenticate → handler → fake svc. */
function buildPipeline(verifier: (jwt: string, cfg: unknown) => Promise<AuthClaims>) {
  const handler = makeConsentHandler((ctx) => new ConsentService(ctx, fakeRepo()));
  return defineHandler(handler, { middleware: [authenticate(verifier)] });
}

Deno.test("POST /v1/consent happy path returns 201 with contract-shaped body", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const pipeline = buildPipeline(() =>
      Promise.resolve({ userId: USER_ID, role: "authenticated" } as AuthClaims)
    );
    const req = new Request("http://localhost/v1/consent", {
      method: "POST",
      headers: { Authorization: "Bearer good", "content-type": "application/json" },
      body: JSON.stringify(validBody()),
    });
    const res = await pipeline(req);
    assertEquals(res.status, 201);
    const json = await res.json();
    assertObjectMatch(json, { personalization_granted: true });
    assertEquals(Array.isArray(json.recorded), true);
    assertEquals(json.recorded.length, 2);
    assertEquals(typeof json.trace_id, "string");
  });
});

Deno.test("POST /v1/consent returns 403 when JWT user_id != body profile_id", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const pipeline = buildPipeline(() =>
      Promise.resolve(
        { userId: "99999999-9999-9999-9999-999999999999", role: "authenticated" } as AuthClaims,
      )
    );
    const req = new Request("http://localhost/v1/consent", {
      method: "POST",
      headers: { Authorization: "Bearer good", "content-type": "application/json" },
      body: JSON.stringify(validBody()),
    });
    const res = await pipeline(req);
    assertEquals(res.status, 403);
  });
});

Deno.test("POST /v1/consent returns 422 for an unknown consent_type", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const pipeline = buildPipeline(() =>
      Promise.resolve({ userId: USER_ID, role: "authenticated" } as AuthClaims)
    );
    const req = new Request("http://localhost/v1/consent", {
      method: "POST",
      headers: { Authorization: "Bearer good", "content-type": "application/json" },
      body: JSON.stringify({ ...validBody(), consents: [{ consent_type: "x", granted: true }] }),
    });
    const res = await pipeline(req);
    assertEquals(res.status, 422);
    const json = await res.json();
    assertEquals(json.error.code, API_ERRORS.ERR_CONSENT_TYPE_INVALID.code);
  });
});

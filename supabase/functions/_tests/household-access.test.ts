import { assertEquals, assertNotEquals } from "@std/assert";
import { authenticate, defineHandler, resetConfigCacheForTests } from "../_shared/mod.ts";
import type { AuthClaims } from "../_shared/mod.ts";
import {
  type HouseholdAccessDeps,
  makeHouseholdAccessHandler,
} from "../household-access/handler.ts";

const USER_ID = "11111111-1111-1111-1111-111111111111";
const HOUSEHOLD_ID = "22222222-2222-2222-2222-222222222222";
const REQUIRED_ENV = {
  SUPABASE_URL: "http://localhost:54321",
  SUPABASE_ANON_KEY: "anon-test-key",
  SUPABASE_SERVICE_ROLE_KEY: "service-test-key",
  RE_SERVICE_URL: "http://re.local",
  RE_HMAC_SECRET: "test-hmac-secret-at-least-32-characters",
};

async function withEnv(fn: () => Promise<void>) {
  const previous = new Map<string, string | undefined>();
  for (const [key, value] of Object.entries(REQUIRED_ENV)) {
    previous.set(key, Deno.env.get(key));
    Deno.env.set(key, value);
  }
  try {
    await fn();
  } finally {
    for (const [key, value] of previous) {
      if (value === undefined) Deno.env.delete(key);
      else Deno.env.set(key, value);
    }
    resetConfigCacheForTests();
  }
}

function pipeline(deps: HouseholdAccessDeps) {
  const verifier = () => Promise.resolve({ userId: USER_ID, role: "authenticated" } as AuthClaims);
  return defineHandler(makeHouseholdAccessHandler(deps), { middleware: [authenticate(verifier)] });
}

function post(body: Record<string, unknown>) {
  return new Request("http://localhost/v1/household-access", {
    method: "POST",
    headers: { Authorization: "Bearer good", "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

Deno.test("shared-household viewer can list memberships without owner audit data", async () => {
  await withEnv(async () => {
    let ownerData = true;
    const res = await pipeline({
      authorize: () => Promise.resolve("viewer"),
      list: (_ctx, _household, includeOwnerData) => {
        ownerData = includeOwnerData;
        return Promise.resolve({
          memberships: [{
            user_id: USER_ID,
            role_code: "viewer",
            status: "active",
            joined_at: "2026-08-05T00:00:00Z",
            revoked_at: null,
          }],
          invites: [],
          events: [],
        });
      },
    })(post({ action: "list", household_id: HOUSEHOLD_ID }));
    assertEquals(res.status, 200);
    assertEquals(ownerData, false);
    const body = await res.json();
    assertEquals(body.caller_role, "viewer");
  });
});

Deno.test("owner creates a one-time invite while only its hash reaches storage", async () => {
  await withEnv(async () => {
    let storedHash = "";
    const res = await pipeline({
      authorize: () => Promise.resolve("owner"),
      create: (_ctx, _household, _actor, tokenHash) => {
        storedHash = tokenHash;
        return Promise.resolve("invite-1");
      },
    })(post({ action: "create_invite", household_id: HOUSEHOLD_ID, role: "planner" }));
    assertEquals(res.status, 201);
    const body = await res.json();
    assertEquals(body.invite_id, "invite-1");
    assertEquals(body.role, "planner");
    assertEquals(String(body.token).length, 64);
    assertEquals(storedHash.length, 64);
    assertNotEquals(storedHash, body.token);
  });
});

Deno.test("invite acceptance is token-authorized and does not require existing membership", async () => {
  await withEnv(async () => {
    let authorizationCalled = false;
    const res = await pipeline({
      authorize: () => {
        authorizationCalled = true;
        return Promise.resolve(null);
      },
      accept: (_ctx, actor, hash) => {
        assertEquals(actor, USER_ID);
        assertEquals(hash.length, 64);
        return Promise.resolve(HOUSEHOLD_ID);
      },
    })(post({ action: "accept_invite", token: "a".repeat(64) }));
    assertEquals(res.status, 200);
    assertEquals(authorizationCalled, false);
    assertEquals((await res.json()).household_id, HOUSEHOLD_ID);
  });
});

Deno.test("non-owner cannot create household invitations", async () => {
  await withEnv(async () => {
    let createCalled = false;
    const res = await pipeline({
      authorize: () => Promise.resolve("planner"),
      create: () => {
        createCalled = true;
        return Promise.resolve("unexpected");
      },
    })(post({ action: "create_invite", household_id: HOUSEHOLD_ID, role: "member" }));
    assertEquals(res.status, 403);
    assertEquals(createCalled, false);
  });
});

import { assertEquals, assertRejects } from "@std/assert";
import {
  HOUSEHOLD_PLAN_WRITE_ROLES,
  HOUSEHOLD_READ_ROLES,
  requireHouseholdRole,
} from "../_shared/auth/household.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import type { AuthClaims, RequestContext } from "../_shared/types/context.ts";

const claims: AuthClaims = { userId: "user-1", role: "authenticated" };
const ctx = {} as RequestContext;

Deno.test("active viewer may read a shared household", async () => {
  const role = await requireHouseholdRole(
    ctx,
    claims,
    "household-1",
    HOUSEHOLD_READ_ROLES,
    (_ctx, householdId, userId) => {
      assertEquals(householdId, "household-1");
      assertEquals(userId, "user-1");
      return Promise.resolve("viewer");
    },
  );
  assertEquals(role, "viewer");
});

Deno.test("planner may mutate a household plan", async () => {
  const role = await requireHouseholdRole(
    ctx,
    claims,
    "household-1",
    HOUSEHOLD_PLAN_WRITE_ROLES,
    () => Promise.resolve("planner"),
  );
  assertEquals(role, "planner");
});

Deno.test("viewer cannot mutate a household plan", async () => {
  const error = await assertRejects(
    () =>
      requireHouseholdRole(
        ctx,
        claims,
        "household-1",
        HOUSEHOLD_PLAN_WRITE_ROLES,
        () => Promise.resolve("viewer"),
      ),
    AppError,
  );
  assertEquals(error.code, API_ERRORS.ERR_OWNERSHIP_MISMATCH.code);
});

Deno.test("missing or revoked membership is denied", async () => {
  const error = await assertRejects(
    () =>
      requireHouseholdRole(
        ctx,
        claims,
        "household-1",
        HOUSEHOLD_READ_ROLES,
        () => Promise.resolve(null),
      ),
    AppError,
  );
  assertEquals(error.code, API_ERRORS.ERR_OWNERSHIP_MISMATCH.code);
});

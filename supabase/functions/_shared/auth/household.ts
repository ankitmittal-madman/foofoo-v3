/** Role-aware household authorization for service-role Edge Functions. */
import { createServiceRoleClient } from "../db/client.ts";
import { AppError } from "../errors/app-error.ts";
import { API_ERRORS } from "../errors/api-catalogue.ts";
import type { AuthClaims, RequestContext } from "../types/context.ts";

export const HOUSEHOLD_ROLES = ["owner", "planner", "cook", "member", "viewer"] as const;
export type HouseholdRole = typeof HOUSEHOLD_ROLES[number];

export const HOUSEHOLD_READ_ROLES: readonly HouseholdRole[] = HOUSEHOLD_ROLES;
export const HOUSEHOLD_PLAN_WRITE_ROLES: readonly HouseholdRole[] = ["owner", "planner"];

export type HouseholdRoleLookup = (
  ctx: RequestContext,
  householdId: string,
  userId: string,
) => Promise<HouseholdRole | null>;

export const lookupHouseholdRole: HouseholdRoleLookup = async (ctx, householdId, userId) => {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await db.from("household_memberships").select("role_code")
    .eq("household_id", householdId).eq("user_id", userId).eq("status", "active")
    .maybeSingle();
  if (error) {
    ctx.logger.warn("household.authorization_lookup_failed", { detail: error.message });
    throw new AppError(API_ERRORS.ERR_OWNERSHIP_MISMATCH, {
      detail: "household authorization lookup failed",
    });
  }
  const role = data?.role_code;
  return HOUSEHOLD_ROLES.includes(role as HouseholdRole) ? role as HouseholdRole : null;
};

/** Resolve and enforce an active membership role before any service-role data access. */
export async function requireHouseholdRole(
  ctx: RequestContext,
  claims: AuthClaims,
  householdId: string | null | undefined,
  allowedRoles: readonly HouseholdRole[],
  lookup: HouseholdRoleLookup = lookupHouseholdRole,
): Promise<HouseholdRole> {
  if (!householdId) {
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "no household_id" });
  }
  const role = await lookup(ctx, householdId, claims.userId);
  if (!role || !allowedRoles.includes(role)) {
    throw new AppError(API_ERRORS.ERR_OWNERSHIP_MISMATCH, {
      detail: "active household role is not permitted",
    });
  }
  return role;
}

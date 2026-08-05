import { jsonContract } from "../_shared/api/response.ts";
import { requireAuth } from "../_shared/auth/authorize.ts";
import {
  HOUSEHOLD_READ_ROLES,
  type HouseholdRoleLookup,
  requireHouseholdRole,
} from "../_shared/auth/household.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import { acceptInvite, createInvite, listHouseholdAccess, mutateHouseholdAccess } from "./store.ts";

const INVITABLE_ROLES = ["planner", "cook", "member", "viewer"] as const;
type InvitableRole = typeof INVITABLE_ROLES[number];

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, "0")).join(
    "",
  );
}

function invitationToken(): string {
  return `${crypto.randomUUID().replaceAll("-", "")}${crypto.randomUUID().replaceAll("-", "")}`;
}

export interface HouseholdAccessDeps {
  authorize?: HouseholdRoleLookup;
  list?: typeof listHouseholdAccess;
  create?: typeof createInvite;
  accept?: typeof acceptInvite;
  mutate?: typeof mutateHouseholdAccess;
}

export function makeHouseholdAccessHandler(deps: HouseholdAccessDeps = {}): Handler {
  const list = deps.list ?? listHouseholdAccess;
  const create = deps.create ?? createInvite;
  const accept = deps.accept ?? acceptInvite;
  const mutate = deps.mutate ?? mutateHouseholdAccess;
  return async (req, ctx) => {
    if (req.method !== "POST") throw new AppError(ERROR_CATALOGUE.METHOD_NOT_ALLOWED);
    const claims = requireAuth(ctx.claims);
    let body: Record<string, unknown>;
    try {
      body = await req.json() as Record<string, unknown>;
    } catch {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "invalid JSON body" });
    }
    const action = String(body.action ?? "list");

    if (action === "accept_invite") {
      const token = String(body.token ?? "");
      if (token.length < 32) {
        throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "invalid invite token" });
      }
      const householdId = await accept(ctx, claims.userId, await sha256(token));
      return jsonContract(
        { kind: "household_invite_accepted", household_id: householdId },
        ctx.traceId,
      );
    }

    const householdId = typeof body.household_id === "string" ? body.household_id : claims.userId;
    const requiredRoles = action === "list" || action === "leave"
      ? HOUSEHOLD_READ_ROLES
      : ["owner"] as const;
    const callerRole = await requireHouseholdRole(
      ctx,
      claims,
      householdId,
      requiredRoles,
      deps.authorize,
    );

    if (action === "list") {
      const access = await list(ctx, householdId, callerRole === "owner");
      return jsonContract(
        { kind: "household_access", household_id: householdId, caller_role: callerRole, ...access },
        ctx.traceId,
      );
    }
    if (action === "create_invite") {
      const role = String(body.role ?? "member") as InvitableRole;
      if (!INVITABLE_ROLES.includes(role)) {
        throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "invalid household role" });
      }
      const days = typeof body.expires_in_days === "number"
        ? Math.max(1, Math.min(30, Math.floor(body.expires_in_days)))
        : 7;
      const expiresAt = new Date(Date.now() + days * 86_400_000).toISOString();
      const token = invitationToken();
      const inviteId = await create(
        ctx,
        householdId,
        claims.userId,
        await sha256(token),
        role,
        expiresAt,
      );
      return jsonContract(
        { kind: "household_invite", invite_id: inviteId, token, role, expires_at: expiresAt },
        ctx.traceId,
        201,
      );
    }

    const targetUserId = String(body.target_user_id ?? "");
    if (action !== "leave" && !targetUserId) {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: "target_user_id is required",
      });
    }
    if (action === "change_role") {
      const role = String(body.role ?? "") as InvitableRole;
      if (!INVITABLE_ROLES.includes(role)) {
        throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "invalid household role" });
      }
      await mutate(ctx, "change_household_member_role", {
        p_household_id: householdId,
        p_actor_user_id: claims.userId,
        p_target_user_id: targetUserId,
        p_new_role_code: role,
      });
    } else if (action === "revoke") {
      await mutate(ctx, "revoke_household_membership", {
        p_household_id: householdId,
        p_actor_user_id: claims.userId,
        p_target_user_id: targetUserId,
      });
    } else if (action === "transfer_owner") {
      await mutate(ctx, "transfer_household_ownership", {
        p_household_id: householdId,
        p_actor_user_id: claims.userId,
        p_new_owner_user_id: targetUserId,
      });
    } else if (action === "leave") {
      await mutate(ctx, "leave_household", {
        p_household_id: householdId,
        p_actor_user_id: claims.userId,
      });
    } else {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "unsupported action" });
    }
    return jsonContract(
      { kind: "household_access_updated", action, household_id: householdId },
      ctx.traceId,
    );
  };
}

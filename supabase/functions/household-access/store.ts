import { createServiceRoleClient } from "../_shared/db/client.ts";
import type { HouseholdRole } from "../_shared/auth/household.ts";
import type { RequestContext } from "../_shared/types/context.ts";

export async function listHouseholdAccess(
  ctx: RequestContext,
  householdId: string,
  includeOwnerData: boolean,
) {
  const db = createServiceRoleClient(ctx.config);
  const { data: memberships, error: membershipError } = await db.from("household_memberships")
    .select("user_id,role_code,status,joined_at,revoked_at")
    .eq("household_id", householdId).order("joined_at");
  if (membershipError) throw membershipError;
  if (!includeOwnerData) return { memberships: memberships ?? [], invites: [], events: [] };

  const [{ data: invites, error: inviteError }, { data: events, error: eventError }] = await Promise
    .all([
      db.from("household_invites")
        .select("id,invited_role,invited_by,expires_at,accepted_at,revoked_at,created_at")
        .eq("household_id", householdId).order("created_at", { ascending: false }).limit(50),
      db.from("household_membership_events")
        .select(
          "id,user_id,event_type,previous_role_code,new_role_code,actor_user_id,reason_code,occurred_at",
        )
        .eq("household_id", householdId).order("occurred_at", { ascending: false }).limit(100),
    ]);
  if (inviteError) throw inviteError;
  if (eventError) throw eventError;
  return { memberships: memberships ?? [], invites: invites ?? [], events: events ?? [] };
}

export async function createInvite(
  ctx: RequestContext,
  householdId: string,
  actorUserId: string,
  tokenHash: string,
  role: Exclude<HouseholdRole, "owner">,
  expiresAt: string,
) {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await db.rpc("create_household_invite", {
    p_household_id: householdId,
    p_actor_user_id: actorUserId,
    p_token_hash: tokenHash,
    p_invited_role: role,
    p_expires_at: expiresAt,
  });
  if (error) throw error;
  return String(data);
}

export async function acceptInvite(
  ctx: RequestContext,
  actorUserId: string,
  tokenHash: string,
) {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await db.rpc("accept_household_invite", {
    p_token_hash: tokenHash,
    p_actor_user_id: actorUserId,
  });
  if (error) throw error;
  return String(data);
}

export async function mutateHouseholdAccess(
  ctx: RequestContext,
  rpc:
    | "change_household_member_role"
    | "revoke_household_membership"
    | "leave_household"
    | "transfer_household_ownership",
  params: Record<string, unknown>,
) {
  const db = createServiceRoleClient(ctx.config);
  const { error } = await db.rpc(rpc, params);
  if (error) throw error;
}

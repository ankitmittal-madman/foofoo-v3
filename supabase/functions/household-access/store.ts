import { createServiceRoleClient } from "../_shared/db/client.ts";
import type { HouseholdRole } from "../_shared/auth/household.ts";
import type { RequestContext } from "../_shared/types/context.ts";

export async function listUserHouseholds(ctx: RequestContext, userId: string) {
  const db = createServiceRoleClient(ctx.config);
  const { data: memberships, error } = await db.from("household_memberships")
    .select("household_id,role_code,status,joined_at")
    .eq("user_id", userId).eq("status", "active").order("joined_at");
  if (error) throw error;
  const householdIds = (memberships ?? []).map((row) => String(row.household_id));
  if (householdIds.length === 0) return [];
  const { data: households, error: householdError } = await db.from("households")
    .select("id,name,owner_user_id,status").in("id", householdIds);
  if (householdError) throw householdError;
  const byId = new Map((households ?? []).map((row) => [String(row.id), row]));
  return (memberships ?? []).map((membership) => ({
    household_id: membership.household_id,
    role: membership.role_code,
    joined_at: membership.joined_at,
    name: byId.get(String(membership.household_id))?.name ?? "Household",
    owner_user_id: byId.get(String(membership.household_id))?.owner_user_id ?? null,
  }));
}

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

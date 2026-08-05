import { apiPost } from "./client";

export type HouseholdRole = "owner" | "planner" | "cook" | "member" | "viewer";
export type InvitableRole = Exclude<HouseholdRole, "owner">;

export interface HouseholdSummary {
  household_id: string;
  name: string;
  role: HouseholdRole;
  joined_at: string;
  owner_user_id: string | null;
}

export interface HouseholdMembership {
  user_id: string;
  role_code: HouseholdRole;
  status: string;
  joined_at: string;
  revoked_at: string | null;
}

export interface HouseholdInvite {
  id: string;
  invited_role: InvitableRole;
  invited_by: string;
  expires_at: string;
  accepted_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface HouseholdAccessResponse {
  kind: "household_access";
  household_id: string;
  caller_role: HouseholdRole;
  memberships: HouseholdMembership[];
  invites: HouseholdInvite[];
  events: Array<{
    id: string;
    user_id: string;
    event_type: string;
    previous_role_code: HouseholdRole | null;
    new_role_code: HouseholdRole | null;
    actor_user_id: string | null;
    occurred_at: string;
  }>;
  trace_id: string;
}

export function listMyHouseholds(): Promise<{
  kind: "household_list";
  households: HouseholdSummary[];
  trace_id: string;
}> {
  return apiPost("/household-access", { action: "list_my_households" });
}

export function listHouseholdAccess(householdId: string): Promise<HouseholdAccessResponse> {
  return apiPost("/household-access", { action: "list", household_id: householdId });
}

export function createHouseholdInvite(
  householdId: string,
  role: InvitableRole,
): Promise<{ token: string; invite_id: string; expires_at: string }> {
  return apiPost("/household-access", {
    action: "create_invite",
    household_id: householdId,
    role,
    expires_in_days: 7,
  });
}

export function acceptHouseholdInvite(token: string): Promise<{ household_id: string }> {
  return apiPost("/household-access", { action: "accept_invite", token: token.trim() });
}

export function updateHouseholdMember(
  householdId: string,
  action: "change_role" | "revoke" | "transfer_owner",
  targetUserId: string,
  role?: InvitableRole,
): Promise<unknown> {
  return apiPost("/household-access", {
    action,
    household_id: householdId,
    target_user_id: targetUserId,
    ...(role ? { role } : {}),
  });
}

export function leaveHousehold(householdId: string): Promise<unknown> {
  return apiPost("/household-access", { action: "leave", household_id: householdId });
}

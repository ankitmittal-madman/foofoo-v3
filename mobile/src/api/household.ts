import { apiPost } from "./client";
import type { HouseholdWriteRequest, HouseholdWriteResponse, ScreenAnswer, MemberWrite } from "./types";

/**
 * POST /v1/household. `household_id` is intentionally omittable — the handler defaults it to the
 * caller's own JWT `userId` (household/handler.ts), and requireOwnership rejects any other value
 * for a caller who isn't that household's owner.
 */
export function postHousehold(
  screens: ScreenAnswer[],
  members: MemberWrite[] = [],
): Promise<HouseholdWriteResponse> {
  const body: HouseholdWriteRequest = { screens, members };
  return apiPost<HouseholdWriteResponse>("/household", body);
}

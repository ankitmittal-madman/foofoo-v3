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

export interface OnboardingStatus {
  complete: boolean;
  missingRequiredFields: string[];
}

/**
 * Single source of truth for "has this household completed onboarding" (audit-onboarding-funnel
 * HIGH finding: index.tsx and sign-in.tsx previously used two different, contradictory rules for
 * this, and recommendations.tsx had no completeness check at all).
 *
 * No dedicated read endpoint exists for this yet (a genuine backend gap — see the audit) — this
 * calls POST /v1/household with empty `screens`/`members` as a safe status probe instead of adding
 * a new endpoint, which is out of this fix's scope (mobile-only). This is provably non-mutating:
 * household/store.ts's insertOnboardingSessionRows and upsertHouseholdAnswers both return
 * immediately when given an empty array/object, so an empty call only exercises the handler's own
 * profileExists() check (and, if no profile exists yet, a read-only accumulatedProfileFields()
 * SELECT) — it never writes a row. `profile_exists` on the response is treated as "onboarding
 * complete" since household/handler.ts only ever creates a profile once all five required fields
 * are known.
 */
export async function fetchOnboardingStatus(): Promise<OnboardingStatus> {
  const res = await postHousehold([], []);
  return { complete: res.profile_exists, missingRequiredFields: res.missing_required_fields };
}

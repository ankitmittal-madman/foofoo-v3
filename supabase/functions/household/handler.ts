/**
 * POST /v1/household — business handler (onboarding write path).
 *
 * THIN orchestration handler, same discipline as recommendations/handler.ts: parse → authorize →
 * write → respond. No business logic beyond sequencing four steps against the live `public` schema
 * (store.ts):
 *   1. log every screen this call covers to onboarding_sessions (append-only source of truth)
 *   2. incrementally UPSERT household_answers-bound answers into the current-state row
 *   3. once all five required profiles columns are known (accumulated across calls via step 1's
 *      history), INSERT profiles — exactly once, never re-created if it already exists
 *   4. write any household_members rows supplied, once a profile exists (its FK requires one)
 *
 * Deps are injectable so the handler is unit-testable without a live database, same pattern as
 * recommendations/handler.ts's RecommendationDeps.
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
import { requireOwnership } from "../_shared/auth/authenticate.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import type { RequestContext } from "../_shared/types/context.ts";

import { UserJourney } from "../_shared/logging/userJourney.ts";
import { parseHouseholdWriteRequest } from "./schema.ts";
import {
  accumulatedProfileFields,
  buildHouseholdAnswersPatch,
  createProfile,
  insertOnboardingSessionRows,
  missingRequiredProfileFields,
  profileExists,
  upsertHouseholdAnswers,
  upsertHouseholdMembers,
} from "./store.ts";

const SERVICE_NAME = "household";

export interface HouseholdDeps {
  insertScreens?: typeof insertOnboardingSessionRows;
  upsertAnswers?: typeof upsertHouseholdAnswers;
  loadAccumulated?: typeof accumulatedProfileFields;
  checkProfileExists?: typeof profileExists;
  createProfileRow?: typeof createProfile;
  upsertMembers?: typeof upsertHouseholdMembers;
}

/** Build the POST /v1/household handler. */
export function makeHouseholdHandler(deps: HouseholdDeps = {}): Handler {
  const insertScreens = deps.insertScreens ?? insertOnboardingSessionRows;
  const upsertAnswers = deps.upsertAnswers ?? upsertHouseholdAnswers;
  const loadAccumulated = deps.loadAccumulated ?? accumulatedProfileFields;
  const checkProfileExists = deps.checkProfileExists ?? profileExists;
  const createProfileRow = deps.createProfileRow ?? createProfile;
  const upsertMembers = deps.upsertMembers ?? upsertHouseholdMembers;

  return async (req, ctx: RequestContext) => {
    if (req.method !== "POST") {
      throw new AppError(ERROR_CATALOGUE.METHOD_NOT_ALLOWED);
    }

    // Auth middleware populated claims; requireAuth is the defensive backstop.
    const claims = requireAuth(ctx.claims);

    let body: Record<string, unknown> = {};
    try {
      const text = await req.text();
      if (text) body = JSON.parse(text) as Record<string, unknown>;
    } catch {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: "request body is not valid JSON",
      });
    }

    const householdId = (typeof body.household_id === "string" ? body.household_id : null) ??
      claims.userId;

    // Sole Surface-B authorization boundary (DOC-P3-06 §05), same import/call/placement as
    // recommendations/handler.ts: runs BEFORE any write — an unauthorized household_id never
    // reaches store.ts. For a household that does not exist yet, this degenerates to "the id being
    // written to must equal the caller's own id", which createProfile below additionally enforces
    // at the query level (defense in depth, not a replacement for this check).
    requireOwnership(claims, householdId);

    const log = ctx.logger.child({ household_id: householdId, service: SERVICE_NAME });

    // Full structural + semantic validation (schema.ts) — after the ownership gate, same ordering
    // as recommendations/handler.ts's contract validation running after its own ownership check.
    const parsed = parseHouseholdWriteRequest(body);

    // 1. Append every screen this call covers to the source-of-truth history. Must run before
    // step 3 reads accumulated profile fields, so this call's own answers are included.
    await insertScreens(ctx, householdId, parsed.screens);

    // 2. Incrementally upsert the household_answers-bound subset of this call's answers.
    const answersPatch = buildHouseholdAnswersPatch(parsed.screens);
    await upsertAnswers(ctx, householdId, answersPatch);
    log.info("household.answers_upserted", { fields: Object.keys(answersPatch) });

    // 3. Profile creation — gated on all five required fields being known, accumulated across
    // however many calls it took. Never re-created if a profiles row already exists.
    let exists = await checkProfileExists(ctx, householdId);
    let createdThisCall = false;
    let missing: string[] = [];

    if (!exists) {
      const accumulated = await loadAccumulated(ctx, householdId);
      missing = missingRequiredProfileFields(accumulated);
      if (missing.length === 0) {
        // claims.userId, NOT householdId — see createProfile's own doc comment. The two are
        // already guaranteed equal by requireOwnership above; this is belt-and-suspenders so the
        // INSERT itself cannot create a profile for anyone but the authenticated caller, even if a
        // future change to the ownership check above had a bug.
        await createProfileRow(ctx, claims.userId, accumulated);
        createdThisCall = true;
        exists = true;
        log.info("household.profile_created", { household_id: householdId });
      }
    }

    // 4. household_members — requires a profiles row (FK). Reject cleanly (422) rather than let a
    // raw FK-violation reach the client as an opaque 500.
    let membersWritten = 0;
    if (parsed.members.length > 0) {
      if (!exists) {
        throw new AppError(API_ERRORS.ERR_HOUSEHOLD_INCOMPLETE, {
          context: { missing_required_fields: missing },
        });
      }
      membersWritten = await upsertMembers(ctx, householdId, parsed.members);
      log.info("household.members_written", { count: membersWritten });
    }

    UserJourney.logOnboardingStep(
      householdId,
      parsed.screens.map((s) => s.screenId),
      { profileCreated: createdThisCall, membersWritten: membersWritten || undefined },
    );

    return jsonContract(
      {
        household_id: householdId,
        profile_exists: exists,
        profile_created: createdThisCall,
        answers_recorded: Object.keys(answersPatch),
        missing_required_fields: exists ? [] : missing,
        members_written: membersWritten,
      },
      ctx.traceId,
      200,
    );
  };
}

/**
 * POST /v1/user/delete — business handler (DOC-P3-06 §06.8 / DCR-P3-06-005, LF-M03). CRITICAL
 * audit fix — this endpoint did not previously exist at all.
 *
 * Flow: authenticate → ownership → confirmation_phrase safety gate → soft-delete immediately
 * (`profiles.deleted_at`) → 202 with the deletion job handle. The hard-delete-within-72h itself is
 * NOT done here — it is `_shared/services/scheduler/hard-delete.ts`, a separate scheduled job, per
 * this endpoint's own DCR note ("the CRON-based hard-delete itself remains ... an internal
 * scheduled job").
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
import { requireOwnership } from "../_shared/auth/authenticate.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { deterministicUuid } from "../_shared/utils/deterministic-id.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import { getProfileDeletionState, softDeleteIfNotAlready } from "./store.ts";
import { parseDeleteRequest, REQUIRED_CONFIRMATION_PHRASE } from "./schema.ts";

const SERVICE_NAME = "user-delete";
const HARD_DELETE_WINDOW_MS = 72 * 60 * 60 * 1000; // DOC-P3-03 §15 LF-M03: hard-delete within 72h
/** Namespaces the deterministic deletion_job_id so it can never collide with an unrelated
 * deterministic id derived elsewhere in the codebase from the same profile_id. */
const DELETION_JOB_SALT = "foofoo.user_delete.deletion_job_id.v1";

/** Build the POST /v1/user/delete handler. */
export function makeUserDeleteHandler(): Handler {
  return async (req, ctx) => {
    if (req.method !== "POST") {
      throw new AppError(ERROR_CATALOGUE.METHOD_NOT_ALLOWED);
    }

    const claims = requireAuth(ctx.claims);

    let body: unknown;
    try {
      body = await req.json();
    } catch {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: "request body is not valid JSON",
      });
    }

    const { userId, confirmationPhrase } = parseDeleteRequest(body);

    // Sole Surface-B authorization boundary (DOC-P3-06 §05).
    requireOwnership(claims, userId);

    // Safety gate (DOC-P3-06 §06.8 field table) — exact match, case-sensitive, no trimming (a
    // permanent irreversible action should not be triggerable by an accidental near-match).
    if (confirmationPhrase !== REQUIRED_CONFIRMATION_PHRASE) {
      throw new AppError(API_ERRORS.ERR_CONFIRMATION_PHRASE_MISMATCH);
    }

    const db = createServiceRoleClient(ctx.config);
    const log = ctx.logger.child({ profile_id: userId, service: SERVICE_NAME });

    const before = await getProfileDeletionState(db, userId);
    if (!before.exists) {
      throw new AppError(ERROR_CATALOGUE.NOT_FOUND, { detail: "no profile for this user_id" });
    }

    // Idempotent per DOC-P3-06 §08: a repeat call on an already-soft-deleted profile must return
    // the SAME deletion_job_id/timestamps, never reset the 72h clock or spawn a second job.
    const deletedAt = before.deletedAt ?? await softDeleteIfNotAlready(db, userId);
    if (before.deletedAt === null) {
      log.info("user_delete.soft_deleted", { deleted_at: deletedAt });
    } else {
      log.info("user_delete.repeat_call_already_soft_deleted", { deleted_at: deletedAt });
    }

    const deletionJobId = await deterministicUuid(DELETION_JOB_SALT, userId);
    const hardDeleteEstimatedBy = new Date(
      new Date(deletedAt).getTime() + HARD_DELETE_WINDOW_MS,
    ).toISOString();

    return jsonContract(
      {
        deletion_job_id: deletionJobId,
        soft_deleted_at: deletedAt,
        hard_delete_estimated_by: hardDeleteEstimatedBy,
      },
      ctx.traceId,
      202,
    );
  };
}

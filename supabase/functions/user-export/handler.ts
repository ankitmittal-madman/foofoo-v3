/**
 * GET /v1/user/export (+ GET /v1/user/export/{export_job_id}) — CRITICAL audit fix (LF-M02 had no
 * endpoint at all). DOC-P3-06 §06.7's own DCR note requires the polling sub-resource; both routes
 * are served from this one Edge Function (path-suffix routing — see index.ts's own doc comment for
 * why: this repo's Supabase project has no per-path routing config, one folder = one function).
 *
 * MVP job-queue design decision (judgment call, flagged per this WP's instructions):
 * `_shared/services/scheduler/` has no existing async-job-queue convention to reuse (only
 * synchronous, single-invocation scheduled jobs — nightly-plan.ts), and no job table exists in the
 * live schema (would need a migration, out of this task's scope — flagged in the WP report). So
 * this is the explicitly-sanctioned "synchronous-but-202-shaped" MVP interpretation: the export is
 * computed immediately and written to a private Supabase Storage bucket; the response still matches
 * the `202 { export_job_id, status: "queued", estimated_completion }` shape exactly. No job-status
 * table is needed for the poll either — ownership + job identity are both enforced by the STORAGE
 * PATH ITSELF (`exports/{ownerId}/{jobId}.json`): the poll handler only ever looks under the
 * CALLER's OWN `ownerId` prefix (from their own verified JWT), so a job id that belongs to someone
 * else simply isn't found there — a safe 404, never a cross-user read (Task 4's RLS/service_role
 * leakage requirement, verified by construction, not by a runtime check that could be forgotten).
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { loadUserExportBundle } from "./store.ts";

const SERVICE_NAME = "user-export";
const BUCKET = "user-exports";
const SIGNED_URL_TTL_SECONDS = 24 * 60 * 60; // 24h, per DOC-P3-06 §06.7 "expires in 24h"
const HARD_DELETE_WINDOW_MS = 72 * 60 * 60 * 1000; // "queued job completes within 72 hours"
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function jobPath(ownerId: string, jobId: string): string {
  return `exports/${ownerId}/${jobId}.json`;
}

/** Idempotent bucket creation — application-level, not a `database/` migration (Storage buckets
 * are a Storage-API resource, not a hand-numbered schema migration). Safe to call every request:
 * a 409/"already exists" from a concurrent first-caller is swallowed, never surfaced. */
async function ensureBucket(ctx: RequestContext): Promise<void> {
  const db = createServiceRoleClient(ctx.config);
  const { error } = await withTimeout(
    db.storage.createBucket(BUCKET, { public: false }),
    "userExport.ensureBucket",
  );
  if (error && !/already exists/i.test(error.message)) {
    ctx.logger.warn("user_export.bucket_create_failed", { detail: error.message });
  }
}

async function createExportJob(ctx: RequestContext, ownerId: string): Promise<Response> {
  await ensureBucket(ctx);
  const db = createServiceRoleClient(ctx.config);
  const bundle = await loadUserExportBundle(db, ownerId);

  const exportJobId = crypto.randomUUID();
  const path = jobPath(ownerId, exportJobId);
  const { error } = await withTimeout(
    db.storage.from(BUCKET).upload(path, JSON.stringify(bundle, null, 2), {
      contentType: "application/json",
      upsert: false,
    }),
    "userExport.upload",
  );
  if (error) {
    throw new AppError(ERROR_CATALOGUE.INTERNAL, {
      detail: `export upload failed: ${error.message}`,
    });
  }

  ctx.logger.info("user_export.job_created", { profile_id: ownerId, export_job_id: exportJobId });

  return jsonContract(
    {
      export_job_id: exportJobId,
      status: "queued",
      estimated_completion: new Date(Date.now() + HARD_DELETE_WINDOW_MS).toISOString(),
    },
    ctx.traceId,
    202,
  );
}

async function pollExportJob(
  ctx: RequestContext,
  ownerId: string,
  exportJobId: string,
): Promise<Response> {
  const db = createServiceRoleClient(ctx.config);
  const path = jobPath(ownerId, exportJobId);

  const { data: signed, error } = await withTimeout(
    db.storage.from(BUCKET).createSignedUrl(path, SIGNED_URL_TTL_SECONDS),
    "userExport.createSignedUrl",
  );
  // Ownership is enforced by construction: `path` is built from the CALLER's own verified ownerId,
  // never from anything in the URL — a job id that belongs to someone else's prefix is simply not
  // found at this path, indistinguishable from "no such job", never a cross-user leak.
  if (error || !signed?.signedUrl) {
    throw new AppError(API_ERRORS.ERR_EXPORT_JOB_NOT_FOUND, {
      detail: error?.message ?? "no signed URL",
    });
  }

  return jsonContract(
    {
      export_job_id: exportJobId,
      status: "complete",
      download_url: signed.signedUrl,
      format: "json",
    },
    ctx.traceId,
    200,
  );
}

/** Build the GET /v1/user/export[/{export_job_id}] handler. */
export function makeUserExportHandler(): Handler {
  return async (req, ctx) => {
    if (req.method !== "GET") {
      throw new AppError(ERROR_CATALOGUE.METHOD_NOT_ALLOWED);
    }

    // Auth middleware populated claims; requireAuth is the defensive backstop. Per DOC-P3-06 §05
    // table: "/v1/user/export — JWT user_id (or JWT-derived, no body param needed)" — the caller's
    // own JWT is the ENTIRE ownership boundary here (there is no body/path user_id to compare it
    // against), which is exactly what the storage-path-scoping design above relies on.
    const claims = requireAuth(ctx.claims);
    const log = ctx.logger.child({ profile_id: claims.userId, service: SERVICE_NAME });

    // Path-suffix routing: this repo has no per-path route config (one folder = one function), so
    // the polling sub-resource is distinguished by whether the last path segment looks like a job
    // id, matching DOC-P3-06 §06.7's own literal path shape `/v1/user/export/{export_job_id}`.
    const segments = ctx.url.pathname.split("/").filter(Boolean);
    const last = segments[segments.length - 1] ?? "";
    if (UUID_RE.test(last)) {
      return await pollExportJob({ ...ctx, logger: log }, claims.userId, last);
    }
    return await createExportJob({ ...ctx, logger: log }, claims.userId);
  };
}

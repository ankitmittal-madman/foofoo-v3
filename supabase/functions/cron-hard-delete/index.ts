/**
 * Scheduled job entrypoint — LF-M03's hard-delete-within-72h CRON (DOC-P3-06 §06.8 / DOC-P3-03
 * §15). Invoked by pg_cron via net.http_post with `Authorization: Bearer <service_role key>`
 * (see ops/audits/audit-dpdp/RUNBOOK_schedule-retention-jobs-2026-07-30.md) — verified below by
 * `requireServiceRole()`, not a user JWT. Previously shipped with `verify_jwt=false` at the
 * gateway AND no application-level check, so the URL alone was enough to trigger a real deletion
 * run; both are closed now (config.toml no longer overrides verify_jwt for this function).
 */
import { buildContext, compose, errorBoundary, requestLogging } from "../_shared/middleware/index.ts";
import { requireServiceRole } from "../_shared/auth/service-role.ts";
import { jsonOk } from "../_shared/api/response.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { HardDeleteScheduler } from "../_shared/services/scheduler/hard-delete.ts";

const pipeline = compose([errorBoundary, requestLogging, requireServiceRole()])(async (_req, ctx) => {
  const scheduler = new HardDeleteScheduler(createServiceRoleClient(ctx.config), ctx.logger);
  const result = await scheduler.run();
  return jsonOk(result, ctx.traceId, 200);
});

Deno.serve(async (req: Request): Promise<Response> => {
  const ctx = buildContext(req);
  return await pipeline(req, ctx);
});

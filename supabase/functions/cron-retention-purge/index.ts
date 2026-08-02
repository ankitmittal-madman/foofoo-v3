/**
 * Scheduled job entrypoint — DOC-P3-03 §15 / DCR-P3-07-004 retention purge (interaction_events > 2
 * years, audit_log > 3 years — two separate policies, see retention-purge.ts). Same
 * unauthenticated-by-design posture as cron-hard-delete/index.ts — see that file's doc comment.
 */
import {
  buildContext,
  compose,
  errorBoundary,
  requestLogging,
} from "../_shared/middleware/index.ts";
import { jsonOk } from "../_shared/api/response.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { RetentionPurgeScheduler } from "../_shared/services/scheduler/retention-purge.ts";

const pipeline = compose([errorBoundary, requestLogging])(async (_req, ctx) => {
  const scheduler = new RetentionPurgeScheduler(createServiceRoleClient(ctx.config), ctx.logger);
  const result = await scheduler.run();
  return jsonOk(result, ctx.traceId, 200);
});

Deno.serve(async (req: Request): Promise<Response> => {
  const ctx = buildContext(req);
  return await pipeline(req, ctx);
});

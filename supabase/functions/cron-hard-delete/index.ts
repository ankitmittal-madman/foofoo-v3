/**
 * Scheduled job entrypoint — LF-M03's hard-delete-within-72h CRON (DOC-P3-06 §06.8 / DOC-P3-03
 * §15). Deliberately UNAUTHENTICATED at the application layer (no `authenticate()` middleware) —
 * per DOC-P3-06 §04, scheduled jobs "execute under service_role via Supabase's scheduled Edge
 * Function / pg_cron mechanism and are never reachable over the public internet with a user JWT."
 * The Supabase project's global `verify_jwt = true` (config.toml) still applies at the platform
 * gateway unless a per-function override is added there — flagged in the WP report as a deployment
 * config step (adding `[functions.cron-hard-delete] verify_jwt = false` to config.toml) alongside
 * the actual `pg_cron` schedule registration, both coordinated with the database-migration work
 * happening in parallel rather than done here.
 */
import {
  buildContext,
  compose,
  errorBoundary,
  requestLogging,
} from "../_shared/middleware/index.ts";
import { jsonOk } from "../_shared/api/response.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { HardDeleteScheduler } from "../_shared/services/scheduler/hard-delete.ts";

const pipeline = compose([errorBoundary, requestLogging])(async (_req, ctx) => {
  const scheduler = new HardDeleteScheduler(createServiceRoleClient(ctx.config), ctx.logger);
  const result = await scheduler.run();
  return jsonOk(result, ctx.traceId, 200);
});

Deno.serve(async (req: Request): Promise<Response> => {
  const ctx = buildContext(req);
  return await pipeline(req, ctx);
});

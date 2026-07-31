/**
 * GET /v1/user/export (+ /v1/user/export/{export_job_id}) — Edge Function entrypoint.
 *
 * Same always-on pipeline + `authenticate()` middleware pattern as every other endpoint in this
 * repo (consent/index.ts, household/index.ts, onboarding/index.ts, recommendations/index.ts). Both
 * contract routes are served by this one function — see handler.ts's own doc comment for why.
 */
import { defineHandler } from "../_shared/api/handler.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { makeUserExportHandler } from "./handler.ts";

Deno.serve(defineHandler(makeUserExportHandler(), { middleware: [authenticate()] }));

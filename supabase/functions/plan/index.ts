/**
 * POST /v1/plan — WP-18 planning-surfaces Edge Function entrypoint.
 *
 * Same wiring as recommendations/index.ts: the always-on infrastructure pipeline (context →
 * error-boundary → logging) plus authenticate() around the thin handler. JWT is enforced at the
 * gateway (config.toml verify_jwt = true) and re-verified here. This function owns auth/DB and
 * calls the stateless Python RE for the planning math.
 */
import { defineHandler } from "../_shared/api/handler.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { makePlanHandler } from "./handler.ts";

Deno.serve(defineHandler(makePlanHandler(), { middleware: [authenticate()] }));

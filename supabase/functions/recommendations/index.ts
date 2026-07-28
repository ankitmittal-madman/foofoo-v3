/**
 * POST /v1/recommendations — Edge Function entrypoint (Phase C, RE-DOC-10 §4/§9).
 *
 * Wires the always-on infrastructure pipeline (context → error-boundary → logging) plus the
 * `authenticate()` middleware around the thin orchestration handler, and serves it. JWT is also
 * enforced at the gateway (config.toml verify_jwt = true); the in-function verifier provides
 * defense-in-depth. This function OWNS auth/DB and calls the stateless Python RE for the math —
 * the frozen architecture boundary.
 */
import { defineHandler } from "../_shared/api/handler.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { makeRecommendationsHandler } from "./handler.ts";

Deno.serve(defineHandler(makeRecommendationsHandler(), { middleware: [authenticate()] }));

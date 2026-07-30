/**
 * POST /v1/household — Edge Function entrypoint (onboarding write path).
 *
 * Wires the always-on infrastructure pipeline (context → error-boundary → logging) plus the
 * `authenticate()` middleware around the thin write handler, and serves it — the exact same
 * `defineHandler(handler, { middleware: [authenticate()] })` pattern as consent/index.ts and
 * recommendations/index.ts; no new middleware pattern introduced. JWT is also enforced at the
 * gateway (config.toml verify_jwt = true); the in-function verifier provides defense-in-depth.
 */
import { defineHandler } from "../_shared/api/handler.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { makeHouseholdHandler } from "./handler.ts";

Deno.serve(defineHandler(makeHouseholdHandler(), { middleware: [authenticate()] }));

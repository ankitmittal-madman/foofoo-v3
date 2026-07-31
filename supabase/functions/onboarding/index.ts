/**
 * POST /v1/onboarding — Edge Function entrypoint.
 *
 * Wires the always-on infrastructure pipeline (context → error-boundary → logging) plus the
 * `authenticate()` middleware around the thin business handler — identical pattern to
 * consent/index.ts, household/index.ts, recommendations/index.ts. JWT is additionally enforced at
 * the gateway (config.toml verify_jwt = true); the in-function verifier provides defense-in-depth.
 */
import { defineHandler } from "../_shared/api/handler.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { makeOnboardingHandler } from "./handler.ts";

Deno.serve(defineHandler(makeOnboardingHandler(), { middleware: [authenticate()] }));

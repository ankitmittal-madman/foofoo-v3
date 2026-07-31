/**
 * POST /v1/onboarding — Edge Function entrypoint.
 *
 * ⚠️ NOT ON THE LIVE MOBILE PATH — see handler.ts's header comment before deploying or changing
 * this. Targets the legacy/retired TypeScript RE engine, kept as a reference implementation
 * (Founder decision, 2026-07-30), not called by the app.
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

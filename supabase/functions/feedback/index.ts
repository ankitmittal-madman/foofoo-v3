/**
 * POST /v1/feedback — Edge Function entrypoint (WP-15).
 *
 * Wires the always-on infrastructure pipeline (context → error-boundary → logging) plus the
 * `authenticate()` middleware around the thin business handler, and serves it. JWT is also
 * enforced at the gateway (config.toml verify_jwt = true); the in-function verifier provides
 * defense-in-depth, same pattern as every other authenticated endpoint in this repo.
 */
import { defineHandler } from "../_shared/api/handler.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { makeFeedbackHandler } from "./handler.ts";

Deno.serve(defineHandler(makeFeedbackHandler(), { middleware: [authenticate()] }));

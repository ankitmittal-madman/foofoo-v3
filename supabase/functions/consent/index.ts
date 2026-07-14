/**
 * POST /v1/consent — Edge Function entrypoint (WP-8C).
 *
 * Wires the always-on infrastructure pipeline (context → error-boundary → logging) plus the
 * `authenticate()` middleware around the thin business handler, and serves it. Endpoint contract:
 * DOC-P3-06 §06.1; business logic LF-M01 (DOC-P3-03 §15). JWT is additionally enforced at the
 * gateway (config.toml verify_jwt = true, DOC-P3-06 §04) — the in-function verifier extracts the
 * verified claims and provides defense-in-depth.
 */
import { defineHandler } from "../_shared/api/handler.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { makeConsentHandler } from "./handler.ts";

Deno.serve(defineHandler(makeConsentHandler(), { middleware: [authenticate()] }));

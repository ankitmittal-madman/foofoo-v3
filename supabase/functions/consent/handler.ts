/**
 * POST /v1/consent — business handler (WP-8C).
 *
 * THIN handler (DOC-P4-00 §2/§6): parse → authorize (ownership) → delegate to the service →
 * envelope the response. No business logic and no SQL here. Authentication is applied by the
 * `authenticate()` middleware in index.ts (claims are already on the context by the time this
 * runs). Maps to LF-M01 (DOC-P3-03 §15), contract DOC-P3-06 §06.1.
 *
 * The service is resolved via an injectable factory so the handler is unit-testable without a
 * live database (default resolves the real service from the DI container).
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
import { requireOwnership } from "../_shared/auth/authenticate.ts";
import { parseConsentRequest } from "../_shared/validation/consent-schema.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { createContainer } from "../_shared/di/container.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { ConsentService } from "../_shared/services/consent-service.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import type { RequestContext } from "../_shared/types/context.ts";

/** How the handler obtains its service. Default = the real DI container; tests inject a fake. */
export type ConsentServiceResolver = (ctx: RequestContext) => ConsentService;

const defaultResolver: ConsentServiceResolver = (ctx) => createContainer(ctx).consentService;

/** Build the POST /v1/consent handler. */
export function makeConsentHandler(resolve: ConsentServiceResolver = defaultResolver): Handler {
  return async (req, ctx) => {
    if (req.method !== "POST") {
      throw new AppError(ERROR_CATALOGUE.METHOD_NOT_ALLOWED);
    }

    // Auth middleware populated claims; requireAuth is a defensive backstop.
    const claims = requireAuth(ctx.claims);

    let body: unknown;
    try {
      body = await req.json();
    } catch {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: "request body is not valid JSON",
      });
    }

    const consentReq = parseConsentRequest(body);

    // Sole Surface-B authorization boundary (DOC-P3-06 §05): JWT user_id == body profile_id.
    requireOwnership(claims, consentReq.profileId);

    // IP-hash deferred (see ConsentService); pass null (column is nullable, DOC-P3-04 §03.4).
    const result = await resolve(ctx).captureConsent(consentReq, null);

    // 201 Created per DOC-P3-06 §06.1.
    return jsonContract({ ...result }, ctx.traceId, 201);
  };
}

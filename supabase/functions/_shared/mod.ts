/**
 * FooFoo backend shared foundation — public barrel (WP-8B).
 *
 * Single import surface for the engineering foundation. Endpoints and services (WP-8C onward)
 * import from here. Contains NO business logic, NO endpoints, NO recommendation logic — only the
 * scaffold approved in DOC-P4-00 (WP-8A).
 */

// config
export { getConfig, loadConfig, resetConfigCacheForTests } from "./config/config.ts";
export type { AppConfig, Environment } from "./config/config.ts";
export { ENV_VARS } from "./config/env.ts";

// logging
export { createLogger } from "./logging/logger.ts";
export type { LogFields, Logger, LogLevel } from "./logging/logger.ts";

// errors
export { API_ERRORS, AppError, ERROR_CATALOGUE } from "./errors/index.ts";
export type { ApiErrorCode, ErrorCode, ErrorSpec } from "./errors/index.ts";

// types
export type { AuthClaims, RequestContext } from "./types/context.ts";
export { err, ok } from "./types/result.ts";
export type { Result } from "./types/result.ts";

// db
export { createAuthenticatedClient, createServiceRoleClient } from "./db/client.ts";
export type { SupabaseClient } from "./db/client.ts";

// auth
export { claimsFromPayload, extractBearer } from "./auth/jwt.ts";
export { assertOwns, assertRole, requireAuth } from "./auth/authorize.ts";
export { authenticate, requireOwnership, supabaseJwtVerifier } from "./auth/authenticate.ts";
export type { JwtVerifier } from "./auth/authenticate.ts";

// validation
export { validate, z } from "./validation/validate.ts";
export { CONSENT_TYPES, parseConsentRequest } from "./validation/consent-schema.ts";
export type { ConsentInput, ConsentRequest, ConsentType } from "./validation/consent-schema.ts";

// middleware
export { buildContext, compose, errorBoundary, requestLogging } from "./middleware/index.ts";
export type { Handler, Middleware } from "./middleware/index.ts";

// api
export { jsonContract, jsonOk, noContent } from "./api/response.ts";
export { defineHandler } from "./api/handler.ts";

// repositories / services (base classes + concrete WP-8C classes)
export { BaseRepository } from "./repositories/base-repository.ts";
export { BaseService } from "./services/base-service.ts";
export { ConsentRepository } from "./repositories/consent-repository.ts";
export type {
  ConsentInsertRow,
  IConsentRepository,
  RecordedConsent,
} from "./repositories/consent-repository.ts";
export { ConsentService } from "./services/consent-service.ts";
export type { ConsentResponse } from "./services/consent-service.ts";

// telemetry
export { loggerSink, withTiming } from "./telemetry/telemetry.ts";
export type { TelemetrySink } from "./telemetry/telemetry.ts";

// di
export { Container, createContainer } from "./di/container.ts";

// constants + utils
export { PUBLIC_SCHEMA, RE_ENGINE_SCHEMA, ROLES } from "./constants/schemas.ts";
export { newTraceId } from "./utils/id.ts";
export { invariant } from "./utils/assert.ts";

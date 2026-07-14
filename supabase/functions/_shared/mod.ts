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
export { AppError, ERROR_CATALOGUE } from "./errors/index.ts";
export type { ErrorCode, ErrorSpec } from "./errors/index.ts";

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

// validation
export { validate, z } from "./validation/validate.ts";

// middleware
export { buildContext, compose, errorBoundary, requestLogging } from "./middleware/index.ts";
export type { Handler, Middleware } from "./middleware/index.ts";

// api
export { jsonOk, noContent } from "./api/response.ts";
export { defineHandler } from "./api/handler.ts";

// repositories / services (base classes only)
export { BaseRepository } from "./repositories/base-repository.ts";
export { BaseService } from "./services/base-service.ts";

// telemetry
export { loggerSink, withTiming } from "./telemetry/telemetry.ts";
export type { TelemetrySink } from "./telemetry/telemetry.ts";

// di
export { Container, createContainer } from "./di/container.ts";

// constants + utils
export { PUBLIC_SCHEMA, RE_ENGINE_SCHEMA, ROLES } from "./constants/schemas.ts";
export { newTraceId } from "./utils/id.ts";
export { invariant } from "./utils/assert.ts";

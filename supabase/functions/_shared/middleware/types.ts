/**
 * Middleware + handler types (WP-8B foundation).
 *
 * A Handler turns a Request + RequestContext into a Response. Middleware wraps a Handler,
 * running cross-cutting concerns before/after (auth, validation, rate-limit, logging, errors).
 * This is the framework; concrete auth/rate-limit implementations arrive in later WPs.
 */
import type { RequestContext } from "../types/context.ts";

export type Handler = (req: Request, ctx: RequestContext) => Promise<Response> | Response;

export type Middleware = (next: Handler) => Handler;

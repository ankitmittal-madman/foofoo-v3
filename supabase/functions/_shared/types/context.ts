/**
 * Request context + auth claims types (WP-8B foundation).
 *
 * RequestContext is threaded through middleware → handler → service; it carries the trace id,
 * logger, config, and (once authenticated) the caller's claims. Services stay stateless by
 * receiving context explicitly.
 */
import type { AppConfig } from "../config/config.ts";
import type { Logger } from "../logging/logger.ts";

/** Verified JWT claims (populated by the auth middleware). Framework shape, not a flow. */
export interface AuthClaims {
  /** Supabase user id (JWT `sub`). */
  readonly userId: string;
  /** JWT `role` claim (e.g. "authenticated"). */
  readonly role: string;
  readonly email?: string;
}

export interface RequestContext {
  readonly traceId: string;
  readonly logger: Logger;
  readonly config: AppConfig;
  readonly method: string;
  readonly url: URL;
  /** Present only after the auth middleware runs on a protected route. */
  readonly claims?: AuthClaims;
}

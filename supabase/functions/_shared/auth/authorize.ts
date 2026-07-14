/**
 * Authorization guards (WP-8B foundation).
 *
 * Because Edge Functions run under `service_role` and BYPASS RLS (DOC-P3-06 §01.2 / §05), every
 * ownership check that RLS would normally enforce MUST be coded explicitly. These are the generic
 * primitives; concrete per-resource checks are added with each endpoint (WP-8C onward). No
 * business logic here — just the reusable guards.
 */
import { AppError } from "../errors/app-error.ts";
import { ERROR_CATALOGUE } from "../errors/catalogue.ts";
import type { AuthClaims } from "../types/context.ts";

/** Assert the request is authenticated; returns the claims or throws AUTH_REQUIRED. */
export function requireAuth(claims: AuthClaims | undefined): AuthClaims {
  if (!claims) throw new AppError(ERROR_CATALOGUE.AUTH_REQUIRED);
  return claims;
}

/** Assert the authenticated caller owns the target resource (by user id), else FORBIDDEN. */
export function assertOwns(claims: AuthClaims, resourceOwnerId: string): void {
  if (claims.userId !== resourceOwnerId) {
    throw new AppError(ERROR_CATALOGUE.FORBIDDEN, {
      detail: `caller ${claims.userId} != owner ${resourceOwnerId}`,
    });
  }
}

/** Assert the caller holds a required role, else FORBIDDEN. */
export function assertRole(claims: AuthClaims, requiredRole: string): void {
  if (claims.role !== requiredRole) {
    throw new AppError(ERROR_CATALOGUE.FORBIDDEN, {
      detail: `role ${claims.role} != required ${requiredRole}`,
    });
  }
}

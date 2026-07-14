/**
 * Base service (WP-8B foundation).
 *
 * Services orchestrate business logic (the DOC-P3-03 Logical Functions) and delegate all I/O to
 * repositories. They are stateless: per-request state arrives via RequestContext. The base class
 * binds the context + a component logger. Concrete services (onboarding, planning, recommendation
 * core, …) are added in later WPs — none here.
 */
import type { RequestContext } from "../types/context.ts";
import type { Logger } from "../logging/logger.ts";

export abstract class BaseService {
  protected readonly ctx: RequestContext;
  protected readonly logger: Logger;

  constructor(ctx: RequestContext) {
    this.ctx = ctx;
    this.logger = ctx.logger.child({ component: this.constructor.name });
  }
}

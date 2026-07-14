/**
 * Dependency-injection container (WP-8B foundation).
 *
 * Lightweight, framework-free DI (WP-8A §20). A per-request Container lazily builds the object
 * graph (config → service-role db client → telemetry → [repositories → services in later WPs]).
 * Lazy getters keep cold-start cheap and make swapping fakes trivial in tests. No global mutable
 * singletons except the process-level config (cached in config.ts).
 */
import { createServiceRoleClient, type SupabaseClient } from "../db/client.ts";
import { loggerSink, type TelemetrySink } from "../telemetry/telemetry.ts";
import type { RequestContext } from "../types/context.ts";

export class Container {
  private readonly ctx: RequestContext;
  private _db: SupabaseClient | null = null;
  private _telemetry: TelemetrySink | null = null;

  constructor(ctx: RequestContext) {
    this.ctx = ctx;
  }

  /** Service-role DB client (RLS bypassed — authorize explicitly). Built once per request. */
  get db(): SupabaseClient {
    if (this._db === null) this._db = createServiceRoleClient(this.ctx.config);
    return this._db;
  }

  get telemetry(): TelemetrySink {
    if (this._telemetry === null) this._telemetry = loggerSink(this.ctx.logger);
    return this._telemetry;
  }

  // Repository/service accessors are added per-WP as concrete classes land (WP-8C onward),
  // each as a lazy getter that composes from `this.db` / `this.ctx`.
}

/** Build a fresh container for a request. */
export function createContainer(ctx: RequestContext): Container {
  return new Container(ctx);
}

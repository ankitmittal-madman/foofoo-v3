/**
 * Base repository (WP-8B foundation).
 *
 * Repositories are the ONLY layer that touches the database (DOC-P4-00 §4). The base class holds
 * the service-role Supabase client + a bound logger and offers shared helpers (schema-qualified
 * table access, keyset-pagination cursor encoding). Concrete repositories (dishes, cohorts,
 * weekly plans, …) are added in later WPs — none here. No SQL and no business logic in the base.
 */
import type { SupabaseClient } from "../db/client.ts";
import type { Logger } from "../logging/logger.ts";

export interface KeysetCursor {
  /** Order-by anchor (e.g. occurred_at for interaction_events, DOC-P3-06 §09). */
  readonly occurredAt: string;
  readonly id: string;
}

export abstract class BaseRepository {
  protected readonly db: SupabaseClient;
  protected readonly logger: Logger;

  constructor(db: SupabaseClient, logger: Logger) {
    this.db = db;
    this.logger = logger.child({ component: this.constructor.name });
  }

  /** Encode a keyset cursor to an opaque string (offset pagination is forbidden on partitioned
   * tables — DOC-P3-06 §09). */
  protected encodeCursor(cursor: KeysetCursor): string {
    return btoa(`${cursor.occurredAt}|${cursor.id}`);
  }

  /** Decode an opaque keyset cursor, or null if absent/invalid. */
  protected decodeCursor(raw: string | null): KeysetCursor | null {
    if (!raw) return null;
    try {
      const [occurredAt, id] = atob(raw).split("|");
      return occurredAt && id ? { occurredAt, id } : null;
    } catch {
      return null;
    }
  }
}

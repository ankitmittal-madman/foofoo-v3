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
import { ConsentRepository } from "../repositories/consent-repository.ts";
import { ConsentService } from "../services/consent-service.ts";
import type { RequestContext } from "../types/context.ts";
import { RecommendationEngine } from "../services/re/engine.ts";
import { OnboardingOrchestrator } from "../services/onboarding/orchestrator.ts";
import {
  SupabaseCandidateRepository,
  SupabaseOnboardingStore,
  SupabaseWeekPlanStore,
} from "../services/adapters/supabase-stores.ts";
import {
  SupabaseBanditStateRepository,
  SupabaseCohortPriorRepository,
  SupabaseCohortResolutionRepository,
  SupabaseContextMultiplierRepository,
  SupabaseNeverListRepository,
  SupabasePersonalHistoryRepository,
  SupabaseReConfigProvider,
  SupabaseSuppressionRepository,
  SupabaseTasteVectorRepository,
  SystemRandom,
} from "../services/adapters/re-engine-full-adapters.ts";

/**
 * `[FLAGGED — see re-engine-full-adapters.ts module header]` Best-effort constant, not confirmed
 * against the full DOC-P3-03 §04 LF-B03 text (out of this WP's time budget). Multiple
 * `re_meal_classes.class_code` rows plausibly represent "the" non-veg main class
 * (`DN_NONVEG_HOME_DINNER`, `LD_TANDOORI_GRILL_NONVEG`, ...); this picks the one whose name most
 * closely matches "everyday non-veg main dinner" per the seeded data. Needs Founder/Engineering
 * confirmation before being trusted in production — flagged in the WP report, not silently assumed.
 */
const NON_VEG_MAIN_CLASS = "DN_NONVEG_HOME_DINNER";

/** Per-request DI container — lazily builds and caches the db client, telemetry sink, and
 * repository/service graph for the lifetime of one request (see file header). */
export class Container {
  private readonly ctx: RequestContext;
  private _db: SupabaseClient | null = null;
  private _telemetry: TelemetrySink | null = null;
  private _consentRepository: ConsentRepository | null = null;
  private _consentService: ConsentService | null = null;
  private _onboardingOrchestrator: OnboardingOrchestrator | null = null;

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

  // ── WP-8C: consent (POST /v1/consent, LF-M01) ──────────────────────────────────────────────
  get consentRepository(): ConsentRepository {
    if (this._consentRepository === null) {
      this._consentRepository = new ConsentRepository(this.db, this.ctx.logger);
    }
    return this._consentRepository;
  }

  get consentService(): ConsentService {
    if (this._consentService === null) {
      this._consentService = new ConsentService(this.ctx, this.consentRepository);
    }
    return this._consentService;
  }

  // ── Onboarding (POST /v1/onboarding, LF-A01–A09) — wires OnboardingOrchestrator to a real,
  // schema-verified EngineDeps object per re-engine-full-adapters.ts (CRITICAL audit fix). ─────────
  get onboardingOrchestrator(): OnboardingOrchestrator {
    if (this._onboardingOrchestrator === null) {
      const cohortResolution = new SupabaseCohortResolutionRepository(this.db);
      const engine = new RecommendationEngine({
        candidates: new SupabaseCandidateRepository(this.db),
        neverList: new SupabaseNeverListRepository(this.db),
        suppression: new SupabaseSuppressionRepository(this.db),
        cohortPriors: new SupabaseCohortPriorRepository(this.db),
        tasteVectors: new SupabaseTasteVectorRepository(this.db),
        personalHistory: new SupabasePersonalHistoryRepository(this.db),
        bandit: new SupabaseBanditStateRepository(this.db),
        contextMultipliers: new SupabaseContextMultiplierRepository(this.db),
        cohortResolution,
        config: new SupabaseReConfigProvider(this.db),
        rng: new SystemRandom(),
      });
      this._onboardingOrchestrator = new OnboardingOrchestrator(
        new SupabaseOnboardingStore(this.db),
        cohortResolution,
        engine,
        new SupabaseWeekPlanStore(this.db),
        "classfirst_v1", // matches the live re_engine_versions.is_active row (confirmed via MCP)
        NON_VEG_MAIN_CLASS,
      );
    }
    return this._onboardingOrchestrator;
  }

  // Further repository/service accessors are added per-WP as concrete classes land.
}

/** Build a fresh container for a request. */
export function createContainer(ctx: RequestContext): Container {
  return new Container(ctx);
}

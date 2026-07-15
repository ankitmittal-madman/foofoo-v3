/**
 * Recommendation Engine — orchestrator (WP-8D).
 *
 * The single reusable RE core (RE-DOC-01 isolation; DOC-P4-00 §5/§14; DCR-P3-06-007). It owns ALL
 * recommendation decisions and is invoked identically by every caller — /v1/recommendations, the
 * nightly plan job, and (per DOC-P3-02 Domain Events "PlanPreviewGenerated", actor = RE Engine) the
 * onboarding orchestrator. Callers never duplicate this logic; they only supply inputs and persist
 * the output. Dependencies arrive as ports (DI, DOC-P4-00 §20), so the engine is DB-agnostic and
 * unit-testable with fakes.
 *
 * Single-slot pipeline (DOC-P3-03 §02 Stages 5–8): candidates (LF-D01) → hard constraints
 * (LF-D02–D06) → [fallback LF-D07] → score (LF-E01–E08) → MMR (LF-F01) → safety gates (LF-H01–H03).
 * Week assembly (LF-L01 body, minus persistence): class plan (LF-B02/B03) → per-slot slate.
 */
import type {
  DishCandidate,
  GeneratedWeekPlan,
  HouseholdConstraints,
  HouseholdMember,
  MealSlot,
  RecommendationContext,
  ScoredCandidate,
  Slate,
  UserReState,
} from "./types.ts";
import type {
  BanditStateRepository,
  CandidateRepository,
  CohortPriorRepository,
  CohortResolutionRepository,
  ContextMultiplierRepository,
  NeverListRepository,
  PersonalHistoryRepository,
  Random,
  ReConfigProvider,
  SuppressionRepository,
  TasteVectorRepository,
} from "./ports.ts";
import { applyHardConstraints, combinedAllergenFlags } from "./constraints.ts";
import {
  cohortPrior,
  contentMatch,
  contextFit,
  explorationBonus,
  finalScore,
  interpolateWeightLadder,
  notTodayPenalty,
  personalHistory,
} from "./scoring.ts";
import { applyMmr } from "./variety.ts";
import { runSafetyGates, type SafetyViolation } from "./safety.ts";
import { classForSlot, resolveWeeklyClassPlan } from "./resolvers.ts";

/** All ports the engine needs (constructor-injected). */
export interface EngineDeps {
  readonly candidates: CandidateRepository;
  readonly neverList: NeverListRepository;
  readonly suppression: SuppressionRepository;
  readonly cohortPriors: CohortPriorRepository;
  readonly tasteVectors: TasteVectorRepository;
  readonly personalHistory: PersonalHistoryRepository;
  readonly bandit: BanditStateRepository;
  readonly contextMultipliers: ContextMultiplierRepository;
  readonly cohortResolution: CohortResolutionRepository;
  readonly config: ReConfigProvider;
  readonly rng: Random;
}

/** Inputs shared across a request (resolved once, reused per slot). */
export interface SlotRequest {
  readonly user: UserReState;
  readonly constraints: HouseholdConstraints;
  readonly members: HouseholdMember[];
  readonly context: RecommendationContext;
  readonly classCode: string;
  /** Dishes already placed in the plan this week (LF-D01 exclude / variety awareness). */
  readonly excludeDishIds?: Set<string>;
}

export class RecommendationEngine {
  private readonly d: EngineDeps;

  constructor(deps: EngineDeps) {
    this.d = deps;
  }

  /**
   * Generate one slate for a single plan slot (the core pipeline). Safety gates run last; if a
   * gate flags a dish the slate is rejected and rebuilt from the fallback (LF-D07) rather than
   * ever serving a violating dish (§02 Stage 8 discipline).
   */
  async generateSlate(req: SlotRequest): Promise<Slate> {
    const cfg = await this.d.config.getScoringConfig();
    const reVersion = await this.d.config.getActiveReVersion();
    const combined = combinedAllergenFlags(req.constraints.allergenFlags, req.members);
    const neverIds = await this.d.neverList.getActiveNeverDishIds(req.user.profileId);

    // Stage 5 — candidates + 6 hard constraints (LF-D01–D06).
    const raw = await this.d.candidates.getClassCandidates(req.classCode);
    let pool = applyHardConstraints(raw, {
      dietType: req.constraints.dietType,
      religiousPref: req.constraints.religiousPref,
      combinedAllergenFlags: combined,
      mealSlot: req.context.mealSlot,
      activeNeverIds: neverIds,
    });
    if (req.excludeDishIds) pool = pool.filter((c) => !req.excludeDishIds!.has(c.dishId));

    // LF-D07 — coverage gap: fewer than the minimum survivors → static popular fallback.
    let fallbackUsed = false;
    if (pool.length < cfg.minCandidates) {
      fallbackUsed = true;
      const fb = await this.d.candidates.getPopularFallback(
        req.constraints.dietType,
        cfg.slateSize,
      );
      // The fallback is diet-filtered only; still enforce allergen + never (safety-critical).
      pool = fb.filter((c) =>
        (c.ingredientAllergenUnion & combined) === 0 && !neverIds.has(c.dishId)
      );
    }

    // Stages 6–7 — score every survivor, then MMR to the slate size.
    const scored = await this.scorePool(pool, req, cfg);
    const slate = applyMmr(scored, cfg.mmrLambda, cfg.slateSize);

    // Stage 8 — safety gates (defense in depth). A violation should be impossible after the hard
    // constraints, but if one appears the offending dish is dropped and the gate re-checked.
    const safe = this.enforceSafety(slate, {
      dietType: req.constraints.dietType,
      religiousPref: req.constraints.religiousPref,
      combinedAllergenFlags: combined,
    });

    const ranked = safe.map((s, i) => ({
      dishId: s.candidate.dishId,
      rank: i + 1,
      score: s.score,
      reasonTags: reasonTags(s, req.context),
    }));
    return {
      mealSlot: req.context.mealSlot,
      slotDate: req.context.slotDate,
      classCode: req.classCode,
      ranked,
      dishIds: ranked.map((r) => r.dishId),
      reasonTags: Object.fromEntries(ranked.map((r) => [r.dishId, r.reasonTags])),
      confidence: req.user.confidenceScore,
      coldStartMode: req.user.coldStartMode,
      reVersion,
      fallbackUsed,
    };
  }

  /**
   * Assemble a full week plan in memory (LF-L01 body). Resolves the cohort's class plan and
   * generates one slate per slot. Persistence of week_plans/plan_slots is the CALLER's concern
   * (DOC-P3-02: RE Engine generates; a repository persists) — the engine returns a plain object.
   */
  async generateWeekPlan(
    user: UserReState,
    constraints: HouseholdConstraints,
    members: HouseholdMember[],
    weekStartDate: string,
    contextForSlot: (slotDate: string, mealSlot: MealSlot) => RecommendationContext,
    opts: { nonVegMainClass: string },
  ): Promise<GeneratedWeekPlan> {
    const reVersion = await this.d.config.getActiveReVersion();

    // LF-B02/B03 — weekly class plan (+ non-veg overlay). Reuses the resolver over the port.
    const assignments = await resolveWeeklyClassPlan(
      this.d.cohortResolution,
      user.cohortId,
      weekStartDate,
      {
        dietType: constraints.dietType,
        homeState: constraints.homeState,
        nonVegMainClass: opts.nonVegMainClass,
      },
    );

    const placed = new Set<string>();
    const slots: Slate[] = [];
    for (const a of assignments) {
      const classCode = classForSlot(assignments, a.slotDate, a.mealSlot) ?? a.classCode;
      const slate = await this.generateSlate({
        user,
        constraints,
        members,
        context: contextForSlot(a.slotDate, a.mealSlot),
        classCode,
        excludeDishIds: placed,
      });
      // Track the headline dish to bias toward across-week variety (LF-F02 same_dish window).
      if (slate.dishIds[0]) placed.add(slate.dishIds[0]);
      slots.push(slate);
    }

    return {
      profileId: user.profileId,
      weekStartDate,
      reVersion,
      coldStartMode: user.coldStartMode,
      slots,
    };
  }

  /** Score every candidate in the pool (LF-E01–E08). */
  private async scorePool(
    pool: DishCandidate[],
    req: SlotRequest,
    cfg: Awaited<ReturnType<ReConfigProvider["getScoringConfig"]>>,
  ): Promise<ScoredCandidate[]> {
    const ladder = await this.d.config.getWeightLadder();
    const weights = interpolateWeightLadder(req.user.interactionCount, ladder);

    // LF-E03 — user taste vector; cold start uses the cohort average.
    let userVector = await this.d.tasteVectors.getUserTasteVector(req.user.profileId);
    if (!userVector || req.user.coldStartMode) {
      userVector = await this.d.tasteVectors.getCohortAverageVector(req.user.cohortId);
    }

    const rawPrior = await this.d.cohortPriors.getPrior(req.user.cohortId, req.classCode);
    const cp = cohortPrior(rawPrior, cfg); // neutral 0.50 fallback if unseeded (documented MVP limit)
    const notToday = await this.d.suppression.getActiveNotToday(req.user.profileId);
    const notTodayByDish = new Map(notToday.map((n) => [n.dishId, n.daysElapsed]));

    const scored: ScoredCandidate[] = [];
    for (const dish of pool) {
      const cm = contentMatch(userVector, dish.genomeVector);
      const events = await this.d.personalHistory.getEvents(req.user.profileId, dish.dishId);
      // Pre-resolve event weights (config port is async; personalHistory stays pure/sync).
      const weightCache = new Map<string, number>();
      for (const e of events) {
        const key = `${e.eventType}|${e.rating ?? ""}`;
        if (!weightCache.has(key)) {
          weightCache.set(key, await this.d.config.getEventWeight(e.eventType, e.rating));
        }
      }
      const ph = personalHistory(
        events,
        (t, r) => weightCache.get(`${t}|${r ?? ""}`) ?? 0,
        cfg,
      );
      const ctxMultipliers = await this.gatherContextMultipliers(dish, req.context);
      const cf = contextFit(dish, ctxMultipliers, req.context.dayType);
      const beta = await this.d.bandit.getBetaParams(req.user.profileId, dish.dishId);
      const eb = explorationBonus(beta.alpha, beta.beta, cfg, this.d.rng);
      const penalty = notTodayByDish.has(dish.dishId)
        ? notTodayPenalty(notTodayByDish.get(dish.dishId)!, cf, cfg)
        : 0;

      const signals = {
        cohortPrior: cp,
        contentMatch: cm,
        personalHistory: ph,
        contextFit: cf,
        explorationBonus: eb,
        penalty,
      };
      scored.push({ candidate: dish, score: finalScore(weights, signals), signals });
    }
    return scored;
  }

  /** Resolve a dish's context multipliers for the current weather/season (LF-E05). */
  private async gatherContextMultipliers(
    dish: DishCandidate,
    ctx: RecommendationContext,
  ): Promise<number[]> {
    const out: number[] = [];
    if (ctx.weather) {
      out.push(
        await this.d.contextMultipliers.getMultiplier("weather", ctx.weather, dish.cookingMethod),
      );
    }
    if (ctx.season && dish.seasonalAffinity.includes(ctx.season)) {
      out.push(
        await this.d.contextMultipliers.getMultiplier("season", ctx.season, dish.cuisineFamily),
      );
    }
    return out;
  }

  /** Enforce safety gates over the slate; drop any violating dish (should be none). */
  private enforceSafety(
    slate: ScoredCandidate[],
    p: {
      dietType: HouseholdConstraints["dietType"];
      religiousPref: HouseholdConstraints["religiousPref"];
      combinedAllergenFlags: number;
    },
  ): ScoredCandidate[] {
    const violations: SafetyViolation[] = runSafetyGates(slate.map((s) => s.candidate), p);
    if (violations.length === 0) return slate;
    const bad = new Set(violations.map((v) => v.dishId));
    return slate.filter((s) => !bad.has(s.candidate.dishId));
  }
}

/**
 * Derive slate reason tags from the dominant scoring signals (DOC-P3-06 §06.4 `reason_tags`,
 * stored to suggestion_logs.slate_reasons). Implementation convention (DCR-class): the tag is the
 * name of the signal(s) that contributed most — a faithful summary, not invented business logic.
 */
function reasonTags(s: ScoredCandidate, ctx: RecommendationContext): string[] {
  const tags: string[] = [];
  const sig = s.signals;
  if (sig.contextFit >= 0.9) tags.push(ctx.weather ? "weather" : "context");
  if (sig.personalHistory > 0.2) tags.push("history");
  if (sig.cohortPrior >= 0.6) tags.push("cohort");
  if (sig.contentMatch >= 0.6) tags.push("content");
  if (tags.length === 0) tags.push("cohort"); // cold-start default: cohort-driven
  return tags;
}

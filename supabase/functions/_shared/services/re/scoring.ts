/**
 * Recommendation Engine — scoring (WP-8D).
 *
 * DOC-P3-03 §07 (LF-E01–E08). Pure, deterministic functions except the exploration bonus (LF-E06),
 * which draws from a Beta distribution using an INJECTED Random (deterministic in tests). All
 * numeric parameters arrive via config (§16 Working Principle 7) — none are hardcoded here.
 */
import type {
  DishCandidate,
  InteractionEvent,
  ScoringConfig,
  ScoringWeights,
  WeightLadderTier,
} from "./types.ts";
import type { Random } from "./ports.ts";

/**
 * LF-E01 — interpolate scoring weights from interaction_count with linear interpolation between the
 * bracketing tier rows (DOC-P3-03 §07). Computed at request time, never stored.
 */
export function interpolateWeightLadder(
  interactionCount: number,
  ladder: WeightLadderTier[],
): ScoringWeights {
  const sorted = [...ladder].sort((a, b) => a.lowerBound - b.lowerBound);
  const first = sorted[0];
  const last = sorted[sorted.length - 1];
  if (interactionCount <= first.lowerBound) return first.weights;
  if (interactionCount >= last.upperBound) return last.weights;

  const tier =
    sorted.find((t) => interactionCount >= t.lowerBound && interactionCount <= t.upperBound) ??
      last;
  const span = tier.upperBound - tier.lowerBound;
  const progress = span === 0 ? 0 : (interactionCount - tier.lowerBound) / span;

  // Interpolate toward the NEXT tier's weights (smooth transition across the boundary).
  const idx = sorted.indexOf(tier);
  const next = sorted[Math.min(idx + 1, sorted.length - 1)];
  const lerp = (a: number, b: number) => a + progress * (b - a);
  return {
    wCohort: lerp(tier.weights.wCohort, next.weights.wCohort),
    wContent: lerp(tier.weights.wContent, next.weights.wContent),
    wHistory: lerp(tier.weights.wHistory, next.weights.wHistory),
    wContext: lerp(tier.weights.wContext, next.weights.wContext),
    wExplore: lerp(tier.weights.wExplore, next.weights.wExplore),
  };
}

/**
 * LF-E02 — CohortPrior lookup with the documented neutral fallback. When the research table
 * (re_cohort_class_priors) has no row — including the current MVP state where it is unseeded — the
 * neutral prior (0.50) is used and the gap is the caller's to log. See ScoringConfig.neutralCohortPrior.
 */
export function cohortPrior(rawPrior: number | null, cfg: ScoringConfig): number {
  return rawPrior ?? cfg.neutralCohortPrior;
}

/** LF-E03 — cosine similarity between the user taste vector and a dish genome vector (0–1). */
export function contentMatch(userVector: number[], dishVector: number[]): number {
  const n = Math.min(userVector.length, dishVector.length);
  let dot = 0;
  let magA = 0;
  let magB = 0;
  for (let i = 0; i < n; i++) {
    dot += userVector[i] * dishVector[i];
    magA += userVector[i] * userVector[i];
    magB += dishVector[i] * dishVector[i];
  }
  if (magA === 0 || magB === 0) return 0;
  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
}

/**
 * LF-E04 — PersonalHistory: time-decayed weighted sum of prior interactions with this dish.
 * event_weight × e^(−λ_history × days_elapsed). `dish_not_today` carries its own faster fade
 * (−0.10 × e^(−0.35 t)) per §07 note (distinct from the LF-E08 Not-Today penalty). Range −1..+1.
 */
export function personalHistory(
  events: InteractionEvent[],
  eventWeightOf: (eventType: string, rating: number | null) => number,
  cfg: ScoringConfig,
): number {
  let sum = 0;
  for (const e of events) {
    if (e.eventType === "dish_not_today") {
      sum += -0.10 * Math.exp(-cfg.notTodayLambda * e.daysElapsed);
      continue;
    }
    const w = eventWeightOf(e.eventType, e.rating);
    sum += w * Math.exp(-cfg.personalHistoryLambda * e.daysElapsed);
  }
  return Math.max(-1, Math.min(1, sum));
}

/**
 * LF-E05 — ContextFit: sum of matched context-attribute multipliers (weather/season/day/cook-time).
 * Multiplier values are config (re_context_multipliers). Range 0–1.2. `multiplierFor` is supplied by
 * the engine (which reads the multiplier port); this keeps the math pure and testable.
 */
export function contextFit(
  dish: DishCandidate,
  matchedMultipliers: number[],
  dayType: "weekday" | "weekend",
): number {
  let fit = matchedMultipliers.reduce((a, m) => a + m, 0);
  // Weekday cook-time boost (LF-E05): favour ≤30-min dishes on weekdays; weekend = no restriction.
  if (dayType === "weekday" && dish.cookTimeBandMinutes <= 30) fit += 0.1;
  return Math.max(0, Math.min(1.2, fit));
}

/**
 * LF-E06 — ExplorationBonus: Thompson-sampling draw from Beta(α,β), scaled to [0, exploration_max].
 * Uses an injected Random so tests are deterministic. Beta is sampled via two Gamma draws
 * (Marsaglia–Tsang); Beta(1,1) reduces to Uniform(0,1).
 */
export function explorationBonus(
  alpha: number,
  beta: number,
  cfg: ScoringConfig,
  rng: Random,
): number {
  const sample = sampleBeta(alpha, beta, rng);
  return sample * cfg.explorationBonusMax;
}

/** α/β update rule (LF-E06): accept/lock/cooked → α+1; swiped_past/not_today → β+1. */
export function updateBanditParams(
  alpha: number,
  beta: number,
  eventType: string,
): { alpha: number; beta: number } {
  if (["dish_accepted", "dish_locked", "dish_cooked"].includes(eventType)) {
    return { alpha: alpha + 1, beta };
  }
  if (["dish_swiped_past", "dish_not_today"].includes(eventType)) {
    return { alpha, beta: beta + 1 };
  }
  return { alpha, beta };
}

/**
 * LF-E07 — Not-Today penalty at recommendation time: P0 × e^(−λ t). Below the decay threshold the
 * suppression is considered expired (0). Context override (t≥3 and ContextFit>threshold) halves it.
 */
export function notTodayPenalty(
  daysElapsed: number,
  contextFitValue: number,
  cfg: ScoringConfig,
): number {
  let penalty = cfg.notTodayP0 * Math.exp(-cfg.notTodayLambda * daysElapsed);
  if (penalty < cfg.notTodayDecayThreshold) return 0;
  if (daysElapsed >= 3 && contextFitValue > cfg.contextOverrideThreshold) penalty *= 0.5;
  return penalty;
}

/**
 * LF-E08 — assemble the FinalScore from the five weighted signals minus the penalty
 * (hard constraints are assumed already passed — never bypassed).
 */
export function finalScore(
  weights: ScoringWeights,
  signals: {
    cohortPrior: number;
    contentMatch: number;
    personalHistory: number;
    contextFit: number;
    explorationBonus: number;
    penalty: number;
  },
): number {
  return (
    weights.wCohort * signals.cohortPrior +
    weights.wContent * signals.contentMatch +
    weights.wHistory * signals.personalHistory +
    weights.wContext * signals.contextFit +
    weights.wExplore * signals.explorationBonus -
    signals.penalty
  );
}

// ── Beta / Gamma sampling (Marsaglia–Tsang) ─────────────────────────────────────────────────────

/** Beta(a,b) = X/(X+Y), X~Gamma(a,1), Y~Gamma(b,1). */
export function sampleBeta(a: number, b: number, rng: Random): number {
  const x = sampleGamma(a, rng);
  const y = sampleGamma(b, rng);
  return x + y === 0 ? 0 : x / (x + y);
}

/** Gamma(shape, 1) via Marsaglia–Tsang; handles shape<1 via the boost transform. */
export function sampleGamma(shape: number, rng: Random): number {
  if (shape < 1) {
    const u = rng.uniform();
    return sampleGamma(shape + 1, rng) * Math.pow(u, 1 / shape);
  }
  const d = shape - 1 / 3;
  const c = 1 / Math.sqrt(9 * d);
  while (true) {
    const x = rng.normal();
    let v = 1 + c * x;
    if (v <= 0) continue;
    v = v * v * v;
    const u = rng.uniform();
    if (u < 1 - 0.0331 * x * x * x * x) return d * v;
    if (Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v;
  }
}

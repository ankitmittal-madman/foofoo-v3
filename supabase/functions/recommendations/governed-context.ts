import type { HouseholdRaw } from "./compose.ts";

export type GovernedContextSignal = {
  feature_code: "health_objective" | "working_professionals" | "weekday_time_pressure";
  value: unknown;
  authority: "explicit" | "inferred";
  confidence: number;
  sources: string[];
  allowed_use: "strong_rank" | "soft_rank" | "context_input";
  created_at?: string | null;
  expires_at?: string | null;
  correction_state: "active" | "confirmed" | "rejected";
  feature_version: "governed-context-v1";
};

const OBJECTIVES = new Set([
  "awesome_taste",
  "healthy_living",
  "into_fitness",
  "protein_calculator",
]);

function bounded(value: number): number {
  return Math.max(0, Math.min(1, value));
}

/**
 * Build only policy-approved context. Geography and member age never imply profession, disease,
 * income, diet, or medical restrictions. The inferred feature is intentionally a small scheduling
 * hypothesis; it cannot enter safety eligibility.
 */
export function deriveGovernedContextSignals(household: HouseholdRaw): GovernedContextSignal[] {
  const objective = OBJECTIVES.has(household.q15_objective)
    ? household.q15_objective
    : "awesome_taste";
  const workers = Math.max(0, Math.min(20, Math.trunc(household.q2_working_professionals || 0)));
  const adults = Math.max(
    1,
    household.q12_member_ages.filter((member) => Number(member.age) >= 18).length,
  );
  const hasDependents = household.q12_member_ages.some((member) => Number(member.age) < 18);
  const cooksAtHome = household.q13_who_cooks === "self" || household.q13_who_cooks === "family";
  const pressure = bounded(
    0.10 + 0.45 * Math.min(1, workers / adults) + (hasDependents ? 0.15 : 0) +
      (cooksAtHome ? 0.15 : 0),
  );
  const pressureSources = ["q2_working_professionals", "q13_who_cooks"];
  if (hasDependents) pressureSources.push("q12_member_ages");

  return [
    {
      feature_code: "health_objective",
      value: objective,
      authority: "explicit",
      confidence: 1,
      sources: ["q15_objective"],
      allowed_use: "strong_rank",
      correction_state: "active",
      feature_version: "governed-context-v1",
    },
    {
      feature_code: "working_professionals",
      value: workers,
      authority: "explicit",
      confidence: 1,
      sources: ["q2_working_professionals"],
      allowed_use: "context_input",
      correction_state: "active",
      feature_version: "governed-context-v1",
    },
    {
      feature_code: "weekday_time_pressure",
      value: Number(pressure.toFixed(4)),
      authority: "inferred",
      confidence: 0.65,
      sources: pressureSources,
      allowed_use: "soft_rank",
      correction_state: "active",
      feature_version: "governed-context-v1",
    },
  ];
}

export function extractGovernedContextSignals(value: unknown): GovernedContextSignal[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is GovernedContextSignal => {
    if (!item || typeof item !== "object") return false;
    const row = item as Record<string, unknown>;
    return ["health_objective", "working_professionals", "weekday_time_pressure"].includes(
      String(row.feature_code),
    ) && ["explicit", "inferred"].includes(String(row.authority)) &&
      typeof row.confidence === "number" && row.confidence >= 0 && row.confidence <= 1 &&
      Array.isArray(row.sources) && row.sources.length > 0 &&
      ["strong_rank", "soft_rank", "context_input"].includes(String(row.allowed_use)) &&
      ["active", "confirmed"].includes(String(row.correction_state)) &&
      row.feature_version === "governed-context-v1";
  }).slice(0, 20);
}

export function mergeGovernedContextSignals(
  derived: GovernedContextSignal[],
  stored: GovernedContextSignal[],
): GovernedContextSignal[] {
  const byCode = new Map(derived.map((signal) => [signal.feature_code, signal]));
  for (const signal of stored) byCode.set(signal.feature_code, signal);
  return [...byCode.values()].sort((left, right) =>
    left.feature_code.localeCompare(right.feature_code)
  );
}

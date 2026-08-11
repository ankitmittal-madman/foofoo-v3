/** Pure normalization of external food evidence into governed Foofoo facts. */
import type { ResearchRecord } from "./research.ts";

export interface ExternalFoodTerm {
  code: string;
  label: string;
  iri: string;
  aliases: string[];
  confidence: number;
}

export interface ExternalAlias {
  label: string;
  source: string;
  confidence: number;
}

export interface ExternalNutrient {
  code: "energy_kcal" | "protein_g" | "fat_g" | "carbohydrate_g";
  displayName: string;
  unit: "kcal" | "g";
  value: number;
  servingBasis: string;
  confidence: number;
}

const NUTRIENT_NAMES: Record<string, Omit<ExternalNutrient, "value" | "confidence">> = {
  energy: { code: "energy_kcal", displayName: "Energy", unit: "kcal", servingBasis: "100 g" },
  protein: { code: "protein_g", displayName: "Protein", unit: "g", servingBasis: "100 g" },
  "total lipid (fat)": {
    code: "fat_g",
    displayName: "Total fat",
    unit: "g",
    servingBasis: "100 g",
  },
  "carbohydrate, by difference": {
    code: "carbohydrate_g",
    displayName: "Carbohydrate",
    unit: "g",
    servingBasis: "100 g",
  },
};

function strings(value: unknown): string[] {
  if (Array.isArray(value)) return value.filter((item): item is string => typeof item === "string");
  return typeof value === "string" ? [value] : [];
}

/** Extract the leading FoodOn match and synonyms without treating it as accepted product truth. */
export function normalizeFoodOn(record: ResearchRecord): ExternalFoodTerm | null {
  if (record.provider !== "foodon_ols") return null;
  const response = record.payload.response as Record<string, unknown> | undefined;
  const docs = Array.isArray(response?.docs) ? response.docs as Record<string, unknown>[] : [];
  const first = docs[0];
  const iri = typeof first?.iri === "string" ? first.iri : record.providerRecordId;
  const label = typeof first?.label === "string" ? first.label : null;
  if (!iri || !label) return null;
  const localId = iri.split(/[\/#]/).filter(Boolean).at(-1) ?? iri;
  // Ancestor labels (searchFoodOn's is_a hierarchy fetch) are additive alias/context signal --
  // e.g. an ancestor of "Indian food product" is useful cuisine evidence a flat top-hit match on
  // the dish's own label would never surface.
  const ancestors = strings(record.payload.ancestors);
  const aliases = [
    ...new Set(
      [
        ...strings(first.synonym),
        ...strings(first.synonyms),
        ...strings(first.label_localized),
        ...ancestors,
      ].map((item) => item.trim()).filter((item) =>
        item && item.toLowerCase() !== label.toLowerCase()
      ),
    ),
  ];
  return {
    code: `FOODON_${localId.replace(/[^a-zA-Z0-9_]+/g, "_").toUpperCase()}`,
    label,
    iri,
    aliases,
    confidence: record.confidence,
  };
}

/** Extract a regional/vernacular alias label from the leading AGROVOC match.
 *
 * AGROVOC is a vocabulary, never a nutrient source -- there is deliberately no normalizeAgrovoc
 * path into ExternalNutrient, mirroring normalizeUsda's confidence gate for the same reason
 * FoodOn's own aliases are staged as evidence, not accepted as product truth automatically.
 */
export function normalizeAgrovoc(record: ResearchRecord): ExternalAlias | null {
  if (record.provider !== "agrovoc") return null;
  const results = Array.isArray(record.payload.results)
    ? record.payload.results as Record<string, unknown>[]
    : [];
  const first = results[0];
  const label = typeof first?.prefLabel === "string" ? first.prefLabel : null;
  if (!label) return null;
  return { label, source: "agrovoc", confidence: record.confidence };
}

/** Extract the best-match IFCT (ICMR-NIN) nutrient row for a dish name via public.match_ifct_nutrients.
 *
 * Unlike the other normalizers here, IFCT has no external HTTP API -- match_ifct_nutrients is a
 * DB-side trigram lookup (migration 128) against ifct_nutrient_reference, which is empty until the
 * Founder supplies the real dataset. Call sites must treat a null/empty result as "no IFCT match
 * yet", not an error.
 */
export function normalizeIfctRow(
  row: Record<string, unknown> | null | undefined,
): ExternalNutrient[] {
  if (!row) return [];
  const similarity = Number(row.similarity);
  const results: ExternalNutrient[] = [];
  const push = (
    code: ExternalNutrient["code"],
    displayName: string,
    unit: ExternalNutrient["unit"],
    rawValue: unknown,
  ) => {
    const value = Number(rawValue);
    if (Number.isFinite(value) && value >= 0) {
      results.push({
        code,
        displayName,
        unit,
        value,
        servingBasis: "100 g",
        confidence: similarity,
      });
    }
  };
  push("energy_kcal", "Energy", "kcal", row.energy_kcal);
  push("protein_g", "Protein", "g", row.protein_g);
  push("fat_g", "Total fat", "g", row.fat_g);
  push("carbohydrate_g", "Carbohydrate", "g", row.carbohydrate_g);
  return results;
}

/** Extract the four recommendation-safe macro values from the leading USDA result. */
export function normalizeUsda(record: ResearchRecord): ExternalNutrient[] {
  if (record.provider !== "usda_fdc") return [];
  // Search results are not composition authority unless the provider label is an exact normalized
  // match. This blocks cases such as "Poha" resolving to cape gooseberries or "Butter Chicken"
  // resolving to clarified butter. Exact matches remain provisional evidence, never product truth.
  if (record.confidence < 0.9) return [];
  const foods = Array.isArray(record.payload.foods)
    ? record.payload.foods as Record<string, unknown>[]
    : [];
  const first = foods[0];
  const nutrients = Array.isArray(first?.foodNutrients)
    ? first.foodNutrients as Record<string, unknown>[]
    : [];
  const normalized = new Map<ExternalNutrient["code"], ExternalNutrient>();
  for (const nutrient of nutrients) {
    const name = typeof nutrient.nutrientName === "string"
      ? nutrient.nutrientName.toLowerCase()
      : "";
    const definition = NUTRIENT_NAMES[name];
    const value = Number(nutrient.value);
    if (!definition || !Number.isFinite(value) || value < 0) continue;
    const sourceUnit = typeof nutrient.unitName === "string" ? nutrient.unitName.toLowerCase() : "";
    if (definition.unit === "kcal" && sourceUnit !== "kcal") continue;
    normalized.set(definition.code, { ...definition, value, confidence: record.confidence });
  }
  return [...normalized.values()];
}

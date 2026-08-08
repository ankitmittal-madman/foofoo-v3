/** Free-tier Groq adapter for low-risk dish ontology enrichment.
 *
 * Only public catalogue names are sent. The schema deliberately excludes nutrition, allergens,
 * religious/clinical suitability and other safety facts. Results remain versioned evidence and
 * are promoted only by the database-governed confidence policy.
 */
import type { FetchLike, ResearchRecord } from "./research.ts";
import { normalizeFoodName } from "./research.ts";

export interface GroqUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export interface GroqDishEnrichment {
  aliases: Array<{
    name: string;
    language: string;
    region: string | null;
    alias_type:
      | "regional_name"
      | "common_name"
      | "transliteration"
      | "english_gloss"
      | "spelling_variant";
    confidence: number;
  }>;
  taxonomy: Array<{
    dimension:
      | "cooking_method"
      | "spice_level"
      | "heaviness"
      | "texture"
      | "richness"
      | "weather_affinity";
    code: string;
    label: string;
    confidence: number;
  }>;
  regional_affinities: Array<{
    region_code: string;
    affinity_score: number;
    confidence: number;
  }>;
  // Meal-class and cuisine are structural catalogue-membership facts, not taxonomy descriptors —
  // kept as separate arrays/fields so the DB promotion policy (record_ai_low_risk_enrichment,
  // migration 104) can validate each against its own closed vocabulary (public.meal_classes,
  // public.cuisines) rather than inserting free-text into a foreign-keyed column. Like taxonomy,
  // this is deliberately non-safety: no diet/Jain/allergen inference, matching the ai.ts header.
  meal_class: Array<{
    class_code: string;
    slot: "breakfast" | "lunch" | "dinner" | "snack";
    confidence: number;
  }>;
  cuisine: {
    cuisine_name: string;
    confidence: number;
  } | null;
}

export interface GroqEnrichmentResult {
  record: ResearchRecord;
  enrichment: GroqDishEnrichment;
  usage: GroqUsage;
  responseId: string | null;
  model: string;
}

const GROQ_URL = "https://api.groq.com/openai/v1/chat/completions";
const GROQ_TIMEOUT_MS = 15_000;

const OUTPUT_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["aliases", "taxonomy", "regional_affinities", "meal_class", "cuisine"],
  properties: {
    aliases: {
      type: "array",
      maxItems: 8,
      items: {
        type: "object",
        additionalProperties: false,
        required: ["name", "language", "region", "alias_type", "confidence"],
        properties: {
          name: { type: "string", minLength: 2, maxLength: 160 },
          language: { type: "string", minLength: 2, maxLength: 40 },
          region: { type: ["string", "null"], maxLength: 80 },
          alias_type: {
            type: "string",
            enum: [
              "regional_name",
              "common_name",
              "transliteration",
              "english_gloss",
              "spelling_variant",
            ],
          },
          confidence: { type: "number", minimum: 0, maximum: 1 },
        },
      },
    },
    taxonomy: {
      type: "array",
      maxItems: 12,
      items: {
        type: "object",
        additionalProperties: false,
        required: ["dimension", "code", "label", "confidence"],
        properties: {
          dimension: {
            type: "string",
            enum: [
              "cooking_method",
              "spice_level",
              "heaviness",
              "texture",
              "richness",
              "weather_affinity",
            ],
          },
          code: { type: "string", pattern: "^[a-z0-9]+(?:_[a-z0-9]+)*$", maxLength: 80 },
          label: { type: "string", minLength: 2, maxLength: 120 },
          confidence: { type: "number", minimum: 0, maximum: 1 },
        },
      },
    },
    regional_affinities: {
      type: "array",
      maxItems: 3,
      items: {
        type: "object",
        additionalProperties: false,
        required: ["region_code", "affinity_score", "confidence"],
        properties: {
          region_code: {
            type: "string",
            pattern: "^[a-z0-9]+(?:_[a-z0-9]+)*$",
            maxLength: 80,
          },
          affinity_score: { type: "number", minimum: 0, maximum: 1 },
          confidence: { type: "number", minimum: 0, maximum: 1 },
        },
      },
    },
    // class_code/cuisine_name are intentionally NOT enum-constrained here: public.meal_classes
    // has 131+ rows and public.cuisines is large and grows independently of this file. The closed-
    // vocabulary check happens in record_ai_low_risk_enrichment (DB-side, always current), not in
    // this static schema — an unrecognized code is recorded as a candidate but never published.
    meal_class: {
      type: "array",
      maxItems: 3,
      items: {
        type: "object",
        additionalProperties: false,
        required: ["class_code", "slot", "confidence"],
        properties: {
          class_code: { type: "string", pattern: "^[A-Z0-9]+(?:_[A-Z0-9]+)*$", maxLength: 80 },
          slot: { type: "string", enum: ["breakfast", "lunch", "dinner", "snack"] },
          confidence: { type: "number", minimum: 0, maximum: 1 },
        },
      },
    },
    cuisine: {
      type: ["object", "null"],
      additionalProperties: false,
      required: ["cuisine_name", "confidence"],
      properties: {
        cuisine_name: { type: "string", pattern: "^[a-z0-9]+(?:_[a-z0-9]+)*$", maxLength: 80 },
        confidence: { type: "number", minimum: 0, maximum: 1 },
      },
    },
  },
} as const;

function numberOrZero(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? Math.max(0, value) : 0;
}

const REGION_CODE_ALIASES: Record<string, string> = {
  in_rajasthan: "rajasthan",
  in_punjab: "punjab",
  in_maharashtra: "maharashtra",
  in_gujarat: "gujarat",
  in_kerala: "kerala",
  in_karnataka: "karnataka",
  in_tamil_nadu: "tamil_nadu",
  in_west_bengal: "west_bengal",
  in_uttar_pradesh: "uttar_pradesh",
  in_north_india: "north_india",
  in_south_india: "south_india",
  in_east_india: "east_india",
  in_west_india: "west_india",
  india_hyderabad: "hyderabad",
  india_delhi: "delhi",
  india_goa: "goa",
  it: "italy",
};

/** Reject deterministic alias errors and normalize provider-specific region shorthand. */
export function sanitizeGroqEnrichment(
  dishName: string,
  enrichment: GroqDishEnrichment,
): GroqDishEnrichment {
  const canonical = normalizeFoodName(dishName);
  const canonicalWords = canonical.split(" ");
  const aliasSeen = new Set<string>();
  const aliases = (Array.isArray(enrichment.aliases) ? enrichment.aliases : []).filter((alias) => {
    const normalized = normalizeFoodName(alias.name);
    if (!normalized || normalized === canonical || aliasSeen.has(normalized)) return false;
    if (
      canonicalWords.length > 1 && !normalized.includes(" ") && canonicalWords.includes(normalized)
    ) {
      return false;
    }
    aliasSeen.add(normalized);
    return true;
  });
  const taxonomySeen = new Set<string>();
  const taxonomy = (Array.isArray(enrichment.taxonomy) ? enrichment.taxonomy : []).filter(
    (item) => {
      const key = `${item.dimension}:${item.code}`;
      if (taxonomySeen.has(key)) return false;
      taxonomySeen.add(key);
      return true;
    },
  );
  const regionSeen = new Set<string>();
  const regionalAffinities =
    (Array.isArray(enrichment.regional_affinities) ? enrichment.regional_affinities : []).map((
      item,
    ) => ({
      ...item,
      region_code: REGION_CODE_ALIASES[item.region_code] ?? item.region_code,
    })).filter((item) => {
      if (regionSeen.has(item.region_code)) return false;
      regionSeen.add(item.region_code);
      return true;
    });
  const mealClassSeen = new Set<string>();
  const mealClass = (Array.isArray(enrichment.meal_class) ? enrichment.meal_class : []).filter(
    (item) => {
      const key = `${item.class_code}:${item.slot}`;
      if (mealClassSeen.has(key)) return false;
      mealClassSeen.add(key);
      return true;
    },
  );
  const cuisine = enrichment.cuisine && typeof enrichment.cuisine.cuisine_name === "string"
    ? { ...enrichment.cuisine, cuisine_name: enrichment.cuisine.cuisine_name.toLowerCase() }
    : null;
  return { aliases, taxonomy, regional_affinities: regionalAffinities, meal_class: mealClass, cuisine };
}

export interface ClosedVocabulary {
  /** public.meal_classes.class_code, active rows only. */
  classCodes: string[];
  /** public.cuisines.name. */
  cuisineNames: string[];
}

/** Generate structured, non-safety ontology candidates for one canonical dish.
 *
 * `vocabulary` (when supplied) is listed verbatim in the prompt so the model selects meal_class
 * and cuisine values from the real closed vocabulary instead of inventing plausible-looking codes
 * that would never match public.meal_classes/public.cuisines — record_ai_low_risk_enrichment
 * (migration 104) still re-validates against the live tables regardless, since this list can go
 * stale between calls, but an unlisted model has near-zero chance of guessing a real class_code.
 */
export async function generateGroqDishEnrichment(
  dishName: string,
  apiKey: string,
  model: string,
  fetchImpl: FetchLike = globalThis.fetch as FetchLike,
  timeoutMs = GROQ_TIMEOUT_MS,
  vocabulary?: ClosedVocabulary,
): Promise<GroqEnrichmentResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(GROQ_URL, {
      method: "POST",
      headers: {
        authorization: `Bearer ${apiKey}`,
        "content-type": "application/json",
        accept: "application/json",
      },
      body: JSON.stringify({
        model,
        temperature: 0,
        max_completion_tokens: 1_200,
        reasoning_effort: "low",
        messages: [
          {
            role: "system",
            content:
              "You classify Indian food catalogue names. Return only well-known low-risk aliases, regional affinities, non-safety sensory/context taxonomy, meal-class membership (which structural class of dish this is, and which of breakfast/lunch/dinner/snack it is normally eaten in), and cuisine of origin. Never infer ingredients, nutrition, allergens, medical suitability, religious suitability, vegetarian status or alcohol — meal_class and cuisine describe catalogue structure and geographic/culinary origin only, not diet or safety. Use empty arrays or null when uncertain. Confidence must reflect factual certainty, not output fluency.",
          },
          {
            role: "user",
            content: vocabulary
              ? `Canonical dish name: ${dishName}\n\nValid meal_class class_code values (pick 0-3, only these — do not invent new ones): ${
                vocabulary.classCodes.join(", ")
              }\n\nValid cuisine cuisine_name values (pick 0-1, only these, or null — do not invent new ones): ${
                vocabulary.cuisineNames.join(", ")
              }`
              : `Canonical dish name: ${dishName}\n\n(No meal-class/cuisine vocabulary supplied this call — return empty meal_class and null cuisine.)`,
          },
        ],
        response_format: {
          type: "json_schema",
          json_schema: { name: "foofoo_dish_ontology", strict: true, schema: OUTPUT_SCHEMA },
        },
      }),
      signal: controller.signal,
    });
    if (!response.ok) {
      let providerCode = "provider_error";
      try {
        const errorPayload = await response.json() as Record<string, unknown>;
        const error = errorPayload.error as Record<string, unknown> | undefined;
        const candidate = typeof error?.code === "string"
          ? error.code
          : (typeof error?.type === "string" ? error.type : "provider_error");
        providerCode = candidate.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 50);
      } catch {
        // Never retain provider bodies; only a bounded machine-readable code is diagnostic-safe.
      }
      throw new Error(`groq_http_${response.status}:${providerCode}`);
    }
    const payload = await response.json() as Record<string, unknown>;
    const choices = Array.isArray(payload.choices)
      ? payload.choices as Record<string, unknown>[]
      : [];
    const message = choices[0]?.message as Record<string, unknown> | undefined;
    const content = typeof message?.content === "string" ? message.content : "";
    if (!content) throw new Error("groq_empty_content");
    let enrichment: GroqDishEnrichment;
    try {
      enrichment = JSON.parse(content) as GroqDishEnrichment;
    } catch {
      throw new Error("groq_invalid_json");
    }
    const sanitized = sanitizeGroqEnrichment(dishName, enrichment);
    const usagePayload = payload.usage as Record<string, unknown> | undefined;
    const usage = {
      promptTokens: numberOrZero(usagePayload?.prompt_tokens),
      completionTokens: numberOrZero(usagePayload?.completion_tokens),
      totalTokens: numberOrZero(usagePayload?.total_tokens),
    };
    const confidences = [
      ...sanitized.aliases.map((item) => item.confidence),
      ...sanitized.taxonomy.map((item) => item.confidence),
      ...sanitized.regional_affinities.map((item) => item.confidence),
      ...sanitized.meal_class.map((item) => item.confidence),
      ...(sanitized.cuisine ? [sanitized.cuisine.confidence] : []),
    ].filter((value) => typeof value === "number" && Number.isFinite(value));
    const confidence = confidences.length ? Math.max(...confidences) : 0;
    const responseId = typeof payload.id === "string" ? payload.id : null;
    return {
      enrichment: sanitized,
      usage,
      responseId,
      model,
      record: {
        provider: "groq",
        providerRecordId: responseId,
        sourceUrl: "https://console.groq.com/docs/models",
        confidence,
        payload: { model, raw_enrichment: enrichment, enrichment: sanitized, usage },
      },
    };
  } finally {
    clearTimeout(timer);
  }
}

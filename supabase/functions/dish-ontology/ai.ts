/** Free-tier Groq adapter for low-risk dish ontology enrichment.
 *
 * Only public catalogue names are sent. The schema deliberately excludes nutrition, allergens,
 * religious/clinical suitability and other safety facts. Results remain versioned evidence and
 * are promoted only by the database-governed confidence policy.
 */
import type { FetchLike, ResearchRecord } from "./research.ts";

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
    alias_type: "regional_name" | "common_name" | "transliteration" | "english_gloss" |
      "spelling_variant";
    confidence: number;
  }>;
  taxonomy: Array<{
    dimension: "cooking_method" | "spice_level" | "heaviness" | "texture" | "richness" |
      "weather_affinity";
    code: string;
    label: string;
    confidence: number;
  }>;
  regional_affinities: Array<{
    region_code: string;
    affinity_score: number;
    confidence: number;
  }>;
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
  required: ["aliases", "taxonomy", "regional_affinities"],
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
  },
} as const;

function numberOrZero(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? Math.max(0, value) : 0;
}

/** Generate structured, non-safety ontology candidates for one canonical dish. */
export async function generateGroqDishEnrichment(
  dishName: string,
  apiKey: string,
  model: string,
  fetchImpl: FetchLike = globalThis.fetch as FetchLike,
  timeoutMs = GROQ_TIMEOUT_MS,
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
        max_completion_tokens: 700,
        messages: [
          {
            role: "system",
            content:
              "You classify Indian food catalogue names. Return only well-known low-risk aliases, regional affinities and non-safety sensory/context taxonomy. Never infer ingredients, nutrition, allergens, medical suitability, religious suitability, vegetarian status or alcohol. Use empty arrays when uncertain. Confidence must reflect factual certainty, not output fluency.",
          },
          { role: "user", content: `Canonical dish name: ${dishName}` },
        ],
        response_format: {
          type: "json_schema",
          json_schema: { name: "foofoo_dish_ontology", strict: true, schema: OUTPUT_SCHEMA },
        },
      }),
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`groq_http_${response.status}`);
    const payload = await response.json() as Record<string, unknown>;
    const choices = Array.isArray(payload.choices) ? payload.choices as Record<string, unknown>[] : [];
    const message = choices[0]?.message as Record<string, unknown> | undefined;
    const content = typeof message?.content === "string" ? message.content : "";
    if (!content) throw new Error("groq_empty_content");
    let enrichment: GroqDishEnrichment;
    try {
      enrichment = JSON.parse(content) as GroqDishEnrichment;
    } catch {
      throw new Error("groq_invalid_json");
    }
    const usagePayload = payload.usage as Record<string, unknown> | undefined;
    const usage = {
      promptTokens: numberOrZero(usagePayload?.prompt_tokens),
      completionTokens: numberOrZero(usagePayload?.completion_tokens),
      totalTokens: numberOrZero(usagePayload?.total_tokens),
    };
    const confidences = [
      ...(Array.isArray(enrichment.aliases) ? enrichment.aliases : []).map((item) => item.confidence),
      ...(Array.isArray(enrichment.taxonomy) ? enrichment.taxonomy : []).map((item) => item.confidence),
      ...(Array.isArray(enrichment.regional_affinities) ? enrichment.regional_affinities : []).map(
        (item) => item.confidence,
      ),
    ].filter((value) => typeof value === "number" && Number.isFinite(value));
    const confidence = confidences.length ? Math.max(...confidences) : 0;
    const responseId = typeof payload.id === "string" ? payload.id : null;
    return {
      enrichment,
      usage,
      responseId,
      model,
      record: {
        provider: "groq",
        providerRecordId: responseId,
        sourceUrl: "https://console.groq.com/docs/models",
        confidence,
        payload: { model, enrichment, usage },
      },
    };
  } finally {
    clearTimeout(timer);
  }
}

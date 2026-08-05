/** External food-research adapters used by the dish ontology ingestion workflow.
 *
 * FoodOn/OLS supplies ontology identifiers and synonyms. USDA FoodData Central supplies optional
 * food/nutrient matches when an operator configures a key. Neither provider is trusted to assign
 * FooFoo meal classes; provider responses are staged as evidence for later rules/AI/review.
 */

export interface ResearchRecord {
  provider: "foodon_ols" | "usda_fdc" | "groq";
  providerRecordId: string | null;
  sourceUrl: string;
  payload: Record<string, unknown>;
  confidence: number;
}

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

const RESEARCH_TIMEOUT_MS = 3500;

/** Normalize a user-entered food name for conservative exact-match comparisons. */
export function normalizeFoodName(value: string): string {
  return value.normalize("NFKC").trim().toLocaleLowerCase("en-IN").replace(/\s+/g, " ");
}

/** Convert an external search rank/exactness signal into a bounded evidence confidence. */
export function externalMatchConfidence(
  query: string,
  label: string,
  providerScore?: number,
): number {
  if (normalizeFoodName(query) === normalizeFoodName(label)) return 0.9;
  if (typeof providerScore === "number" && Number.isFinite(providerScore)) {
    return Math.max(0.1, Math.min(0.8, providerScore));
  }
  return 0.45;
}

/** Fetch JSON with a hard deadline; provider failure is handled by the caller as partial research. */
async function fetchJson(
  url: string,
  fetchImpl: FetchLike,
  timeoutMs: number,
): Promise<Record<string, unknown>> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(url, {
      headers: { accept: "application/json", "user-agent": "FooFoo-food-ontology/1.0" },
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`provider_http_${response.status}`);
    return await response.json() as Record<string, unknown>;
  } finally {
    clearTimeout(timer);
  }
}

/** Search FoodOn through EMBL-EBI OLS4 and return at most one raw evidence record. */
export async function searchFoodOn(
  query: string,
  fetchImpl: FetchLike = globalThis.fetch as FetchLike,
  timeoutMs = RESEARCH_TIMEOUT_MS,
): Promise<ResearchRecord | null> {
  const url = new URL("https://www.ebi.ac.uk/ols4/api/search");
  url.searchParams.set("q", query);
  url.searchParams.set("ontology", "foodon");
  url.searchParams.set("rows", "5");
  const payload = await fetchJson(url.toString(), fetchImpl, timeoutMs);
  const response = payload.response as Record<string, unknown> | undefined;
  const docs = Array.isArray(response?.docs) ? response.docs as Record<string, unknown>[] : [];
  const first = docs[0];
  if (!first) return null;
  const label = typeof first.label === "string" ? first.label : "";
  return {
    provider: "foodon_ols",
    providerRecordId: typeof first.iri === "string" ? first.iri : null,
    sourceUrl: url.toString(),
    payload,
    confidence: externalMatchConfidence(query, label),
  };
}

/** Search USDA FoodData Central when an API key is configured and retain one raw evidence record. */
export async function searchUsda(
  query: string,
  apiKey: string,
  fetchImpl: FetchLike = globalThis.fetch as FetchLike,
  timeoutMs = RESEARCH_TIMEOUT_MS,
): Promise<ResearchRecord | null> {
  const url = new URL("https://api.nal.usda.gov/fdc/v1/foods/search");
  url.searchParams.set("api_key", apiKey);
  url.searchParams.set("query", query);
  url.searchParams.set("pageSize", "5");
  const payload = await fetchJson(url.toString(), fetchImpl, timeoutMs);
  const foods = Array.isArray(payload.foods) ? payload.foods as Record<string, unknown>[] : [];
  const first = foods[0];
  if (!first) return null;
  const description = typeof first.description === "string" ? first.description : "";
  return {
    provider: "usda_fdc",
    providerRecordId: first.fdcId === undefined ? null : String(first.fdcId),
    sourceUrl: "https://fdc.nal.usda.gov/",
    payload,
    confidence: externalMatchConfidence(query, description),
  };
}

/** Run available providers concurrently; one provider failing never discards another's evidence. */
export async function researchDish(
  query: string,
  usdaApiKey: string | null,
  fetchImpl: FetchLike = globalThis.fetch as FetchLike,
): Promise<{
  records: ResearchRecord[];
  failedProviders: string[];
  providerErrors: Record<string, string>;
}> {
  const providers: Array<{ name: string; request: Promise<ResearchRecord | null> }> = [
    { name: "foodon_ols", request: searchFoodOn(query, fetchImpl) },
  ];
  if (usdaApiKey) {
    providers.push({ name: "usda_fdc", request: searchUsda(query, usdaApiKey, fetchImpl) });
  }
  const settled = await Promise.allSettled(providers.map((provider) => provider.request));
  const records: ResearchRecord[] = [];
  const failedProviders: string[] = [];
  const providerErrors: Record<string, string> = {};
  settled.forEach((result, index) => {
    if (result.status === "fulfilled") {
      if (result.value) records.push(result.value);
    } else {
      failedProviders.push(providers[index].name);
      providerErrors[providers[index].name] = result.reason instanceof Error
        ? result.reason.message.slice(0, 120)
        : "provider_error";
    }
  });
  return { records, failedProviders, providerErrors };
}

/** Return a lowercase SHA-256 hex digest for deterministic source-response identity. */
export async function sha256Json(payload: Record<string, unknown>): Promise<string> {
  const bytes = new TextEncoder().encode(JSON.stringify(payload));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

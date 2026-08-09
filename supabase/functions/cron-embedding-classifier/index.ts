/** Service-only background worker: Groq-independent meal_class/cuisine classification.
 *
 * meal_classes and cuisines are closed, DB-governed vocabularies (migration 128 embedding columns
 * + migration 130 nearest-embedding lookups) -- classifying a dish against them needs no LLM call,
 * so this worker is not subject to Groq's rate limit or daily budget at all. It exists specifically
 * to close the meal_class/cuisine coverage gap independently of cron-dish-ontology's Groq path;
 * taxonomy/aliases/regional_affinities remain Groq-only (open-ended, not closed-vocabulary lookups)
 * and are unaffected by this worker.
 */
import { jsonOk } from "../_shared/api/response.ts";
import { requireServiceRole } from "../_shared/auth/service-role.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { buildContext, compose, errorBoundary, requestLogging } from "../_shared/middleware/index.ts";
import { embedText, toVectorLiteral } from "../dish-ontology/embeddings.ts";
import { sha256Json } from "../dish-ontology/research.ts";

// gte-small cold-start plus sequential per-dish embedding calls hit WORKER_RESOURCE_LIMIT at
// batch 30 in production testing -- 8 is a conservative size that leaves headroom for the
// classify_dish_by_embedding RPC round-trip per dish too, not just the embedding call itself.
const BATCH_SIZE = 8;

const pipeline = compose([errorBoundary, requestLogging, requireServiceRole()])(
  async (_req, ctx) => {
    const db = createServiceRoleClient(ctx.config);

    // migration 131: single RPC that also excludes dishes with an existing embedding_classifier
    // food_source_records row. The prior two-query selection (cuisine_id IS NULL +
    // dishes_missing_meal_class) had no memory of a dish already being attempted -- a dish whose
    // nearest match scored below the 0.55 threshold stays cuisine_id=NULL/mapping-less forever
    // (embeddings are static, so that outcome never changes), so it kept getting re-selected every
    // invocation instead of the batch advancing to dishes not yet tried. Confirmed in production:
    // food_source_records grew by ~300 rows while coverage counts didn't move at all.
    const { data: rows, error: fetchError } = await db.rpc(
      "dishes_pending_embedding_classification",
      { p_limit: BATCH_SIZE },
    );
    if (fetchError) throw fetchError;
    const targets = (rows ?? []).map((row: Record<string, unknown>) => ({
      id: String(row.id),
      name: String(row.name),
    }));

    let classified = 0;
    let published = 0;
    let candidatesOnly = 0;
    let skippedNoEmbeddingMatch = 0;
    let failed = 0;
    const failures: string[] = [];

    for (const dish of targets) {
      try {
        const embedding = await embedText(dish.name);
        const vector = toVectorLiteral(embedding);

        const sourcePayload = { model: "gte-small", note: "dish-name embedding, not a raw vector dump" };
        const { data: sourceRow, error: sourceError } = await db
          .from("food_source_records")
          .insert({
            provider: "embedding_classifier",
            provider_record_id: null,
            dish_id: dish.id,
            submission_id: null,
            query_text: dish.name,
            source_url: "internal://gte-small-embedding-classifier",
            source_payload: sourcePayload,
            payload_sha256: await sha256Json(sourcePayload),
          })
          .select("id")
          .single();
        if (sourceError) throw sourceError;

        const { data: result, error: classifyError } = await db.rpc("classify_dish_by_embedding", {
          p_dish_id: dish.id,
          p_query_embedding: vector,
          p_source_record_id: sourceRow.id,
        });
        if (classifyError) throw classifyError;

        classified++;
        const counts = result && typeof result === "object" ? result as Record<string, unknown> : {};
        const dishPublished = Number(counts.published ?? 0);
        const dishCandidates = Number(counts.candidates ?? 0);
        published += dishPublished;
        if (dishCandidates > 0 && dishPublished === 0) candidatesOnly++;
        if (dishCandidates === 0) skippedNoEmbeddingMatch++;
      } catch (error) {
        failed++;
        failures.push(
          `${dish.id}:${error instanceof Error ? error.message.slice(0, 100) : "unknown_error"}`,
        );
      }
    }

    return jsonOk(
      { claimed: targets.length, classified, published, candidatesOnly, skippedNoEmbeddingMatch, failed, failures },
      ctx.traceId,
    );
  },
);

Deno.serve((req: Request) => pipeline(req, buildContext(req)));

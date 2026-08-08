/** Service-only background worker for queued canonical and user-submitted dish enrichment. */
import { jsonOk } from "../_shared/api/response.ts";
import { requireServiceRole } from "../_shared/auth/service-role.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import {
  buildContext,
  compose,
  errorBoundary,
  requestLogging,
} from "../_shared/middleware/index.ts";
import { researchDish } from "../dish-ontology/research.ts";
import { promoteExternalEvidence, storeResearchRecordsForSubject } from "../dish-ontology/store.ts";
import type { ClosedVocabulary } from "../dish-ontology/ai.ts";
import { generateGroqDishEnrichment } from "../dish-ontology/ai.ts";
import { embedText, toVectorLiteral } from "../dish-ontology/embeddings.ts";

const pipeline = compose([errorBoundary, requestLogging, requireServiceRole()])(
  async (_req, ctx) => {
    const db = createServiceRoleClient(ctx.config);
    await db.rpc("reconcile_dish_enrichment_jobs");

    // Deterministic, non-AI safety-field correctness pass (migration 125): runs on every
    // invocation so newly-ingested dishes get the same is_jain/diet_type/allergen_flags check as
    // the 2026-08-08 backlog pass, without waiting for a human to notice bad data. Best-effort —
    // a failure here must not block the AI enrichment work below.
    let safetyFieldCorrections: Record<string, number> = {};
    let safetyFieldError: string | null = null;
    try {
      const { data: safetyRows, error: safetyError } = await db.rpc(
        "dish_safety_field_autocorrect",
      );
      if (safetyError) throw safetyError;
      for (const row of safetyRows ?? []) {
        safetyFieldCorrections[String(row.violation)] = Number(row.rows_corrected ?? 0);
      }
    } catch (error) {
      safetyFieldError = error instanceof Error ? error.message.slice(0, 120) : "unknown_error";
    }

    const workerId = `edge:${ctx.traceId}`;
    const { data: jobs, error } = await db.rpc("claim_dish_enrichment_jobs", {
      p_worker_id: workerId,
      p_batch_size: 12,
    });
    if (error) throw error;

    let complete = 0;
    let failed = 0;
    let ontologyTerms = 0;
    let nutrients = 0;
    const providerFailures: Record<string, number> = {};
    for (const job of jobs ?? []) {
      try {
        const research = await researchDish(String(job.query_text), ctx.config.usdaFoodDataApiKey);
        for (const [provider, reason] of Object.entries(research.providerErrors)) {
          const key = `${provider}:${reason}`;
          providerFailures[key] = (providerFailures[key] ?? 0) + 1;
        }
        const stored = await storeResearchRecordsForSubject(ctx, {
          dishId: job.dish_id ?? null,
          submissionId: job.submission_id ?? null,
          query: String(job.query_text),
          records: research.records,
        });
        if (job.dish_id) {
          const promoted = await promoteExternalEvidence(
            ctx,
            String(job.dish_id),
            stored,
            String(job.query_text),
          );
          ontologyTerms += promoted.ontologyTerms;
          nutrients += promoted.nutrients;
        }
        let promotedDishId: string | null = null;
        if (job.submission_id && research.records.length) {
          const { data: promoted, error: promotionError } = await db.rpc(
            "promote_submission_if_safe",
            { p_submission_id: job.submission_id },
          );
          if (promotionError) throw promotionError;
          promotedDishId = promoted ? String(promoted) : null;
        }
        const now = new Date();
        const { error: updateError } = await db.from("dish_enrichment_jobs").update({
          status: job.dish_id || promotedDishId
            ? "complete"
            : (research.records.length ? "pending_ai" : "review"),
          external_enriched_at: now.toISOString(),
          source_refresh_after: new Date(now.getTime() + 90 * 86400000).toISOString(),
          completed_at: job.dish_id || promotedDishId ? now.toISOString() : null,
          locked_at: null,
          locked_by: null,
          lease_expires_at: null,
          last_error_code: research.failedProviders.length ? "partial_provider_failure" : null,
          updated_at: now.toISOString(),
        }).eq("id", job.job_id).eq("locked_by", workerId);
        if (updateError) throw updateError;
        complete++;
      } catch (error) {
        failed++;
        const attempts = Number(job.attempts ?? 1);
        await db.from("dish_enrichment_jobs").update({
          status: "failed",
          last_error_code: error instanceof Error ? error.message.slice(0, 120) : "worker_error",
          next_attempt_at: new Date(Date.now() + Math.min(86400000, 60000 * 2 ** attempts))
            .toISOString(),
          locked_at: null,
          locked_by: null,
          lease_expires_at: null,
          updated_at: new Date().toISOString(),
        }).eq("id", job.job_id).eq("locked_by", workerId);
      }
    }

    let aiClaimed = 0;
    let aiComplete = 0;
    let aiFailed = 0;
    let aiBudgetDeferred = 0;
    let aiCandidates = 0;
    let aiPublished = 0;
    let aiTokens = 0;
    if (ctx.config.groqApiKey) {
      const aiWorkerId = `groq:${ctx.traceId}`;
      const { data: aiJobs, error: aiClaimError } = await db.rpc(
        "claim_ai_dish_enrichment",
        { p_worker_id: aiWorkerId, p_batch_size: 2 },
      );
      if (aiClaimError) throw aiClaimError;
      aiClaimed = aiJobs?.length ?? 0;

      for (const aiJob of aiJobs ?? []) {
        // Fetched per dish (not once per batch) so migration 127's word-overlap filter can trim
        // the class_codes list to what's actually relevant to this dish name, cutting prompt token
        // weight — a live 429 rate limit from Groq on every call since the unfiltered migration 126
        // vocabulary shipped is the reason this exists (see migration 127's header). Best-effort:
        // if this fails, enrichment still runs for aliases/taxonomy/regional_affinities, just
        // without meal_class/cuisine candidates for this dish.
        let vocabulary: ClosedVocabulary | undefined;
        try {
          // migration 128: try the semantic (embedding cosine-similarity) vocabulary first --
          // it catches dishes whose class shares no literal word with the dish name, which
          // migration 127's word-overlap filter (the fallback below) structurally cannot. The RPC
          // itself returns NULL (not an empty list) until the one-time embeddings backfill has
          // run, so an untouched deployment transparently keeps using the word-overlap version.
          let vocabRow: unknown = null;
          try {
            const embedding = await embedText(String(aiJob.query_text));
            const { data } = await db.rpc("ai_enrichment_closed_vocabulary_by_embedding", {
              p_query_embedding: toVectorLiteral(embedding),
              p_match_count: 40,
            });
            vocabRow = data;
          } catch {
            // gte-small unavailable or embeddings not backfilled yet -- fall through below.
          }
          if (!vocabRow) {
            const { data } = await db.rpc("ai_enrichment_closed_vocabulary", {
              p_dish_name: String(aiJob.query_text),
            });
            vocabRow = data;
          }
          if (vocabRow && typeof vocabRow === "object") {
            const raw = vocabRow as Record<string, unknown>;
            vocabulary = {
              classCodes: Array.isArray(raw.class_codes) ? raw.class_codes.map(String) : [],
              cuisineNames: Array.isArray(raw.cuisine_names) ? raw.cuisine_names.map(String) : [],
            };
          }
        } catch {
          // Best-effort, per the comment above.
        }
        // The prompt is ~600 tokens and GPT-OSS may use reasoning tokens. Reserve the full
        // request envelope atomically; settlement replaces it with actual provider usage.
        const reservedTokens = 2_000;
        let budgetReserved = false;
        try {
          const { data: reserved, error: reserveError } = await db.rpc(
            "reserve_ai_provider_budget",
            {
              p_provider: "groq",
              p_request_limit: ctx.config.aiDailyRequestBudget,
              p_token_limit: ctx.config.aiDailyTokenBudget,
              p_reserve_tokens: reservedTokens,
            },
          );
          if (reserveError) throw reserveError;
          budgetReserved = reserved === true;
          if (!budgetReserved) {
            aiBudgetDeferred++;
            await db.rpc("finish_ai_dish_enrichment", {
              p_dish_id: aiJob.dish_id,
              p_worker_id: aiWorkerId,
              p_model_name: ctx.config.groqModel,
              p_status: "budget_deferred",
              p_error: "daily_free_tier_budget_exhausted",
            });
            continue;
          }

          const generated = await generateGroqDishEnrichment(
            String(aiJob.query_text),
            ctx.config.groqApiKey,
            ctx.config.groqModel,
            undefined,
            undefined,
            vocabulary,
          );
          aiTokens += generated.usage.totalTokens;
          const stored = await storeResearchRecordsForSubject(ctx, {
            dishId: String(aiJob.dish_id),
            submissionId: null,
            query: String(aiJob.query_text),
            records: [generated.record],
          });
          if (!stored[0]) throw new Error("groq_source_record_missing");
          const { data: promotion, error: promotionError } = await db.rpc(
            "record_ai_low_risk_enrichment",
            {
              p_dish_id: aiJob.dish_id,
              p_source_record_id: stored[0].id,
              p_model: ctx.config.groqModel,
              p_payload: generated.enrichment,
              p_min_confidence: ctx.config.aiMinUsableConfidence,
              p_direct_confidence: ctx.config.aiDirectPublishConfidence,
            },
          );
          if (promotionError) throw promotionError;
          const counts = promotion && typeof promotion === "object"
            ? promotion as Record<string, unknown>
            : {};
          aiCandidates += Number(counts.candidates ?? 0);
          aiPublished += Number(counts.published ?? 0);
          const { error: settleError } = await db.rpc(
            "settle_ai_provider_budget",
            {
              p_provider: "groq",
              p_reserved_tokens: reservedTokens,
              p_actual_tokens: generated.usage.totalTokens,
            },
          );
          if (settleError) throw settleError;
          budgetReserved = false;
          const { error: finishError } = await db.rpc(
            "finish_ai_dish_enrichment",
            {
              p_dish_id: aiJob.dish_id,
              p_worker_id: aiWorkerId,
              p_model_name: ctx.config.groqModel,
              p_status: "complete",
              p_error: null,
            },
          );
          if (finishError) throw finishError;
          aiComplete++;
        } catch (error) {
          aiFailed++;
          const errorCode = error instanceof Error
            ? error.message.slice(0, 120)
            : "groq_worker_error";
          providerFailures[`groq:${errorCode}`] = (providerFailures[`groq:${errorCode}`] ?? 0) + 1;
          await db.rpc("finish_ai_dish_enrichment", {
            p_dish_id: aiJob.dish_id,
            p_worker_id: aiWorkerId,
            p_model_name: ctx.config.groqModel,
            p_status: "failed",
            p_error: errorCode,
          });
        } finally {
          if (budgetReserved) {
            await db.rpc("settle_ai_provider_budget", {
              p_provider: "groq",
              p_reserved_tokens: reservedTokens,
              p_actual_tokens: 0,
            });
          }
        }
      }
    }
    return jsonOk(
      {
        claimed: jobs?.length ?? 0,
        complete,
        failed,
        ontologyTerms,
        nutrients,
        providerFailures,
        safetyFieldCorrections,
        safetyFieldError,
        ai: {
          claimed: aiClaimed,
          complete: aiComplete,
          failed: aiFailed,
          budget_deferred: aiBudgetDeferred,
          candidates: aiCandidates,
          published: aiPublished,
          tokens: aiTokens,
          model: ctx.config.groqApiKey ? ctx.config.groqModel : null,
        },
      },
      ctx.traceId,
    );
  },
);

Deno.serve((req: Request) => pipeline(req, buildContext(req)));

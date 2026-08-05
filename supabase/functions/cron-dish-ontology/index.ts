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

const pipeline = compose([errorBoundary, requestLogging, requireServiceRole()])(
  async (_req, ctx) => {
    const db = createServiceRoleClient(ctx.config);
    await db.rpc("reconcile_dish_enrichment_jobs");
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
          const promoted = await promoteExternalEvidence(ctx, String(job.dish_id), stored);
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
    return jsonOk(
      { claimed: jobs?.length ?? 0, complete, failed, ontologyTerms, nutrients, providerFailures },
      ctx.traceId,
    );
  },
);

Deno.serve((req: Request) => pipeline(req, buildContext(req)));

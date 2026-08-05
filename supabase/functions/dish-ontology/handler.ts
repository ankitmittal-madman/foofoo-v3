/** Authenticated API for dish intake, enrichment status, meal classes and class-bound candidates. */
import { requireAuth } from "../_shared/auth/authorize.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import { normalizeFoodName, researchDish } from "./research.ts";
import {
  autoPromoteSubmission,
  createSubmission,
  fetchCandidates,
  fetchMealClasses,
  loadSubmissionStatus,
  markResearchComplete,
  storeResearchRecordsForSubject,
  updateSubmission,
} from "./store.ts";

/** Parse an object request body or raise FooFoo's standard validation error. */
async function parseBody(req: Request): Promise<Record<string, unknown>> {
  try {
    const body = await req.json();
    if (!body || typeof body !== "object" || Array.isArray(body)) throw new Error("not_object");
    return body as Record<string, unknown>;
  } catch {
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "invalid JSON object" });
  }
}

/** Validate and normalize a user dish draft without inventing missing product metadata. */
function submissionInput(body: Record<string, unknown>): {
  enteredName: string;
  metadata: Record<string, unknown>;
} {
  const enteredName = typeof body.name === "string" ? body.name.normalize("NFKC").trim() : "";
  if (enteredName.length < 2 || enteredName.length > 160) {
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "name must be 2-160 chars" });
  }
  const metadata =
    body.metadata && typeof body.metadata === "object" && !Array.isArray(body.metadata)
      ? body.metadata as Record<string, unknown>
      : {};
  return { enteredName, metadata };
}

/** Execute best-effort external research and move the job to AI/review without blocking on a miss. */
async function enrichSubmission(
  ctx: Parameters<Handler>[1],
  submissionId: string,
  enteredName: string,
): Promise<{
  evidence_count: number;
  failed_providers: string[];
  next_status: string;
  canonical_dish_id: string | null;
}> {
  const research = await researchDish(enteredName, ctx.config.usdaFoodDataApiKey);
  await storeResearchRecordsForSubject(ctx, {
    submissionId,
    dishId: null,
    query: enteredName,
    records: research.records,
  });
  const canonicalDishId = research.records.length
    ? await autoPromoteSubmission(ctx, submissionId)
    : null;
  if (!canonicalDishId) {
    await markResearchComplete(ctx, submissionId, research.records.length > 0);
  }
  return {
    evidence_count: research.records.length,
    failed_providers: research.failedProviders,
    next_status: canonicalDishId
      ? "resolved"
      : (research.records.length > 0 ? "pending_ai" : "review"),
    canonical_dish_id: canonicalDishId,
  };
}

/** Build POST /v1/dish-ontology; existing /plan endpoints remain the weekly-plan contract. */
export function makeDishOntologyHandler(): Handler {
  return async (req, ctx) => {
    if (req.method !== "POST") throw new AppError(ERROR_CATALOGUE.METHOD_NOT_ALLOWED);
    const claims = requireAuth(ctx.claims);
    const body = await parseBody(req);
    const action = typeof body.action === "string" ? body.action : "";

    if (action === "submit" || action === "update") {
      const input = submissionInput(body);
      const submissionId = typeof body.submission_id === "string" ? body.submission_id : "";
      const submission = action === "update"
        ? await updateSubmission(ctx, claims.userId, submissionId, input)
        : await createSubmission(ctx, claims.userId, input);
      if (!submission) throw new AppError(ERROR_CATALOGUE.NOT_FOUND);
      const id = String(submission.id);
      const research = await enrichSubmission(ctx, id, input.enteredName);
      ctx.logger.info("dish_ontology.research_complete", {
        submission_id: id,
        providers_returned: research.evidence_count,
        providers_failed: research.failed_providers.length,
      });
      return jsonContract({ kind: "dish_submission", submission, research }, ctx.traceId, 201);
    }

    if (action === "status") {
      const submissionId = typeof body.submission_id === "string" ? body.submission_id : "";
      const submission = await loadSubmissionStatus(ctx, claims.userId, submissionId);
      if (!submission) throw new AppError(ERROR_CATALOGUE.NOT_FOUND);
      return jsonContract({ kind: "dish_enrichment_status", submission }, ctx.traceId);
    }

    if (action === "meal_classes") {
      return jsonContract(
        { kind: "meal_classes", classes: await fetchMealClasses(ctx) },
        ctx.traceId,
      );
    }

    if (action === "candidates") {
      const classCode = typeof body.class_code === "string" ? body.class_code : "";
      if (!classCode) {
        throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "class_code required" });
      }
      const role = body.role === "addon" ? "addon" : "primary";
      const limit = typeof body.limit === "number" ? Math.max(1, Math.min(100, body.limit)) : 25;
      const candidates = await fetchCandidates(ctx, {
        classCode,
        role,
        limit,
        slot: typeof body.slot === "string" ? normalizeFoodName(body.slot) : undefined,
        diet: typeof body.diet === "string" ? normalizeFoodName(body.diet) : undefined,
      });
      return jsonContract(
        { kind: "dish_candidates", class_code: classCode, role, candidates },
        ctx.traceId,
      );
    }

    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
      detail: "action must be submit, update, status, meal_classes, or candidates",
    });
  };
}

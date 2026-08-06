/** Authenticated API for dish intake, enrichment status, meal classes and class-bound candidates. */
import { requireAuth } from "../_shared/auth/authorize.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import { normalizeFoodName } from "./research.ts";
import {
  createSubmission,
  fetchCandidates,
  fetchDishOntologyRecord,
  fetchMealClasses,
  loadSubmissionStatus,
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
      // The database trigger creates/deduplicates the durable enrichment job. Provider research,
      // AI inference and promotion are intentionally worker-only: an external outage must never
      // lengthen or fail this user-facing request while the ontology service is extracted.
      const research = {
        evidence_count: 0,
        failed_providers: [] as string[],
        next_status: "pending",
        canonical_dish_id: null,
        processing: "asynchronous",
      };
      ctx.logger.info("dish_ontology.enrichment_queued", {
        submission_id: id,
      });
      return jsonContract({ kind: "dish_submission", submission, research }, ctx.traceId, 202);
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

    if (action === "ontology_record") {
      const dishId = typeof body.dish_id === "string" ? body.dish_id : undefined;
      const name = typeof body.name === "string" ? body.name.normalize("NFKC").trim() : undefined;
      if (!dishId && !name) {
        throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
          detail: "dish_id or name required",
        });
      }
      if (
        dishId &&
        !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(dishId)
      ) {
        throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "dish_id must be a UUID" });
      }
      const record = await fetchDishOntologyRecord(ctx, { dishId, name });
      if (!record) throw new AppError(ERROR_CATALOGUE.NOT_FOUND);
      return jsonContract({ kind: "dish_ontology_record", record }, ctx.traceId);
    }

    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
      detail: "action must be submit, update, status, meal_classes, candidates, or ontology_record",
    });
  };
}

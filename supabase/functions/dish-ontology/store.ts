/** Database operations for user dish intake, external evidence and class-bound candidate reads. */
import { createServiceRoleClient } from "../_shared/db/client.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";
import type { ResearchRecord } from "./research.ts";
import { sha256Json } from "./research.ts";

export interface DishSubmissionInput {
  enteredName: string;
  metadata: Record<string, unknown>;
}

/** Insert a user-owned staging submission; the database trigger creates its enrichment job. */
export async function createSubmission(
  ctx: RequestContext,
  userId: string,
  input: DishSubmissionInput,
): Promise<Record<string, unknown>> {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await withTimeout(
    db.from("dish_submissions").insert({
      submitted_by: userId,
      entered_name: input.enteredName,
      submitted_metadata: input.metadata,
    }).select("id, entered_name, status, canonical_dish_id, created_at").single(),
    "dishOntology.createSubmission",
  );
  if (error) throw error;
  return data as Record<string, unknown>;
}

/** Update one submission after proving ownership in the query itself. */
export async function updateSubmission(
  ctx: RequestContext,
  userId: string,
  submissionId: string,
  input: DishSubmissionInput,
): Promise<Record<string, unknown> | null> {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await withTimeout(
    db.from("dish_submissions").update({
      entered_name: input.enteredName,
      submitted_metadata: input.metadata,
      status: "pending",
      updated_at: new Date().toISOString(),
    }).eq("id", submissionId).eq("submitted_by", userId)
      .select("id, entered_name, status, canonical_dish_id, created_at").maybeSingle(),
    "dishOntology.updateSubmission",
  );
  if (error) throw error;
  return data as Record<string, unknown> | null;
}

/** Load a submission and its active enrichment job, scoped to the authenticated owner. */
export async function loadSubmissionStatus(
  ctx: RequestContext,
  userId: string,
  submissionId: string,
): Promise<Record<string, unknown> | null> {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await withTimeout(
    db.from("dish_submissions")
      .select(
        "id, entered_name, status, canonical_dish_id, created_at, updated_at, dish_enrichment_jobs(id, status, missing_fields, attempts, updated_at)",
      )
      .eq("id", submissionId).eq("submitted_by", userId).maybeSingle(),
    "dishOntology.loadSubmissionStatus",
  );
  if (error) throw error;
  return data as Record<string, unknown> | null;
}

/** Persist raw external responses separately from normalized taxonomy values. */
export async function storeResearchRecords(
  ctx: RequestContext,
  submissionId: string,
  query: string,
  records: ResearchRecord[],
): Promise<void> {
  if (records.length === 0) return;
  const db = createServiceRoleClient(ctx.config);
  const rows = await Promise.all(records.map(async (record) => ({
    provider: record.provider,
    provider_record_id: record.providerRecordId,
    submission_id: submissionId,
    query_text: query,
    source_url: record.sourceUrl,
    source_payload: record.payload,
    payload_sha256: await sha256Json(record.payload),
  })));
  const { error } = await withTimeout(
    db.from("food_source_records").insert(rows),
    "dishOntology.storeResearchRecords",
  );
  if (error) throw error;
}

/** Mark a submission ready for the configured AI/review stage after external lookup finishes. */
export async function markResearchComplete(
  ctx: RequestContext,
  submissionId: string,
  hadEvidence: boolean,
): Promise<void> {
  const db = createServiceRoleClient(ctx.config);
  const nextStatus = hadEvidence ? "pending_ai" : "review";
  const submissionWrite = db.from("dish_submissions").update({
    status: nextStatus,
    updated_at: new Date().toISOString(),
  }).eq("id", submissionId);
  const jobWrite = db.from("dish_enrichment_jobs").update({
    status: nextStatus,
    updated_at: new Date().toISOString(),
  }).eq("submission_id", submissionId).not("status", "in", "(complete,failed)");
  const [submissionResult, jobResult] = await Promise.all([
    withTimeout(submissionWrite, "dishOntology.markSubmissionResearchComplete"),
    withTimeout(jobWrite, "dishOntology.markJobResearchComplete"),
  ]);
  if (submissionResult.error) throw submissionResult.error;
  if (jobResult.error) throw jobResult.error;
}

/** Fetch the canonical meal-class hierarchy and planning-role metadata. */
export async function fetchMealClasses(ctx: RequestContext): Promise<unknown[]> {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await withTimeout(
    db.from("meal_classes")
      .select(
        "class_code, display_name, slot, parent_class_code, class_family_code, planning_role, weekday_fit_1_5, weekend_fit_1_5, is_addon",
      )
      .eq("is_active", true).order("slot").order("class_code"),
    "dishOntology.fetchMealClasses",
  );
  if (error) throw error;
  return data ?? [];
}

/** Fetch recommendation candidates from the ontology gate with optional hard filters. */
export async function fetchCandidates(
  ctx: RequestContext,
  filters: { classCode: string; slot?: string; role: string; diet?: string; limit: number },
): Promise<unknown[]> {
  const db = createServiceRoleClient(ctx.config);
  let query = db.from("dish_candidates_by_class").select("*")
    .eq("class_code", filters.classCode).eq("item_role", filters.role)
    .order("classification_confidence", { ascending: false }).limit(filters.limit);
  if (filters.slot) query = query.eq("slot", filters.slot);
  if (filters.diet) query = query.eq("diet_type", filters.diet);
  const { data, error } = await withTimeout(query, "dishOntology.fetchCandidates");
  if (error) throw error;
  return data ?? [];
}

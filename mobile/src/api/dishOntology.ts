import { apiPost } from "./client";

export interface DishSubmission {
  id: string;
  entered_name: string;
  status: "pending" | "researching" | "pending_ai" | "review" | "resolved" | "rejected" | "failed";
  canonical_dish_id: string | null;
  created_at: string;
}

export interface DishSubmissionMetadata {
  aliases?: string[];
  ingredients?: string[];
  cuisine?: string;
  region?: string;
  meal_slots?: string[];
  diet_type?: string;
  cook_time_minutes?: number;
  difficulty?: "beginner" | "intermediate" | "advanced";
  notes?: string;
}

/** Submit an unknown dish into the staging/ontology workflow; it is never served before promotion. */
export async function submitUnknownDish(name: string, metadata: DishSubmissionMetadata) {
  return apiPost<{
    kind: "dish_submission";
    submission: DishSubmission;
    research: { evidence_count: number; failed_providers: string[]; next_status: string };
    trace_id: string;
  }>("/v1/dish-ontology", { action: "submit", name, metadata });
}

export async function getDishSubmissionStatus(submissionId: string) {
  return apiPost<{ kind: "dish_enrichment_status"; submission: DishSubmission; trace_id: string }>(
    "/v1/dish-ontology",
    { action: "status", submission_id: submissionId },
  );
}

export interface DishOntologyRecord {
  schema_version: "1";
  dish: Record<string, unknown>;
  aliases: Record<string, unknown>[];
  ingredients: Record<string, unknown>[];
  meal_classes: Record<string, unknown>[];
  taxonomy: Record<string, unknown>[];
  constraints: Record<string, unknown>[];
  regional_affinities: Record<string, unknown>[];
  nutrition: Record<string, unknown>[];
  recipes: Record<string, unknown>[];
  meal_episodes: Record<string, unknown>[];
  relationships: Record<string, unknown>[];
  evidence: Record<string, unknown>[];
}

/** Fetch one complete governed dish record with confidence and provenance metadata. */
export async function getDishOntologyRecord(identity: { dishId?: string; name?: string }) {
  return apiPost<{ kind: "dish_ontology_record"; record: DishOntologyRecord; trace_id: string }>(
    "/v1/dish-ontology",
    { action: "ontology_record", dish_id: identity.dishId, name: identity.name },
  );
}

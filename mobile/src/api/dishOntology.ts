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

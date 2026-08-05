/**
 * Request/response types hand-mirrored from the Edge Function source of truth — no generated
 * client exists yet, so these are kept in lockstep manually:
 *   - household/schema.ts (HOUSEHOLD_ANSWERS_SCHEMAS, PROFILE_SCHEMAS, memberEnvelope)
 *   - household/handler.ts's jsonContract response shape
 *   - recommendations/contract.ts + contracts/ghar-re-v1.schema.json (RecommendationResponse)
 *   - consent-schema.ts + docs/architecture/[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md §06.1
 */

// ---- POST /v1/consent -------------------------------------------------------

export type ConsentType = "personalization" | "analytics" | "push_notifications" | "data_retention";

export interface ConsentInput {
  consent_type: ConsentType;
  granted: boolean;
}

export interface ConsentRequest {
  profile_id: string;
  consents: ConsentInput[];
  privacy_policy_version: string;
}

export interface ConsentRecorded {
  consent_type: ConsentType;
  granted: boolean;
  granted_at: string;
}

export interface ConsentResponse {
  recorded: ConsentRecorded[];
  personalization_granted: boolean;
}

// ---- POST /v1/household ----------------------------------------------------

export type ProfileQuestionKey =
  | "primary_cook_name"
  | "home_state"
  | "current_city"
  | "diet_type"
  | "cook_capability"
  | "religious_pref"
  | "allergen_flags"
  | "migration_duration_band"
  | "city_overlay_weight"
  | "push_notification_time";

export type HouseholdAnswerQuestionKey =
  | "q1_household_type"
  | "q2_working_professionals"
  | "q6_nonveg_types"
  | "q7_veg_days"
  | "q10_allergy_other"
  | "q11_conditions"
  | "q13_who_cooks"
  | "q14_eat_out_per_week"
  | "q15_objective";

export type QuestionKey = ProfileQuestionKey | HouseholdAnswerQuestionKey;

export interface ScreenAnswer {
  screen_id: string;
  question_key: QuestionKey;
  answer_value: unknown;
  skipped?: boolean;
}

export interface MemberWrite {
  id?: string;
  member_name?: string;
  conditions?: string[];
  allergen_flags?: number;
  diet_type?: "veg" | "non_veg" | "egg" | "vegan" | "jain";
  is_active?: boolean;
}

export interface HouseholdWriteRequest {
  household_id?: string;
  screens: ScreenAnswer[];
  members: MemberWrite[];
}

export interface HouseholdWriteResponse {
  household_id: string;
  profile_exists: boolean;
  profile_created: boolean;
  answers_recorded: string[];
  missing_required_fields: string[];
  members_written: number;
  trace_id: string;
}

// ---- POST /v1/recommendations ----------------------------------------------

export interface RecommendationsRequest {
  household_id?: string;
  request_id?: string;
  context?: Record<string, unknown>;
}

export interface Contribution {
  module: string;
  value: number;
  weight: number;
  confidence: number;
}

export interface Plate {
  plate_id: string;
  form: "pair" | "single" | "standalone";
  hero_dish_ids: string[];
  hero_dish_names?: string[];
  support?: string | null;
  is_standalone?: boolean;
  plate_score: number;
  base_total: number;
  gain_multiplier: number;
  final_score: number;
  contributions: Contribution[];
}

export interface RecommendationsResponse {
  request_id?: string;
  api_version?: string;
  engine_version?: string;
  config_version?: string;
  plates: Plate[];
  warnings?: string[];
  trace_id: string;
}

// ---- POST /v1/feedback (WP-15) ----------------------------------------------

export type FeedbackEventType =
  | "accept" | "edit" | "swap" | "like" | "dislike" | "shown_not_tapped"
  | "never" | "not_today" | "lock" | "unlock" | "add_to_date"
  | "make_this" | "too_much_work" | "missing_ingredient" | "member_objection"
  | "cooked" | "ordered" | "replaced" | "completed" | "regretted";

export interface FeedbackRequest {
  household_id?: string;
  /** RecommendationsResponse.request_id — the only recommendation identifier this client is ever
   * given; the backend resolves it to the matching recommendation_events row (feedback/events.ts). */
  request_id: string;
  event_type: FeedbackEventType;
  /** plate.hero_dish_names[i] — resolved server-side to public.dishes.id by name. */
  dish_name?: string;
  slot?: string;
  detail?: Record<string, unknown>;
}

export interface FeedbackResponse {
  id: string;
  event_type: FeedbackEventType;
  recorded_at: string;
  trace_id: string;
  /** True when the device durably queued the event for delivery after connectivity returns. */
  queued?: boolean;
}

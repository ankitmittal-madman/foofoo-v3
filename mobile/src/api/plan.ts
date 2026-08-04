/**
 * WP-18 planning API — the onboarding→plan→recipe surfaces, all through the single POST /v1/plan
 * Edge Function (multiplexed by `surface`). Same auth/transport as api/recommendations.ts (apiPost
 * attaches the Supabase JWT). The Edge Function composes the household from the DB, so the client
 * never sends Q1–Q15 here — only the surface + planning params.
 */
import { apiPost } from "./client";

/** One dish/meal card the planner returns (image_url + meal class attached server-side). */
export interface PlanDish {
  name: string;
  cuisine: string;
  diet: string;
  meal_class_code: string | null;
  meal_class_name: string | null;
  spice_level: number | null;
  heaviness: number | null;
  total_mins: number | null;
  score: number;
  image_url: string | null;
  explanation?: {
    base_total: number;
    q15_contribution: number;
    weather_contribution: number;
    top_contributors: Array<{
      module: string;
      value: number;
      weight: number;
      weighted: number;
    }>;
  };
  slot?: string;
  /** Engine-internal calibration bookkeeping (calibration surface only) — plumbing for feedback,
   * never rendered by any screen. */
  cell_role?: "expected_positive" | "planted_negative";
}

export interface PlanAddon {
  member_index: number;
  member_role: string;
  class_code: string;
  dish: PlanDish;
}

export interface ColdStartResponse {
  kind: string;
  count: number;
  dishes: PlanDish[];
  /** Stamped by plan/handler.ts specifically for this call — pass through to POST /v1/feedback
   * (api/feedback.ts) so a cold-start "like" tap resolves to the recommendation_events row the
   * handler wrote for this response. */
  request_id?: string;
}

export interface CalibrationResponse {
  kind: string;
  slots: { breakfast: PlanDish[]; lunch: PlanDish[]; dinner: PlanDish[] };
  request_id?: string;
}

export interface SlotOptionsResponse {
  slot: string;
  weekday: string;
  class_code: string | null;
  count: number;
  options: PlanDish[];
  /** Stamped by plan/handler.ts on every response (P0-4, 2026-08) so a like/dislike tap on the
   * Home tab (today.tsx) can resolve to the recommendation_events row the handler now writes for
   * meal_plan/class_dishes surfaces too — same pattern as ColdStartResponse.request_id. */
  request_id?: string;
  addons?: PlanAddon[];
}

export interface WeeklyClass {
  class_code: string;
  class_name: string;
  plan_weight: number;
  dish_count: number;
}

export interface WeeklyDay {
  weekday: string;
  slots: { breakfast: WeeklyClass[]; lunch: WeeklyClass[]; dinner: WeeklyClass[] };
}

export interface WeeklyPlanResponse {
  kind: string;
  days: WeeklyDay[];
}

export interface Recipe {
  dish_name: string;
  cuisine: string;
  diet: string;
  serves: string;
  prep_mins: number;
  cook_mins: number;
  total_mins: number;
  spice_level: number | null;
  ingredients: string[];
  steps: string[];
  method_source: string;
}

export interface RecipeResponse {
  dish_name: string;
  image_url: string | null;
  recipe: Recipe | null;
}

export type Slot = "breakfast" | "lunch" | "dinner";

/** Surface 1 — post-onboarding top-N (default 15) diverse dishes to like/seed preferences. */
export function fetchColdStart(count = 15): Promise<ColdStartResponse> {
  return apiPost<ColdStartResponse>("/plan", { surface: "cold_start", count });
}

/** Dish-pick calibration grid — 3 slots x 5 dishes (3 expected-positive + 2 planted-mismatch,
 * cell_role never shown in the UI, only echoed back on feedback). */
export function fetchCalibrationGrid(): Promise<CalibrationResponse> {
  return apiPost<CalibrationResponse>("/plan", { surface: "calibration" });
}

/** Surface 2 — a slot's 4–5 dish options (pass class_code to reconcile to one finalized class). */
export function fetchSlotOptions(
  slot: Slot,
  opts: { weekday?: string; class_code?: string; count?: number } = {},
): Promise<SlotOptionsResponse> {
  return apiPost<SlotOptionsResponse>("/plan", { surface: "meal_plan", slot, ...opts });
}

export type WeekSelections = Record<string, Partial<Record<Slot, string>>>;

export interface SavedPlanSlot {
  slot_date: string;
  meal_slot: Slot;
  class_code: string;
  is_locked: boolean;
}

export interface SavedWeekResponse {
  kind: "saved_week";
  plan: { status: "draft" | "finalized"; plan_slots: SavedPlanSlot[] } | null;
}

export function fetchSavedWeek(): Promise<SavedWeekResponse> {
  return apiPost<SavedWeekResponse>("/plan", { surface: "saved_week" });
}

export function savedWeekSelections(response: SavedWeekResponse | undefined): WeekSelections {
  const selections: WeekSelections = {};
  for (const row of response?.plan?.plan_slots ?? []) {
    const weekday = new Date(`${row.slot_date}T12:00:00Z`).toLocaleDateString("en-US", {
      weekday: "long",
      timeZone: "UTC",
    });
    selections[weekday] = { ...selections[weekday], [row.meal_slot]: row.class_code };
  }
  return selections;
}

export function savedWeekLocks(response: SavedWeekResponse | undefined): Record<string, Partial<Record<Slot, boolean>>> {
  const locks: Record<string, Partial<Record<Slot, boolean>>> = {};
  for (const row of response?.plan?.plan_slots ?? []) {
    const weekday = new Date(`${row.slot_date}T12:00:00Z`).toLocaleDateString("en-US", {
      weekday: "long",
      timeZone: "UTC",
    });
    locks[weekday] = { ...locks[weekday], [row.meal_slot]: row.is_locked };
  }
  return locks;
}

export function saveWeekPlan(selections: WeekSelections, finalize: boolean): Promise<unknown> {
  return apiPost("/plan", { surface: "save_week", selections, finalize });
}

export function setPlanSlotLock(
  weekday: string,
  slot: Slot,
  locked: boolean,
): Promise<unknown> {
  return apiPost("/plan", { surface: "lock_slot", weekday, slot, locked });
}

export function addDishToDate(input: {
  slot_date: string;
  slot: Slot;
  class_code: string;
  dish_name: string;
}): Promise<unknown> {
  return apiPost("/plan", { surface: "add_to_date", ...input });
}

/** Surface 3 — the weekly class plan (7 days × slots, top-3 dish-backed classes each). */
export function fetchWeeklyPlan(topClasses = 3): Promise<WeeklyPlanResponse> {
  return apiPost<WeeklyPlanResponse>("/plan", { surface: "weekly_plan", top_classes: topClasses });
}

/** Surface 4 — reconciliation: only dishes of a finalized class for that day/slot. */
export function fetchClassDishes(
  slot: Slot,
  classCode: string,
  weekday: string,
  count = 8,
): Promise<SlotOptionsResponse> {
  return apiPost<SlotOptionsResponse>("/plan", {
    surface: "class_dishes",
    slot,
    class_code: classCode,
    weekday,
    count,
  });
}

/** Surface 5 — full recipe + image for one dish (the meal-detail screen). */
export function fetchRecipe(dishName: string): Promise<RecipeResponse> {
  return apiPost<RecipeResponse>("/plan", { surface: "recipe", dish_name: dishName });
}

export interface DishSearchFilters {
  cuisine?: string;
  diet?: string;
  slot?: Slot;
  max_total_mins?: number;
  limit?: number;
}

export interface DishSearchResponse {
  kind: "dish_search";
  query: string;
  count: number;
  options: PlanDish[];
}

export function searchDishes(query: string, filters: DishSearchFilters = {}): Promise<DishSearchResponse> {
  return apiPost<DishSearchResponse>("/plan", { surface: "search", query, ...filters });
}

/** One past recommendation event (P1-3, 2026-08) — a row of the household's own history. */
export interface RecommendationHistoryRow {
  id: string;
  request_id: string;
  created_at: string;
  slot: string | null;
  outcome: string;
  plate_count: number;
}

export interface HistoryResponse {
  kind: string;
  events: RecommendationHistoryRow[];
}

/** Surface 6 (P1-3) — the caller's own recent recommendation history. No RE call; a pure DB read. */
export function fetchHistory(count = 20): Promise<HistoryResponse> {
  return apiPost<HistoryResponse>("/plan", { surface: "history", count });
}

/** The current composed household (P1-4, 2026-08) — same shape the RE itself scores against. */
export interface HouseholdRawView {
  q5_diet: string;
  q9_allergies: string[];
  q1_household_type?: string;
}

export interface ProfileResponse {
  kind: string;
  household: HouseholdRawView;
  stubbed: boolean;
}

/** Surface 7 (P1-4) — read the caller's own current diet/allergen/household answers. No RE call. */
export function fetchProfile(): Promise<ProfileResponse> {
  return apiPost<ProfileResponse>("/plan", { surface: "profile" });
}

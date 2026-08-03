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
  slot?: string;
}

export interface ColdStartResponse {
  kind: string;
  count: number;
  dishes: PlanDish[];
}

export interface SlotOptionsResponse {
  slot: string;
  weekday: string;
  class_code: string | null;
  count: number;
  options: PlanDish[];
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

/** Surface 2 — a slot's 4–5 dish options (pass class_code to reconcile to one finalized class). */
export function fetchSlotOptions(
  slot: Slot,
  opts: { weekday?: string; class_code?: string; count?: number } = {},
): Promise<SlotOptionsResponse> {
  return apiPost<SlotOptionsResponse>("/plan", { surface: "meal_plan", slot, ...opts });
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

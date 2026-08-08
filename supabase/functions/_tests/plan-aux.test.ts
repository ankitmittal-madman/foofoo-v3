import { assertEquals } from "@std/assert";
import { authenticate, defineHandler, resetConfigCacheForTests } from "../_shared/mod.ts";
import type { AuthClaims } from "../_shared/mod.ts";
import { makePlanHandler } from "../plan/handler.ts";
import type { OnlineRecommendationState } from "../recommendations/personalization.ts";

const USER_ID = "11111111-1111-4111-8111-111111111111";
const DISH_ID = "22222222-2222-4222-8222-222222222222";
const REQUIRED_ENV = {
  SUPABASE_URL: "http://localhost:54321",
  SUPABASE_ANON_KEY: "anon-test-key",
  SUPABASE_SERVICE_ROLE_KEY: "service-test-key",
  FOOFOO_ENV: "local",
};

function withEnv(vars: Record<string, string>, fn: () => void | Promise<void>) {
  const previous: Record<string, string | undefined> = {};
  for (const [key, value] of Object.entries(vars)) {
    previous[key] = Deno.env.get(key);
    Deno.env.set(key, value);
  }
  try {
    return fn();
  } finally {
    for (const key of Object.keys(vars)) {
      if (previous[key] === undefined) Deno.env.delete(key);
      else Deno.env.set(key, previous[key]!);
    }
    resetConfigCacheForTests();
  }
}

const ONLINE: OnlineRecommendationState = {
  interactionCount: 12,
  excludeDishNames: ["Karela"],
  preferenceByDish: { Poha: 0.8 },
  preferenceByClass: { LIGHT_VEG_ROTI: 0.6 },
  preferenceByDirectClass: { LIGHT_VEG_ROTI: 0.9 },
  preferenceByProjectedClass: { LIGHT_VEG_ROTI: 0.2 },
  preferenceByTag: {},
  dishFeedbackCounts: [],
  recentExposureDishNames: [],
  recentClassCounts: {},
  recentCuisineCounts: {},
  noveltyBudget: 0.2,
  richnessDebt: 0,
  temporalClassState: [],
  temporalAttributeState: [],
  governedContextSignals: [],
};

Deno.test("meal-episode planning passes the Aux canonical shortlist into Ghar", async () => {
  await withEnv({
    ...REQUIRED_ENV,
    AUX_RE_MODE: "active",
    AUX_RE_SERVICE_URL: "http://aux.local",
    AUX_RE_SERVICE_SECRET: "test-secret",
  }, async () => {
    let auxPayload: Record<string, unknown> | undefined;
    let gharPayload: Record<string, unknown> | undefined;
    const handler = makePlanHandler({
      authorizeHousehold: () => Promise.resolve("owner"),
      loadHousehold: () =>
        Promise.resolve({
          householdId: USER_ID,
          stubbed: false,
          household: {
            q1_household_type: "couple",
            q2_working_professionals: 2,
            q3_home_state: "Maharashtra",
            q4_current_city: "Mumbai",
            q5_diet: "veg",
            q6_nonveg_types: [],
            q7_veg_days: [],
            q8_is_jain: false,
            q9_allergies: [],
            q10_allergy_other: null,
            q11_conditions: [],
            q12_member_ages: [{ role: "adult", age: 32 }],
            q13_who_cooks: "self",
            q14_eat_out_per_week: 1,
            q15_objective: "healthy_living",
            cook_capability: "intermediate",
          },
        }),
      loadOnlineState: () => Promise.resolve(ONLINE),
      loadWeather: () => Promise.resolve(null),
      loadFestival: () => Promise.resolve({ date: "2026-08-10", festivalNames: [] }),
      callAux: (payload) => {
        auxPayload = payload;
        return Promise.resolve({
          ok: true,
          candidateIds: [DISH_ID],
          publicationVersion: `sha256:${"a".repeat(64)}`,
          latencyMs: 9,
        });
      },
      callRe: (payload) => {
        gharPayload = payload;
        return Promise.resolve({
          ok: false,
          kind: "http",
          status: 503,
          detail: "test stop after payload capture",
        });
      },
    });
    const verifier = () =>
      Promise.resolve({ userId: USER_ID, role: "authenticated" } as AuthClaims);
    const pipeline = defineHandler(handler, { middleware: [authenticate(verifier)] });
    const response = await pipeline(
      new Request("http://localhost/v1/plan", {
        method: "POST",
        headers: { authorization: "Bearer test", "content-type": "application/json" },
        body: JSON.stringify({
          surface: "meal_episodes",
          household_id: USER_ID,
          slot: "lunch",
          date: "2026-08-10",
        }),
      }),
    );

    assertEquals(response.status, 503);
    assertEquals(auxPayload?.preference_by_direct_class, { LIGHT_VEG_ROTI: 0.9 });
    assertEquals(gharPayload?.candidate_dish_ids, [DISH_ID]);
  });
});

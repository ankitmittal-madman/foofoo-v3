/**
 * Synthetic-user harness (Decision 0, RE Intelligence roadmap follow-up).
 *
 * Drives the REAL foofoo-v3 app (Expo web build at http://localhost:8081) through the REAL
 * sign-up -> create-id -> consent -> onboarding step-1..5 -> cold-start flow, for a batch of
 * varied synthetic households. Every account created this way writes through the app's real
 * code paths into the real Supabase tables (auth.users, profiles, onboarding_sessions,
 * household_answers, recommendation_events via /plan) — nothing is hand-inserted via SQL.
 *
 * Every synthetic account is tagged with a `synth_<batch>_<n>@foofoo-synth.test` email so
 * synthetic and real rows are never confused downstream (analytics, ML training corpora, etc.
 * per this repo's standing rule against fabricated data masquerading as real signal).
 *
 * Usage: node scripts/synthetic-users/run.mjs [count] [baseUrl]
 */
import { chromium } from "playwright";

const COUNT = parseInt(process.argv[2] ?? "6", 10);
const BASE_URL = process.argv[3] ?? "http://localhost:8081";
const BATCH = Date.now().toString(36);

// Varied cohorts on purpose (diet/state/city/cook_capability) — the whole point is to NOT repeat
// the identical test_23/test_27 cohort that started this investigation.
const COHORTS = [
  { diet: "veg", state: "Maharashtra", city: "Pune", cook: "beginner", household: "single", objective: "healthy" },
  { diet: "non_veg", state: "Delhi", city: "Delhi", cook: "advanced", household: "couple", objective: "tasty" },
  { diet: "vegan", state: "Karnataka", city: "Bengaluru", cook: "intermediate", household: "flatmates", objective: "discover" },
  { diet: "jain", state: "Gujarat", city: "Ahmedabad", cook: "beginner", household: "couple_kids", objective: "healthy" },
  { diet: "eggetarian", state: "West Bengal", city: "Kolkata", cook: "advanced", household: "joint", objective: "into_fitness" },
  { diet: "veg", state: "Tamil Nadu", city: "Chennai", cook: "intermediate", household: "couple_kids_parents", objective: "tasty" },
];

function cohortFor(i) {
  return COHORTS[i % COHORTS.length];
}

// expo-router (web) keeps previous stack screens mounted in the DOM (hidden, not unmounted), so
// getByText often resolves to several matches across screens — only one of which is actually
// visible right now. Poll until at least one match is visible/enabled, then click that one.
async function clickText(page, text, opts = {}) {
  const timeout = opts.timeout ?? 15000;
  const deadline = Date.now() + timeout;
  const loc = page.getByText(text, { exact: opts.exact ?? true });
  for (;;) {
    const n = await loc.count();
    for (let i = 0; i < n; i++) {
      const el = loc.nth(i);
      if (await el.isVisible().catch(() => false)) {
        await el.scrollIntoViewIfNeeded().catch(() => {});
        await el.click();
        return;
      }
    }
    if (Date.now() > deadline) {
      throw new Error(`clickText: no visible match for "${text}" within ${timeout}ms (${n} hidden matches)`);
    }
    await page.waitForTimeout(200);
  }
}

async function waitVisible(page, text, opts = {}) {
  const timeout = opts.timeout ?? 20000;
  const exact = opts.exact ?? false;
  const deadline = Date.now() + timeout;
  const loc = page.getByText(text, { exact });
  for (;;) {
    const n = await loc.count();
    for (let i = 0; i < n; i++) {
      if (await loc.nth(i).isVisible().catch(() => false)) return;
    }
    if (Date.now() > deadline) throw new Error(`waitVisible: "${text}" never visible within ${timeout}ms`);
    await page.waitForTimeout(200);
  }
}

async function runOne(browser, index) {
  const cohort = cohortFor(index);
  const email = `synth_${BATCH}_${index}@foofoo-synth.test`;
  const password = "SynthUser!2026";
  const name = `Synth${BATCH}${index}`;
  const log = (...a) => console.log(`[${email}]`, ...a);

  const context = await browser.newContext();
  const page = await context.newPage();
  page.on("pageerror", (e) => log("PAGE ERROR:", e.message));

  try {
    // --- Sign up ---
    await page.goto(`${BASE_URL}/(auth)/sign-in?mode=signup`, { waitUntil: "domcontentloaded" });
    await page.getByPlaceholder("you@example.com").waitFor({ state: "visible", timeout: 20000 });
    await page.getByPlaceholder("you@example.com").fill(email);
    await page.getByPlaceholder("At least 6 characters").fill(password);
    await clickText(page, "Create Account →");

    // --- Create ID ---
    await page.getByPlaceholder("e.g. Pratikshit").waitFor({ state: "visible", timeout: 20000 });
    await page.getByPlaceholder("e.g. Pratikshit").fill(name);
    await clickText(page, "Continue →");

    // --- Consent ---
    await waitVisible(page, "Your data,");
    await clickText(page, "Continue →");

    // --- Step 1: household type + earners ---
    await waitVisible(page, "Who lives").catch(() => {});
    const householdLabel = {
      single: "Just Me", couple: "Couple", couple_kids: "Couple + Kids",
      couple_kids_parents: "Couple, Kids & Parents", flatmates: "Flatmates", joint: "Full Family",
    }[cohort.household];
    await clickText(page, householdLabel);
    if (cohort.household !== "single") {
      // pick "2" earners if offered, else whatever's first — best-effort, layout varies by household
      await clickText(page, "2", { exact: true, timeout: 3000 }).catch(() => {});
    }
    await clickText(page, "Continue →");

    // --- Step 2: state + city ---
    await waitVisible(page, "Select your home state");
    await clickText(page, "Select your home state");
    await page.getByPlaceholder("Search state…").fill(cohort.state);
    await clickText(page, cohort.state, { exact: false });
    await page.getByPlaceholder("e.g. Pune").fill(cohort.city);
    await clickText(page, "Continue →");

    // --- Step 3: diet ---
    const dietLabel = {
      veg: "Vegetarian", eggetarian: "Eggetarian", non_veg: "Non-Vegetarian", jain: "Jain", vegan: "Vegan",
    }[cohort.diet];
    await waitVisible(page, dietLabel, { exact: true });
    await clickText(page, dietLabel);
    await clickText(page, "Continue →");

    // --- Step 4: allergens/medical — skip both (optional) ---
    await waitVisible(page, "Any health-related").catch(() => {});
    await clickText(page, "Continue →");

    // --- Step 5: cooking skill (required) + eat-out + objective ---
    const cookLabel = { beginner: "Beginner", intermediate: "Intermediate", advanced: "Advanced" }[cohort.cook];
    await waitVisible(page, "Last details").catch(() => {});
    await clickText(page, cookLabel);
    const objLabel = {
      tasty: "To get tasty options", healthy: "To get healthy options",
      discover: "To discover", into_fitness: "Into Fitness",
    }[cohort.objective];
    await clickText(page, objLabel);
    await clickText(page, "See my plan →");

    // --- Cold-start: wait for the RE-backed dish list, like a few, continue ---
    await waitVisible(page, "Tell us what you like", { timeout: 30000 });
    // give the /plan call a moment to resolve and render dish rows
    await page.waitForTimeout(2000);
    const hearts = page.locator("text=🤍");
    let heartCount = await hearts.count();
    const initialHeartCount = heartCount;
    const toLike = Math.min(3, heartCount);
    for (let i = 0; i < toLike; i++) {
      const visible = hearts.first();
      if (!(await visible.isVisible().catch(() => false))) break;
      await visible.click(); // liking swaps 🤍 -> ❤️, so "first" always advances to the next unliked row
      await page.waitForTimeout(200);
    }

    log(`OK — cohort=${JSON.stringify(cohort)}, liked ${toLike}/${initialHeartCount} cold-start dishes`);
    return { email, cohort, ok: true, liked: toLike, dishCount: initialHeartCount };
  } catch (e) {
    log("FAILED:", e.message);
    return { email, cohort, ok: false, error: e.message };
  } finally {
    await context.close();
  }
}

async function main() {
  console.log(`Synthetic-user batch ${BATCH}: ${COUNT} households against ${BASE_URL}`);
  const browser = await chromium.launch({ headless: true });
  const results = [];
  for (let i = 0; i < COUNT; i++) {
    // sequential, not parallel — mirrors a real signup rate and keeps error output readable
    results.push(await runOne(browser, i));
  }
  await browser.close();

  const ok = results.filter((r) => r.ok).length;
  console.log(`\n=== Batch ${BATCH}: ${ok}/${COUNT} succeeded ===`);
  for (const r of results) {
    console.log(r.ok ? `  OK   ${r.email} (liked ${r.liked}/${r.dishCount})` : `  FAIL ${r.email}: ${r.error}`);
  }
  console.log(`\nQuery synthetic rows with: WHERE email LIKE 'synth_${BATCH}_%@foofoo-synth.test'`);
  process.exit(ok === COUNT ? 0 : 1);
}

main();

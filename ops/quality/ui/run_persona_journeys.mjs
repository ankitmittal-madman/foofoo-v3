/**
 * WP-22 — Synthetic persona UI journey driver.
 *
 * Drives the REAL onboarding UI (consent -> step-1..step-5) through Playwright, one full pass
 * per persona from ops/quality/personas/personas.py (100 personas: 7 golden + 8 derived + 41
 * real_persona_derived + 44 adversarial), screenshotting after every answer and every "Continue"
 * navigation, then captures whatever the app's own POST /v1/recommendations call returns once
 * onboarding completes. This is a REAL Playwright driver, gated on a live target exactly like
 * ops/quality/ui/run_ui.mjs — the Expo/React-Native web app has no committed build to load, so
 * without GHAR_WEB_URL this script only writes a SKIPPED result and exits 0, same honesty rule
 * run_ui.mjs itself documents (never fabricate UI evidence).
 *
 * No RE scoring assertions are made here (Phase 8's pytest suites already own that, black-box,
 * against the real /v1/recommendations contract) — this driver only records what the UI actually
 * showed and what the API actually returned, per persona, as evidence.
 *
 * Per-persona isolation (WP-22 Critical Self-Review §4): each persona's entire Playwright run is
 * wrapped in its own try/catch. A failure on persona N (crashed page, missing testID, unreachable
 * screen) writes that persona's own { ok: false, error } summary and moves on — it can never abort
 * the other 99 personas' runs.
 *
 * Usage:
 *   python3 ops/quality/personas/export_personas.py > /tmp/personas.json   # or let this driver
 *                                                                            # shell out itself
 *   GHAR_WEB_URL=http://localhost:8081 GHAR_UI_OUT=/path/to/report \
 *     GHAR_PERSONAS_JSON=/tmp/personas.json \
 *     node ops/quality/ui/run_persona_journeys.mjs
 *
 *   GHAR_PERSONAS_LIMIT=5   (optional — run only the first N personas, for a fast smoke pass)
 *
 * Auth: no pre-provisioned account is needed or used. Each persona signs up its OWN fresh
 * random-email account via the app's real sign-up flow ((auth)/sign-in?mode=signup ->
 * create-id -> onboarding), since onboarding is only reachable while signed in
 * ((onboarding)/_layout.tsx's guard). This also fixes a correctness gap a shared account would
 * have had: reusing one login across personas would leak persona N's onboarding_completed state
 * onto persona N+1's run. If the target Supabase project requires email confirmation before a
 * session is issued, sign-up will succeed but never yield a session — the driver detects this
 * (the app's own "check your email to confirm" notice) and reports it as the persona's failure
 * reason rather than fabricating a pass; auto-confirm must be enabled in that project for this
 * driver to work end-to-end.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

import { personaToOnboardingAnswers, isSplitAge } from "./personaToOnboardingAnswers.mjs";

const url = process.env.GHAR_WEB_URL;
const outDir = process.env.GHAR_UI_OUT || path.join(process.cwd(), "ui-artifacts");
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");

/** Write the run summary JSON and exit with the given code (matches run_ui.mjs's finish()). */
function finish(summary, code = 0) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, "persona_journeys_result.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
  process.exit(code);
}

if (!url) {
  finish({
    status: "skipped",
    reason:
      "GHAR_WEB_URL not set. The frontend is an Expo/React-Native app with no committed web " +
      "build; provide a running web target (e.g. `expo start --web`) to enable persona UI " +
      "journeys. This driver never fabricates screenshots or recommendation results.",
    phase: "WP-22 persona UI journeys",
  });
}

let chromium;
try {
  ({ chromium } = await import("playwright"));
} catch (e) {
  finish(
    { status: "blocked", reason: "playwright module not installed (npm i -D playwright && npx playwright install)", error: String(e) },
    0,
  );
}

/** Load personas either from GHAR_PERSONAS_JSON or by shelling out to export_personas.py. */
function loadPersonas() {
  const jsonPath = process.env.GHAR_PERSONAS_JSON;
  let raw;
  if (jsonPath) {
    raw = fs.readFileSync(jsonPath, "utf8");
  } else {
    raw = execFileSync("python3", [path.join(REPO_ROOT, "ops", "quality", "personas", "export_personas.py")], {
      cwd: REPO_ROOT,
      encoding: "utf8",
      maxBuffer: 32 * 1024 * 1024,
    });
  }
  const all = JSON.parse(raw);
  const limit = process.env.GHAR_PERSONAS_LIMIT ? Number(process.env.GHAR_PERSONAS_LIMIT) : null;
  return limit ? all.slice(0, limit) : all;
}

/**
 * waitForPath — Node-side poll of page.url() against a predicate, instead of Playwright's
 * page.waitForURL(). expo-router's web navigation uses history.pushState (client-side routing),
 * which never fires the browser 'load' event waitForURL's default waitUntil:'load' waits for —
 * so waitForURL can hang the FULL timeout even after the URL has already changed. Polling
 * page.url() directly is lifecycle-agnostic and works identically for full navigations and SPA
 * route changes. On timeout, throws with the LAST OBSERVED URL so a failure is diagnosable
 * (e.g. "still on /sign-in" -> login itself never completed, vs "on /consent" -> a later step's
 * own selector is what's actually wrong).
 */
async function waitForPath(page, predicate, timeoutMs) {
  const start = Date.now();
  let lastUrl = page.url();
  while (Date.now() - start < timeoutMs) {
    lastUrl = page.url();
    if (predicate(new URL(lastUrl))) return;
    await page.waitForTimeout(250);
  }
  throw new Error(`waitForPath timed out after ${timeoutMs}ms (last url: ${lastUrl})`);
}

let personas;
try {
  personas = loadPersonas();
} catch (e) {
  finish({ status: "blocked", reason: "could not load personas (export_personas.py failed or GHAR_PERSONAS_JSON unreadable)", error: String(e).slice(0, 500) }, 1);
}

/** slug — filesystem-safe persona directory name. */
function slug(key) {
  return String(key).replace(/[^a-zA-Z0-9_-]/g, "-");
}

/** randomTestCredentials — a fresh, never-reused email+password for one persona's own account. */
function randomTestCredentials(personaKey) {
  const suffix = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  return {
    email: `ghar-persona-${slug(personaKey)}-${suffix}@example.com`,
    password: `Qa1-${suffix}-Ghar`,
  };
}

/**
 * signUpAndAuthenticate — creates a fresh random-email account via the app's real sign-up flow
 * and drives it through to a signed-in session, IF one is configured. Onboarding is unreachable
 * while signed out ((onboarding)/_layout.tsx's <Redirect> guard), so a failure here fails
 * identically and honestly rather than the driver fabricating a pass.
 */
async function signUpAndAuthenticate(page, personaKey) {
  const { email, password } = randomTestCredentials(personaKey);
  // Route groups such as `(auth)` organize Expo Router source files but are deliberately omitted
  // from browser URLs. `mode=signup` opens sign-in.tsx directly in its signup state.
  await page.goto(new URL("/sign-in?mode=signup", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
  const emailInput = page.locator('[data-testid="signin-email"], input[type="email"], input[placeholder*="mail" i]').first();
  const passwordInput = page.locator('[data-testid="signin-password"], input[type="password"]').first();
  await emailInput.fill(email, { timeout: 10000 });
  await passwordInput.fill(password, { timeout: 10000 });
  const submit = page.locator('[data-testid="signin-submit"], button:has-text("Create Account"), button:has-text("Sign up")').first();
  await submit.click({ timeout: 10000 });

  try {
    // signUp() -> either an immediate session (auto-confirm on) which routes to /create-id, or
    // (email confirmation required) a "check your email" notice with mode switched back to
    // signin and the URL unchanged — either way this resolves once the URL actually moves.
    await waitForPath(page, (u) => !u.pathname.includes("sign-in"), 30000);
  } catch (e) {
    // Diagnostic capture, not a fix: distinguishes "confirmation required" (a real environment
    // limitation this driver cannot work around) from "already registered" (a random-email
    // collision, extremely unlikely but not impossible) from anything else, instead of every
    // failure here looking like an identical blind timeout.
    const noticeText = await page.locator("text=/check your email|confirm/i").first().textContent({ timeout: 1000 }).catch(() => null);
    const errorText = await page.locator("text=/invalid|error|already registered|exists/i").first().textContent({ timeout: 1000 }).catch(() => null);
    const shotPath = path.join(outDir, `signup-failure-${slug(personaKey)}.png`);
    await page.screenshot({ path: shotPath }).catch(() => {});
    throw new Error(
      `${e.message} | notice: ${noticeText ?? "(none found)"} | error: ${errorText ?? "(none found)"} | screenshot: ${shotPath}`,
    );
  }

  // A brand-new signup always lands on /create-id first (display name capture) before consent —
  // fill it in and continue, same real UI path a human signup would take.
  if (new URL(page.url()).pathname.includes("create-id")) {
    await page.getByTestId("create-id-name").fill(`QA ${personaKey}`, { timeout: 10000 }).catch(() => {});
    await page.getByTestId("create-id-continue").click({ timeout: 10000 }).catch(() => {});
    await waitForPath(page, (u) => u.pathname.includes("consent"), 20000).catch(() => {});
  }
  return { email, password };
}

/**
 * extractBearerToken — best-effort read of the Supabase session's access_token out of the page's
 * own localStorage (Supabase's web client persists the session there under a
 * `sb-<project-ref>-auth-token` key). Needed because the journey driver calls
 * POST /v1/recommendations itself (mirroring mobile/src/api/client.ts's apiPost auth pattern)
 * rather than only passively observing whichever screen the app happens to call it from.
 */
async function extractBearerToken(page) {
  return page.evaluate(() => {
    for (let i = 0; i < window.localStorage.length; i++) {
      const k = window.localStorage.key(i);
      if (!k || !k.includes("auth-token")) continue;
      try {
        const parsed = JSON.parse(window.localStorage.getItem(k));
        const token = parsed?.access_token ?? parsed?.currentSession?.access_token;
        if (token) return token;
      } catch {
        // not JSON / not a session blob — keep scanning other keys
      }
    }
    return null;
  });
}

/**
 * fillChipGroup — clicks every testID matching `${prefix}-${value}` for each value in `values`.
 * Silently skips a value with no matching testID (e.g. this mapper produced a token Screen 4/5
 * doesn't render a chip for) rather than failing the whole persona over one optional field.
 */
async function fillChipGroup(page, prefix, values, recordStep) {
  for (const v of values) {
    const el = page.getByTestId(`${prefix}-${v}`);
    if (await el.count()) {
      await el.first().click();
      await recordStep(`${prefix}-${v}`);
    }
  }
}

let shotCounter = 0;

/** journeyStep — timestamp one completed UI action for chronological Excel reporting. */
function journeyStep(label, screenshotName) {
  return { label, action: label, screenshot: screenshotName, timestamp_utc: new Date().toISOString() };
}

/** screenshot — writes a numbered PNG for this persona and returns its filename (no dir side effects beyond that). */
async function screenshot(page, _artifacts, label, personaDir) {
  shotCounter += 1;
  const name = `${String(shotCounter).padStart(3, "0")}-${label}.png`;
  await page.screenshot({ path: path.join(personaDir, name), fullPage: true }).catch(() => {});
  return name;
}

/** runPersona — drives one persona end-to-end through consent + step-1..5, then the recs call. */
async function runPersona(browser, persona) {
  const personaDir = path.join(outDir, "personas", slug(persona.key));
  fs.mkdirSync(personaDir, { recursive: true });
  shotCounter = 0;
  const steps = [];
  const recommendationEvents = [];
  const startedAtUtc = new Date().toISOString();
  let currentStage = "journey-start";
  const context = await browser.newContext();
  const page = await context.newPage();

  const shot = (label) => screenshot(page, steps, label, personaDir);

  /** recordStep — keep the latest stage aligned with recommendation responses observed by Playwright. */
  const recordStep = async (label) => {
    currentStage = label;
    steps.push(journeyStep(label, await shot(label)));
  };

  page.on("response", async (response) => {
    if (!new URL(response.url()).pathname.endsWith("/v1/recommendations")) return;
    const body = await response.json().catch(() => null);
    recommendationEvents.push({
      timestamp_utc: new Date().toISOString(),
      stage_label: currentStage,
      endpoint: "/v1/recommendations",
      response: { status: response.status(), body },
    });
  });

  try {
    await signUpAndAuthenticate(page, persona.key);
    await recordStep("signed-up");

    // Consent — gate on personalization=true so the flow can proceed into step-1.
    await page.goto(new URL("/consent", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
    await recordStep("consent-loaded");
    const consentContinue = page.getByTestId("onboarding-consent-continue");
    await consentContinue.click({ timeout: 10000 });
    await recordStep("consent-continue");

    const answers = personaToOnboardingAnswers(persona.household);
    const split = isSplitAge(answers.householdType);

    // ---- Step 1 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-1"), 15000).catch(() => {});
    if (answers.householdType) {
      await page.getByTestId(`onboarding-step1-household-${answers.householdType}`).click({ timeout: 10000 });
      await recordStep("step1-household");
    }
    if (answers.workingProfessionals != null) {
      const el = page.getByTestId(`onboarding-step1-earners-${answers.workingProfessionals}`);
      if (await el.count()) {
        await el.first().click();
        await recordStep("step1-earners");
      }
    }
    await page.getByTestId("onboarding-step1-continue").click({ timeout: 10000 });
    await recordStep("step1-continue");

    // ---- Step 2 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-2"), 15000).catch(() => {});
    if (answers.homeState) {
      await page.getByTestId("onboarding-step2-state-field").click({ timeout: 10000 });
      await page.getByTestId("onboarding-step2-state-search").fill(answers.homeState, { timeout: 10000 });
      const stateOption = page.getByTestId(`onboarding-step2-state-option-${answers.homeState}`);
      await stateOption.first().click({ timeout: 10000 });
      await recordStep("step2-state");
    }
    if (answers.currentCity) {
      await page.getByTestId("onboarding-step2-city-input").fill(answers.currentCity, { timeout: 10000 });
      await recordStep("step2-city");
    }
    await page.getByTestId("onboarding-step2-continue").click({ timeout: 10000 });
    await recordStep("step2-continue");

    // ---- Step 3 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-3"), 15000).catch(() => {});
    if (answers.diet) {
      await page.getByTestId(`onboarding-step3-diet-${answers.diet}`).click({ timeout: 10000 });
      await recordStep("step3-diet");
    }
    await fillChipGroup(page, "onboarding-step3-meat", answers.meatPreferences, recordStep);
    await fillChipGroup(page, "onboarding-step3-vegday", answers.vegDays, recordStep);
    await page.getByTestId("onboarding-step3-continue").click({ timeout: 10000 });
    await recordStep("step3-continue");

    // ---- Step 4 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-4"), 15000).catch(() => {});
    await fillChipGroup(page, "onboarding-step4-allergen", answers.allergens, recordStep);
    await fillChipGroup(page, "onboarding-step4-condition", answers.medicalConditions, recordStep);
    if (answers.allergensOther) {
      await page.getByTestId("onboarding-step4-allergen-other-input").fill(answers.allergensOther).catch(() => {});
    }
    if (answers.medicalConditionsOther) {
      await page.getByTestId("onboarding-step4-condition-other-input").fill(answers.medicalConditionsOther).catch(() => {});
    }
    await page.getByTestId("onboarding-step4-continue").click({ timeout: 10000 });
    await recordStep("step4-continue");

    // ---- Step 5 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-5"), 15000).catch(() => {});
    if (split) {
      if (answers.ageEldest) await page.getByTestId(`onboarding-step5-age-eldest-${answers.ageEldest}`).click().catch(() => {});
      if (answers.ageYoungest) await page.getByTestId(`onboarding-step5-age-youngest-${answers.ageYoungest}`).click().catch(() => {});
    } else if (answers.ageSingle) {
      await page.getByTestId(`onboarding-step5-age-single-${answers.ageSingle}`).click().catch(() => {});
    }
    await recordStep("step5-age");
    if (answers.whoCooks) await page.getByTestId(`onboarding-step5-whocooks-${answers.whoCooks}`).click().catch(() => {});
    if (answers.cookCapability) await page.getByTestId(`onboarding-step5-cookcapability-${answers.cookCapability}`).click().catch(() => {});
    if (answers.eatOutFrequency) await page.getByTestId(`onboarding-step5-eatout-${answers.eatOutFrequency}`).click().catch(() => {});
    if (answers.cookingObjective) await page.getByTestId(`onboarding-step5-objective-${answers.cookingObjective}`).click().catch(() => {});
    await recordStep("step5-filled");

    await page.getByTestId("onboarding-step5-continue").click({ timeout: 10000 });
    await recordStep("step5-finish");

    // ---- Land on post-onboarding screen (cold-start) ----
    await waitForPath(page, (u) => u.pathname.includes("cold-start") || u.pathname.includes("recommendations"), 20000).catch(() => {});
    await recordStep("post-onboarding-landing");

    // ---- Capture the actual /v1/recommendations result the app's own session would get ----
    const token = await extractBearerToken(page);
    let recommendations = null;
    if (token) {
      const apiBase = await page.evaluate(() => window.location.origin).catch(() => url);
      const resp = await page
        .evaluate(
          async ({ base, tok }) => {
            const res = await fetch(`${base}/v1/recommendations`, {
              method: "POST",
              headers: { "content-type": "application/json", authorization: `Bearer ${tok}` },
              body: JSON.stringify({}),
            });
            const json = await res.json().catch(() => null);
            return { status: res.status, body: json };
          },
          { base: apiBase, tok: token },
        )
        .catch((e) => ({ status: null, error: String(e) }));
      recommendations = resp;
    } else {
      recommendations = { status: null, error: "no Supabase access_token found in page localStorage — could not call /v1/recommendations" };
    }

    const finalRequestId = recommendations?.body?.request_id ?? null;
    const alreadyCaptured = recommendationEvents.some(
      (event) => event.response?.body?.request_id === finalRequestId && event.response?.status === recommendations?.status,
    );
    if (!alreadyCaptured) {
      recommendationEvents.push({
        timestamp_utc: new Date().toISOString(),
        stage_label: "final-recommendations-api",
        endpoint: "/v1/recommendations",
        response: recommendations,
      });
    }
    fs.writeFileSync(path.join(personaDir, "recommendations.json"), JSON.stringify(recommendations, null, 2));
    fs.writeFileSync(path.join(personaDir, "recommendation_events.json"), JSON.stringify(recommendationEvents, null, 2));

    const summary = {
      key: persona.key,
      label: persona.label,
      test_user_id: persona.test_user_id || `${persona.user_type || "synthetic"}:${persona.key}`,
      user_type: persona.user_type || "synthetic",
      source_persona_id: persona.source_persona_id || null,
      started_at_utc: startedAtUtc,
      completed_at_utc: new Date().toISOString(),
      ok: true,
      expect_status: persona.expect_status,
      recommendations_status: recommendations?.status ?? null,
      steps,
    };
    fs.writeFileSync(path.join(personaDir, "summary.json"), JSON.stringify(summary, null, 2));
    return summary;
  } catch (e) {
    // Per WP-22 Critical Self-Review §4: always write this persona's own failure summary before
    // returning, so one bad persona never silently vanishes from the batch's evidence trail.
    const summary = {
      key: persona.key,
      label: persona.label,
      test_user_id: persona.test_user_id || `${persona.user_type || "synthetic"}:${persona.key}`,
      user_type: persona.user_type || "synthetic",
      source_persona_id: persona.source_persona_id || null,
      started_at_utc: startedAtUtc,
      completed_at_utc: new Date().toISOString(),
      ok: false,
      error: String(e && e.message ? e.message : e).slice(0, 1000),
      steps,
    };
    fs.writeFileSync(path.join(personaDir, "recommendation_events.json"), JSON.stringify(recommendationEvents, null, 2));
    fs.writeFileSync(path.join(personaDir, "summary.json"), JSON.stringify(summary, null, 2));
    return summary;
  } finally {
    await page.close().catch(() => {});
    await context.close().catch(() => {});
  }
}

let browser;
try {
  browser = await chromium.launch({ headless: true });
} catch (e) {
  finish({ status: "blocked", reason: "chromium launch failed", error: String(e).slice(0, 300) }, 0);
}

const results = [];
for (const persona of personas) {
  // Each persona is fully isolated (its own try/catch inside runPersona) — a crash on one never
  // aborts the loop over the other 99.
  try {
    const summary = await runPersona(browser, persona);
    results.push(summary);
  } catch (e) {
    // Should not happen (runPersona itself catches), but guard the loop anyway per the
    // "one bad persona must never abort the batch" requirement.
    results.push({ key: persona.key, label: persona.label, ok: false, error: `driver-level failure: ${String(e).slice(0, 500)}`, steps: [] });
  }
}

await browser.close().catch(() => {});

const okCount = results.filter((r) => r.ok).length;
finish(
  {
    status: okCount === results.length ? "pass" : okCount > 0 ? "partial" : "fail",
    url,
    total: results.length,
    ok: okCount,
    failed: results.length - okCount,
    personas: results.map((r) => ({ key: r.key, ok: r.ok, error: r.error ?? null })),
  },
  okCount === results.length ? 0 : 1,
);

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
  const serialized = JSON.stringify(summary, null, 2);
  // Emit the result first so an exhausted artifact filesystem cannot mask the journey outcome.
  console.log(serialized);
  try {
    fs.mkdirSync(outDir, { recursive: true });
    fs.writeFileSync(path.join(outDir, "persona_journeys_result.json"), serialized);
  } catch (error) {
    console.error(`Could not write persona journey result to ${outDir}: ${String(error)}`);
    code = 1;
  }
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

/**
 * clickUntilPath — submit an onboarding step and retry only when the UI remains on that step.
 *
 * A production-test save can occasionally hit a transient network failure. The real UI keeps the
 * user on the same screen and makes Continue retryable, so the journey driver mirrors that human
 * recovery instead of immediately looking for controls on the next screen. A completed journey
 * step is recorded only after the expected route is visible.
 */
async function clickUntilPath(page, testId, predicate, recordStep, label, attempts = 3) {
  let lastError = null;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    if (predicate(new URL(page.url()))) {
      await recordStep(label);
      return;
    }
    await page.getByTestId(testId).click({ timeout: 10000 });
    try {
      await waitForPath(page, predicate, 20000);
      await recordStep(label);
      return;
    } catch (error) {
      lastError = error;
      if (attempt < attempts) await page.waitForTimeout(1000 * attempt);
    }
  }
  throw new Error(`${label} failed after ${attempts} attempts: ${lastError?.message ?? "route did not change"}`);
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

/** Resolve the native Supabase Edge Functions base used by the deployed mobile application. */
async function resolveApiBaseUrl(page) {
  const configured = process.env.GHAR_API_BASE_URL?.replace(/\/$/, "");
  if (configured) return configured;

  const projectRef = await page.evaluate(() => {
    for (let i = 0; i < window.localStorage.length; i++) {
      const key = window.localStorage.key(i);
      const match = key?.match(/^sb-([a-z0-9]+)-auth-token$/i);
      if (match) return match[1];
    }
    return null;
  });
  return projectRef ? `https://${projectRef}.supabase.co/functions/v1` : null;
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
  await page.screenshot({ path: path.join(personaDir, name), fullPage: true });
  return name;
}

/** Wait for a rendered application surface, not merely an Expo Router URL change. */
async function waitForSurface(page, testId, timeout = 45000) {
  await page.getByTestId(testId).waitFor({ state: "visible", timeout });
}

/** Click an action and require the corresponding backend endpoint to complete successfully. */
async function clickWithApi(page, locator, endpoint, timeout = 30000) {
  const responsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname.endsWith(`/v1/${endpoint}`),
    { timeout },
  );
  await locator.click({ timeout: 10000 });
  const response = await responsePromise;
  if (response.status() >= 400) {
    throw new Error(`${endpoint} returned HTTP ${response.status()}`);
  }
  return response;
}

/** runPersona — drives one persona end-to-end through consent + step-1..5, then the recs call. */
async function runPersona(browser, persona) {
  const personaDir = path.join(outDir, "personas", slug(persona.key));
  fs.mkdirSync(personaDir, { recursive: true });
  shotCounter = 0;
  const steps = [];
  const recommendationEvents = [];
  const apiEvents = [];
  const apiEventTasks = [];
  const featureResults = [];
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

  page.on("response", (response) => {
    const task = (async () => {
      const endpointMatch = new URL(response.url()).pathname.match(/\/v1\/([^/?]+)$/);
      if (!endpointMatch) return;
      const body = await response.json().catch(() => null);
      const request = response.request();
      let requestBody = null;
      try {
        requestBody = request.postDataJSON();
      } catch {
        requestBody = request.postData() || null;
      }
      const event = {
        timestamp_utc: new Date().toISOString(),
        stage_label: currentStage,
        endpoint: `/v1/${endpointMatch[1]}`,
        method: request.method(),
        request_body: requestBody,
        response: { status: response.status(), body },
      };
      apiEvents.push(event);
      if (endpointMatch[1] === "recommendations") recommendationEvents.push(event);
    })();
    apiEventTasks.push(task);
  });

  const feature = async (name, fn, { required = true, continueOnFailure = false } = {}) => {
    const started = new Date().toISOString();
    try {
      await fn();
      featureResults.push({ name, status: "pass", started_at_utc: started, completed_at_utc: new Date().toISOString() });
      return true;
    } catch (error) {
      featureResults.push({
        name,
        status: required ? "fail" : "warn",
        started_at_utc: started,
        completed_at_utc: new Date().toISOString(),
        error: String(error?.message ?? error).slice(0, 1000),
      });
      if (required && !continueOnFailure) throw error;
      return false;
    }
  };

  try {
    await signUpAndAuthenticate(page, persona.key);
    await recordStep("signed-up");

    // Consent — gate on personalization=true so the flow can proceed into step-1.
    await page.goto(new URL("/consent", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
    await recordStep("consent-loaded");
    await clickUntilPath(
      page,
      "onboarding-consent-continue",
      (u) => u.pathname.endsWith("/step-1"),
      recordStep,
      "consent-continue",
    );

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
    await clickUntilPath(
      page,
      "onboarding-step1-continue",
      (u) => u.pathname.endsWith("/step-2"),
      recordStep,
      "step1-continue",
    );

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
    await clickUntilPath(
      page,
      "onboarding-step2-continue",
      (u) => u.pathname.endsWith("/step-3"),
      recordStep,
      "step2-continue",
    );

    // ---- Step 3 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-3"), 15000).catch(() => {});
    if (answers.diet) {
      await page.getByTestId(`onboarding-step3-diet-${answers.diet}`).click({ timeout: 10000 });
      await recordStep("step3-diet");
    }
    await fillChipGroup(page, "onboarding-step3-meat", answers.meatPreferences, recordStep);
    await fillChipGroup(page, "onboarding-step3-vegday", answers.vegDays, recordStep);
    await clickUntilPath(
      page,
      "onboarding-step3-continue",
      (u) => u.pathname.endsWith("/step-4"),
      recordStep,
      "step3-continue",
    );

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
    await clickUntilPath(
      page,
      "onboarding-step4-continue",
      (u) => u.pathname.endsWith("/step-5"),
      recordStep,
      "step4-continue",
    );

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

    await clickUntilPath(
      page,
      "onboarding-step5-continue",
      (u) => u.pathname.includes("cold-start") || u.pathname.includes("recommendations"),
      recordStep,
      "step5-finish",
    );

    const expectedStatus = Number(persona.expect_status);

    // Contract-rejected personas cannot render personalized product surfaces. Their complete
    // negative-path evidence is the onboarding journey plus the expected recommendations 422.
    if (expectedStatus === 200) {
      await feature("cold-start calibration renders", async () => {
        await waitForSurface(page, "cold-start-screen");
        await recordStep("cold-start-loaded");
      });
      await feature("cold-start likes generate feedback events", async () => {
        for (const slot of ["breakfast", "lunch", "dinner"]) {
          await clickWithApi(page, page.getByTestId(`cold-start-${slot}-dish-0`), "feedback");
          await recordStep(`cold-start-like-${slot}`);
        }
      });
      await feature("cold-start continues to weekly plan", async () => {
        await page.getByTestId("cold-start-finish").click();
        await waitForPath(page, (u) => u.pathname.endsWith("/weekly-plan"), 20000);
        await waitForSurface(page, "weekly-plan-screen");
        await recordStep("weekly-plan-loaded");
      });
      await feature("weekly plan supplies and saves 7x3 classes", async () => {
        const choices = page.locator('[data-testid^="weekly-plan-"][data-testid$="-0"]');
        const count = await choices.count();
        if (count !== 21) throw new Error(`weekly plan rendered ${count}/21 first-choice class controls`);

        // The screen deliberately keeps weekend cards mounted but hidden while the Weekdays
        // segment is active (and vice versa). Clicking a positional list of all 21 controls
        // therefore stalls on Saturday even though the locator exists in the DOM. Exercise the
        // controls through the same two visible segments a user sees instead.
        for (const weekday of ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]) {
          for (const slot of ["breakfast", "lunch", "dinner"]) {
            await page.getByTestId(`weekly-plan-${weekday}-${slot}-0`).click();
          }
        }
        const weekendTab = page.getByTestId("weekly-plan-period-weekend");
        if (await weekendTab.count()) {
          await weekendTab.click();
        } else {
          // Backward compatibility for deployed builds predating the stable tab test ID.
          await page.getByText(/^(Weekend|वीकेंड)$/).click();
        }
        await page.getByTestId("weekly-plan-Saturday-breakfast-0").waitFor({ state: "visible", timeout: 10000 });
        for (const weekday of ["Saturday", "Sunday"]) {
          for (const slot of ["breakfast", "lunch", "dinner"]) {
            await page.getByTestId(`weekly-plan-${weekday}-${slot}-0`).click();
          }
        }
        await recordStep("weekly-plan-21-slots-selected");
        await clickWithApi(page, page.getByTestId("weekly-plan-finalize"), "plan", 45000);
        await waitForPath(page, (u) => u.pathname.endsWith("/today"), 20000);
        await waitForSurface(page, "home-screen");
        await page.getByTestId("episode-breakfast-primary").waitFor({ state: "visible", timeout: 45000 });
        await recordStep("home-meal-plan-loaded");
      });
      await feature("meal episode explanation and feedback event types", async () => {
        await page.goto(new URL("/today", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
        await waitForSurface(page, "home-screen");
        await page.getByTestId("episode-breakfast-primary").waitFor({ state: "visible", timeout: 45000 });
        const feedbackActions = [
          ["breakfast", "too-much-work"],
          ["lunch", "missing-ingredient"],
          ["dinner", "member-objection"],
        ];
        for (const [slot, reason] of feedbackActions) {
          await page.getByTestId(`episode-${slot}-not-today`).click();
          const control = page.getByTestId(`episode-${slot}-reason-${reason}`);
          if (!(await control.count())) throw new Error(`missing ${slot} episode reason control: ${reason}`);
          await clickWithApi(page, control, "feedback");
          await recordStep(`episode-feedback-${reason}`);
        }
        await clickWithApi(page, page.getByTestId("episode-breakfast-make-this"), "feedback");
        await recordStep("episode-make-this");
      }, { continueOnFailure: true });
      await feature("home lock refresh and next-date recommendations", async () => {
        await page.goto(new URL("/today", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
        await waitForSurface(page, "home-screen");
        await page.getByTestId("episode-breakfast-primary").waitFor({ state: "visible", timeout: 45000 });
        await clickWithApi(page, page.getByTestId("episode-breakfast-lock"), "plan");
        await recordStep("home-breakfast-locked");
        await clickWithApi(page, page.getByTestId("home-refresh"), "plan", 45000);
        await page.waitForTimeout(750);
        await recordStep("home-unlocked-meals-refreshed");
        const dateControls = page.locator('[data-testid^="home-date-"]');
        if ((await dateControls.count()) < 2) throw new Error("next date selector is missing");
        await clickWithApi(page, dateControls.nth(1), "plan", 45000);
        await page.waitForTimeout(750);
        await recordStep("home-next-date-loaded");
      }, { continueOnFailure: true });
      await feature("recipe details render", async () => {
        await page.goto(new URL("/today", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
        await waitForSurface(page, "home-screen");
        await page.getByTestId("episode-breakfast-primary").waitFor({ state: "visible", timeout: 45000 });
        await page.getByTestId("episode-breakfast-recipe").click();
        await waitForSurface(page, "recipe-screen");
        await recordStep("recipe-detail-loaded");
        await page.getByTestId("recipe-back").click();
        await waitForSurface(page, "home-screen");
      }, { continueOnFailure: true });
      await feature("meal episode alternatives render", async () => {
        await page.goto(new URL("/today", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
        await waitForSurface(page, "home-screen");
        await page.getByTestId("episode-breakfast-primary").waitFor({ state: "visible", timeout: 45000 });
        await page.getByTestId("episode-breakfast-alternatives").click();
        await page.getByText(/Hide alternatives/).waitFor({ state: "visible", timeout: 5000 });
        await recordStep("episode-alternatives-opened");
      }, { continueOnFailure: true });
      await feature("safe dish search and search recipe", async () => {
        await page.goto(new URL("/search", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
        await waitForSurface(page, "search-screen");
        await page.getByTestId("search-input").fill("dal");
        await clickWithApi(page, page.getByTestId("search-submit"), "plan");
        await page.getByTestId("search-result-0").waitFor({ state: "visible", timeout: 30000 });
        await recordStep("search-results-loaded");
        await page.getByTestId("search-result-0").click();
        await waitForSurface(page, "recipe-screen");
        await recordStep("search-recipe-loaded");
      }, { continueOnFailure: true });
      await feature("settings and profile preferences", async () => {
        await page.goto(new URL("/settings", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
        await waitForSurface(page, "settings-screen");
        await recordStep("settings-loaded");
        await page.getByTestId("settings-profile-edit-link").click();
        await waitForSurface(page, "profile-edit-screen");
        await recordStep("profile-preferences-loaded");
        await clickWithApi(page, page.getByTestId("profile-edit-save"), "household");
        await waitForSurface(page, "settings-screen");
        await recordStep("profile-preferences-saved");
      }, { continueOnFailure: true });
      await feature("recommendation history and detail", async () => {
        await page.goto(new URL("/settings", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
        await waitForSurface(page, "settings-screen");
        await page.getByTestId("settings-history-link").click();
        await waitForSurface(page, "history-screen");
        await recordStep("recommendation-history-loaded");
        const firstEvent = page.getByTestId("history-event-0");
        if (!(await firstEvent.count())) throw new Error("recommendation history contains no event rows");
        await firstEvent.click();
        await waitForSurface(page, "history-detail-screen");
        await recordStep("recommendation-history-detail-loaded");
      }, { continueOnFailure: true });
      await feature("data-rights controls are guarded", async () => {
        await page.goto(new URL("/settings", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
        await waitForSurface(page, "settings-screen");
        if (!(await page.getByTestId("settings-export-button").isVisible())) throw new Error("data export control is not visible");
        if (await page.getByTestId("settings-delete-confirm-button").isEnabled()) {
          throw new Error("account deletion is enabled without confirmation phrase");
        }
        await recordStep("data-rights-controls-verified");
      }, { continueOnFailure: true });
    } else {
      featureResults.push({
        name: "authenticated product surfaces",
        status: "not-applicable",
        reason: `persona expects recommendations HTTP ${expectedStatus}`,
        completed_at_utc: new Date().toISOString(),
      });
      await recordStep("post-onboarding-contract-rejection-path");
    }

    // ---- Capture the actual /v1/recommendations result the app's own session would get ----
    const token = await extractBearerToken(page);
    let recommendations = null;
    if (token) {
      const apiBase = await resolveApiBaseUrl(page);
      const resp = apiBase
        ? await page
            .evaluate(
              async ({ base, tok }) => {
                const res = await fetch(`${base}/recommendations`, {
                  method: "POST",
                  headers: { "content-type": "application/json", authorization: `Bearer ${tok}` },
                  body: JSON.stringify({}),
                });
                const json = await res.json().catch(() => null);
                return { status: res.status, body: json };
              },
              { base: apiBase, tok: token },
            )
          .catch((e) => ({ status: null, error: String(e) }))
        : { status: null, error: "could not resolve the Supabase Edge Functions base URL" };
      recommendations = resp;
    } else {
      recommendations = { status: null, error: "no Supabase access_token found in page localStorage — could not call /v1/recommendations" };
    }

    await Promise.allSettled(apiEventTasks);

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
    fs.writeFileSync(path.join(personaDir, "api_events.json"), JSON.stringify(apiEvents, null, 2));

    if (recommendations?.status !== expectedStatus) {
      throw new Error(
        `recommendations returned ${recommendations?.status ?? "no status"}; expected ${expectedStatus}`,
      );
    }
    if (expectedStatus === 200 && !recommendations?.body?.plates?.length) {
      throw new Error("recommendations returned HTTP 200 without any dish plates");
    }

    const failedFeatures = featureResults.filter((result) => result.status === "fail");
    const summary = {
      key: persona.key,
      label: persona.label,
      test_user_id: persona.test_user_id || `${persona.user_type || "synthetic"}:${persona.key}`,
      user_type: persona.user_type || "synthetic",
      source_persona_id: persona.source_persona_id || null,
      started_at_utc: startedAtUtc,
      completed_at_utc: new Date().toISOString(),
      ok: failedFeatures.length === 0,
      error: failedFeatures.length
        ? `${failedFeatures.length} feature test(s) failed: ${failedFeatures.map((result) => result.name).join(", ")}`
        : undefined,
      expect_status: persona.expect_status,
      recommendations_status: recommendations?.status ?? null,
      feature_results: featureResults,
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
      feature_results: featureResults,
      steps,
    };
    await Promise.allSettled(apiEventTasks);
    fs.writeFileSync(path.join(personaDir, "recommendation_events.json"), JSON.stringify(recommendationEvents, null, 2));
    fs.writeFileSync(path.join(personaDir, "api_events.json"), JSON.stringify(apiEvents, null, 2));
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

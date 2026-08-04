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
 *   GHAR_SIGNIN_EMAIL / GHAR_SIGNIN_PASSWORD  (a pre-provisioned test account the driver signs
 *     into before each persona's run — onboarding is only reachable while signed in, per
 *     (onboarding)/_layout.tsx's guard. Without these, the driver cannot get past sign-in and
 *     records that as the failure reason for every persona rather than fabricating a pass.)
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

/**
 * bestEffortLogin — signs into the app via the sign-in screen using a pre-provisioned test
 * account, IF one is configured. Onboarding is unreachable while signed out
 * ((onboarding)/_layout.tsx's <Redirect> guard), so without credentials every persona's journey
 * fails identically and honestly at this step rather than the driver fabricating a pass.
 */
async function bestEffortLogin(page) {
  const email = process.env.GHAR_SIGNIN_EMAIL;
  const password = process.env.GHAR_SIGNIN_PASSWORD;
  if (!email || !password) {
    throw new Error(
      "GHAR_SIGNIN_EMAIL/GHAR_SIGNIN_PASSWORD not set — cannot authenticate. Onboarding is " +
      "gated on a signed-in session (see (onboarding)/_layout.tsx); this driver will not fabricate one.",
    );
  }
  await page.goto(new URL("/(auth)/sign-in", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
  // testID-based selectors are the driver's contract with the app; the sign-in screen predates
  // WP-22 and is out of this work package's scope to retrofit, so this falls back to common
  // input roles/placeholders rather than a testID this screen may not have.
  const emailInput = page.locator('[data-testid="signin-email"], input[type="email"], input[placeholder*="mail" i]').first();
  const passwordInput = page.locator('[data-testid="signin-password"], input[type="password"]').first();
  await emailInput.fill(email, { timeout: 10000 });
  await passwordInput.fill(password, { timeout: 10000 });
  const submit = page.locator('[data-testid="signin-submit"], button:has-text("Sign in"), button:has-text("Log in")').first();
  await submit.click({ timeout: 10000 });
  try {
    // handleSubmit awaits signInWithPassword() THEN fetchOnboardingStatus() before navigating
    // (see (auth)/sign-in.tsx) — two sequential network round trips, so this needs real headroom
    // beyond a single request's latency.
    await waitForPath(page, (u) => !u.pathname.includes("sign-in"), 30000);
  } catch (e) {
    // Diagnostic capture, not a fix: without this, every timeout here looks identical (a bare
    // "timed out") regardless of WHY — wrong credentials (errorMsg visible, URL never moves),
    // a network-egress problem in this environment (same symptom), or something else entirely.
    // Surfacing the on-screen error text + a screenshot path turns the next run's failure into
    // actual evidence instead of another blind timeout.
    const errorText = await page
      .locator("text=/invalid|error|incorrect|not confirmed/i")
      .first()
      .textContent({ timeout: 1000 })
      .catch(() => null);
    const shotPath = path.join(outDir, "login-failure.png");
    await page.screenshot({ path: shotPath }).catch(() => {});
    throw new Error(
      `${e.message} | on-screen error text: ${errorText ?? "(none found)"} | screenshot: ${shotPath}`,
    );
  }
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
async function fillChipGroup(page, prefix, values, artifacts) {
  for (const v of values) {
    const el = page.getByTestId(`${prefix}-${v}`);
    if (await el.count()) {
      await el.first().click();
      artifacts.push(await screenshot(page, artifacts, `${prefix}-${v}`));
    }
  }
}

let shotCounter = 0;

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
  const context = await browser.newContext();
  const page = await context.newPage();

  const shot = (label) => screenshot(page, steps, label, personaDir);

  try {
    await bestEffortLogin(page);
    steps.push({ label: "signed-in", screenshot: await shot("signed-in") });

    // Consent — gate on personalization=true so the flow can proceed into step-1.
    await page.goto(new URL("/(onboarding)/consent", url).toString(), { waitUntil: "networkidle", timeout: 30000 });
    steps.push({ label: "consent-loaded", screenshot: await shot("consent-loaded") });
    const consentContinue = page.getByTestId("onboarding-consent-continue");
    await consentContinue.click({ timeout: 10000 });
    steps.push({ label: "consent-continue", screenshot: await shot("consent-continue") });

    const answers = personaToOnboardingAnswers(persona.household);
    const split = isSplitAge(answers.householdType);

    // ---- Step 1 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-1"), 15000).catch(() => {});
    if (answers.householdType) {
      await page.getByTestId(`onboarding-step1-household-${answers.householdType}`).click({ timeout: 10000 });
      steps.push({ label: "step1-household", screenshot: await shot("step1-household") });
    }
    if (answers.workingProfessionals != null) {
      const el = page.getByTestId(`onboarding-step1-earners-${answers.workingProfessionals}`);
      if (await el.count()) {
        await el.first().click();
        steps.push({ label: "step1-earners", screenshot: await shot("step1-earners") });
      }
    }
    await page.getByTestId("onboarding-step1-continue").click({ timeout: 10000 });
    steps.push({ label: "step1-continue", screenshot: await shot("step1-continue") });

    // ---- Step 2 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-2"), 15000).catch(() => {});
    if (answers.homeState) {
      await page.getByTestId("onboarding-step2-state-field").click({ timeout: 10000 });
      const stateOption = page.getByTestId(`onboarding-step2-state-option-${answers.homeState}`);
      if (await stateOption.count()) {
        await stateOption.first().click();
      }
      steps.push({ label: "step2-state", screenshot: await shot("step2-state") });
    }
    if (answers.currentCity) {
      await page.getByTestId("onboarding-step2-city-input").fill(answers.currentCity, { timeout: 10000 });
      steps.push({ label: "step2-city", screenshot: await shot("step2-city") });
    }
    await page.getByTestId("onboarding-step2-continue").click({ timeout: 10000 });
    steps.push({ label: "step2-continue", screenshot: await shot("step2-continue") });

    // ---- Step 3 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-3"), 15000).catch(() => {});
    if (answers.diet) {
      await page.getByTestId(`onboarding-step3-diet-${answers.diet}`).click({ timeout: 10000 });
      steps.push({ label: "step3-diet", screenshot: await shot("step3-diet") });
    }
    await fillChipGroup(page, "onboarding-step3-meat", answers.meatPreferences, steps);
    await fillChipGroup(page, "onboarding-step3-vegday", answers.vegDays, steps);
    await page.getByTestId("onboarding-step3-continue").click({ timeout: 10000 });
    steps.push({ label: "step3-continue", screenshot: await shot("step3-continue") });

    // ---- Step 4 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-4"), 15000).catch(() => {});
    await fillChipGroup(page, "onboarding-step4-allergen", answers.allergens, steps);
    await fillChipGroup(page, "onboarding-step4-condition", answers.medicalConditions, steps);
    if (answers.allergensOther) {
      await page.getByTestId("onboarding-step4-allergen-other-input").fill(answers.allergensOther).catch(() => {});
    }
    if (answers.medicalConditionsOther) {
      await page.getByTestId("onboarding-step4-condition-other-input").fill(answers.medicalConditionsOther).catch(() => {});
    }
    await page.getByTestId("onboarding-step4-continue").click({ timeout: 10000 });
    steps.push({ label: "step4-continue", screenshot: await shot("step4-continue") });

    // ---- Step 5 ----
    await waitForPath(page, (u) => u.pathname.endsWith("/step-5"), 15000).catch(() => {});
    if (split) {
      if (answers.ageEldest) await page.getByTestId(`onboarding-step5-age-eldest-${answers.ageEldest}`).click().catch(() => {});
      if (answers.ageYoungest) await page.getByTestId(`onboarding-step5-age-youngest-${answers.ageYoungest}`).click().catch(() => {});
    } else if (answers.ageSingle) {
      await page.getByTestId(`onboarding-step5-age-single-${answers.ageSingle}`).click().catch(() => {});
    }
    steps.push({ label: "step5-age", screenshot: await shot("step5-age") });
    if (answers.whoCooks) await page.getByTestId(`onboarding-step5-whocooks-${answers.whoCooks}`).click().catch(() => {});
    if (answers.cookCapability) await page.getByTestId(`onboarding-step5-cookcapability-${answers.cookCapability}`).click().catch(() => {});
    if (answers.eatOutFrequency) await page.getByTestId(`onboarding-step5-eatout-${answers.eatOutFrequency}`).click().catch(() => {});
    if (answers.cookingObjective) await page.getByTestId(`onboarding-step5-objective-${answers.cookingObjective}`).click().catch(() => {});
    steps.push({ label: "step5-filled", screenshot: await shot("step5-filled") });

    await page.getByTestId("onboarding-step5-continue").click({ timeout: 10000 });
    steps.push({ label: "step5-finish", screenshot: await shot("step5-finish") });

    // ---- Land on post-onboarding screen (cold-start) ----
    await waitForPath(page, (u) => u.pathname.includes("cold-start") || u.pathname.includes("recommendations"), 20000).catch(() => {});
    steps.push({ label: "post-onboarding-landing", screenshot: await shot("post-onboarding-landing") });

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

    fs.writeFileSync(path.join(personaDir, "recommendations.json"), JSON.stringify(recommendations, null, 2));

    const summary = {
      key: persona.key,
      label: persona.label,
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
      ok: false,
      error: String(e && e.message ? e.message : e).slice(0, 1000),
      steps,
    };
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

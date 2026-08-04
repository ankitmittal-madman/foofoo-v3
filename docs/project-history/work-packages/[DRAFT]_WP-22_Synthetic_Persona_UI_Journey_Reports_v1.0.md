Status: DRAFT
Version: v1.0
Date: 2026-08-04
Placement: docs/project-history/work-packages/[DRAFT]_WP-22_Synthetic_Persona_UI_Journey_Reports_v1.0.md
Supersedes: none

## Executive Summary

`ops/quality/` already has three of the four pieces a "100 synthetic users, screenshot their
journey, show what fired for them" capability needs: 100 personas
(`ops/quality/personas/personas.py`), a black-box recommendation-behaviour suite
(`ops/quality/suites/test_recommendation_behavior.py`), and a real headless-Playwright driver
(`ops/quality/ui/run_ui.mjs`) that already screenshots every screen discovered from
`mobile/app`'s own expo-router tree. None of the three are wired together: the UI driver visits
routes generically, it does not fill in a persona's answers and click through onboarding, and no
report pairs a screenshot sequence with the recommendation the RE actually returned for that same
household. This work package designs and implements the missing bridge.

## 1. Scope

For each of the 100 existing personas: drive the real onboarding UI (steps 1-5 +
consent, `mobile/app/(onboarding)/`) through Playwright using that persona's own q1-q15 answers,
screenshotting every step, then call the recommendation endpoint the UI itself calls and capture
the returned plates. Assemble one HTML page per persona (screenshots in order + the recommendation
payload actually fired) plus an index page. This is Phase 9-11 territory in `ops/quality/README.md`
and inherits its honesty rule: gated on `GHAR_WEB_URL` (needs `expo start --web`), skips loudly with
a reason if not set, never fabricates a run.

Out of scope: changing RE scoring/behaviour, changing onboarding UX/copy, native (iOS/Android)
journeys (web-only, matching the existing Phase 9-11 gate), CI wiring (can follow once proven
locally).

## 2. Why this doesn't already exist

The onboarding screens (`step-1.tsx` … `step-5.tsx`) render option cards from copy strings only —
no `testID`/accessibility hooks — so Playwright can currently only select by visible text. There is
also no reverse mapping from a persona's q1-q15 household dict back to the UI's own answer shape;
today only the forward direction exists (`mobile/src/onboarding/toHouseholdWrite.ts`, UI answers →
API `q1..q15` write). Building the bridge requires both directions to agree.

## 3. Design

1. **Selector stability** — add `testID` props to each selectable option/control across
   `mobile/app/(onboarding)/step-1.tsx` … `step-5.tsx` and `consent.tsx` (visual/copy unchanged;
   additive prop only, per the existing screens' own stated port-fidelity constraint).
2. **Reverse mapper** — `ops/quality/ui/personaToOnboardingAnswers.mjs`: given one persona's
   `household` dict (q1..q15), return the `OnboardingContext` answer shape each step consumes,
   inverting `toHouseholdWrite.ts`'s own per-step forward functions field-by-field so the two stay
   provably in sync (imports/mirrors its field names rather than re-guessing them).
3. **Persona export** — `ops/quality/personas/export_personas.py`: dumps `all_personas()` to JSON
   (key, household, context) so the Node-side driver does not reimplement persona construction.
4. **Journey driver** — `ops/quality/ui/run_persona_journeys.mjs`: for each persona, opens the
   onboarding flow at `/(onboarding)/step-1`, uses the reverse mapper + testIDs to fill/click each
   step in order, screenshots after each step's answer is set and again after each "Continue"
   navigation, and on reaching the post-onboarding recommendation screen also calls the same
   recommendations endpoint the app calls (same contract already asserted in
   `test_recommendation_behavior.py`) to capture the exact plates returned. Writes one JSON summary
   + screenshot set per persona under `GHAR_UI_OUT/personas/<persona-key>/`. Gated on `GHAR_WEB_URL`
   exactly like `run_ui.mjs`; missing testIDs or an unreachable step fails that persona's run with a
   concrete reason, never a silent skip.
5. **Report** — `ops/quality/runner/persona_journey_report.py`: reads the per-persona JSON+PNGs and
   renders one HTML page per persona (screenshot-by-screenshot with step captions) plus an index
   grouping by outcome (200 / 422 / warned), linked from the existing dashboard
   (`runner/orchestrator.py`) as an optional Phase 9-11 artifact, not a new pass/fail gate.
6. **Docs** — update `ops/quality/README.md`'s layout table with the new phase/files.

## 4. Critical Self-Review

- Risk: 100 personas × 5-6 steps × screenshot = several hundred browser interactions; expect this
  to be slow (minutes, not seconds) and to need retry/backoff on flaky RN-web renders — the driver
  must report per-persona failure reasons, not abort the whole batch on one bad persona.
  - **Mitigation (built into the design):** `run_persona_journeys.mjs` isolates each persona's
    Playwright calls in its own try/catch and always writes that persona's summary (`ok: false` +
    `error`) on failure before moving to the next persona — one bad persona cannot abort the batch.
- Risk: adding `testID`s is a real (if additive) change to shipped onboarding source files, not a
  test-only file — must be reviewed as a product-code change, not folded silently into "just a test
  script."
- This capability inherits the existing gate: without `GHAR_WEB_URL` (a running `expo start --web`)
  it cannot run at all in this environment, same as the Phase 9-11 suite it extends.
- No scoring assertions are added — consistent with the RE black-box rule already governing Phase 8.

## 5. Versioning & Placement

v1.0 — initial design + implementation, filed under `docs/project-history/work-packages/` per the
Placement Rule; no new top-level folder (all code lives inside the existing `ops/quality/` tree).
Status stays DRAFT until a companion certificate documents a real, executed run of the 100-persona
journey (per CLAUDE.md's "Status may only read COMPLETED if a companion certificate exists" rule).

Founder Sign-off:


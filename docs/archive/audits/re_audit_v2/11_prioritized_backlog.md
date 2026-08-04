STATUS: ARCHIVED
Reason: Superseded by docs/active/ (2026-08-04 documentation restructure). This audit remains the evidentiary source for docs/active/CURRENT_STATUS.md, OPEN_ITEMS.md, ROADMAP.md, and LAUNCH_BLOCKERS.md.

# Prioritized Engineering Backlog (fresh, 2026-08-04)

## P0 — Launch blockers

### P0-1: Investigate the 126-recommendation-events-but-0-plan-persistence gap
- **Description:** Live DB shows 126 `recommendation_events` rows but 0 rows in `week_plans`, `plan_slots`, `household_context`, `interaction_events`.
- **Why it matters:** Either the plan-persistence write path is silently failing for real users, or these 126 events came from a source that bypasses normal persistence (e.g. testing/synthetic traffic) — either way, this is currently unknown and directly affects whether users' plans are actually being saved.
- **Evidence:** Live `execute_sql` count query, this session.
- **Estimated complexity:** Small to investigate (a few hours of tracing + a live test call), unknown to fix until root cause is known.
- **Dependencies:** None.
- **Suggested order:** First — everything else about "is the RE actually working for real users" depends on knowing this.

### P0-2: Wire DPDP export/delete into the mobile app
- **Description:** `user-export`/`user-delete` Edge Functions are implemented and correctly authorized but have zero mobile UI callers.
- **Why it matters:** India's DPDP Act requires user-initiated data-subject rights. A backend-only implementation is not a compliant implementation.
- **Evidence:** Grep confirmed zero references to either endpoint path anywhere under `mobile/`.
- **Estimated complexity:** Medium (one settings-style screen + two API calls; backend needs no changes).
- **Dependencies:** A profile/settings screen needs to exist first (see P1-4) or this can ship as a standalone minimal screen.

### P0-3: Decide the fate of the two parallel recommendation surfaces
- **Description:** `recommendations.tsx` (with contributions/feedback UI) is dead code; the actively-routed `/v1/plan` family has no explanation or feedback UI.
- **Why it matters:** This is the root cause of P0-4 and P1-2 below — fixing it once is cheaper than patching each symptom separately.
- **Evidence:** `06_e2e_workflow_audit.md`.
- **Estimated complexity:** Medium — mostly a decision (port the good UI patterns to the active surface, or delete the dead screen and rebuild) plus the actual UI work.
- **Dependencies:** None; blocks P0-4 and P1-2.

### P0-4: Give the actively-routed screens a feedback UI
- **Description:** `today.tsx`/`recipe/[dish].tsx` (the actual daily-use screens) have no like/dislike/accept UI at all.
- **Why it matters:** Without this, the feedback pipeline (already built server-side) will never accumulate real data — which is also what's blocking `s_pref` personalization from ever activating.
- **Evidence:** `06_e2e_workflow_audit.md`, `03_recommendation_engine_audit.md` item 9.
- **Estimated complexity:** Medium.
- **Dependencies:** P0-3.

## P1 — Required before public beta

### P1-1: Enable Supabase leaked-password-protection
- **Description:** One Supabase Auth setting, currently off.
- **Why it matters:** Cheap, real security improvement.
- **Estimated complexity:** Trivial (a dashboard toggle).
- **Dependencies:** None.

### P1-2: Build a recommendation-explanation UI
- **Description:** `contributions`/`decision_trace` data exists end-to-end but nothing renders it.
- **Why it matters:** Explainability is a real, already-built differentiator being wasted.
- **Estimated complexity:** Medium.
- **Dependencies:** P0-3.

### P1-3: Build a history/past-plans view
- **Description:** No GET endpoint or UI exists for a household's own past plans.
- **Why it matters:** Basic expected app functionality; currently only a device-local, non-synced cache exists.
- **Estimated complexity:** Medium (needs a new read endpoint + a screen).
- **Dependencies:** None.

### P1-4: Build a profile/preferences-edit screen
- **Description:** No way to change diet/allergens/household composition after onboarding.
- **Why it matters:** Users' circumstances change; a one-time-only onboarding is a real product gap, and this also unblocks P0-2's natural home.
- **Estimated complexity:** Medium-large (needs a GET endpoint too, since `household` is currently write-only).
- **Dependencies:** None.

### P1-5: Add mobile automated tests
- **Description:** Zero test coverage exists for the mobile app.
- **Why it matters:** Every other layer is well-tested; mobile is the one place a regression can ship unnoticed.
- **Estimated complexity:** Large (tooling setup + writing tests for 8 journeys from scratch).
- **Dependencies:** None, but higher-value once P0-3/P1-2/P1-3/P1-4 stabilize the surfaces being tested.

### P1-6: Wire the IDF-cosine distance into pairing/scoring
- **Description:** `similarity.py` implements the frozen spec's `d(a,b)` formula but pairing still uses a set-intersection proxy.
- **Why it matters:** This is the one real algorithmic gap between the frozen spec and the running code; closing it changes golden-master output, so it needs the same reviewed-decision treatment as any scoring change.
- **Estimated complexity:** Medium (the hard part — the cosine machinery — is already built and tested).
- **Dependencies:** A Founder-level decision to accept the scoring change.

### P1-7: Add real monitoring/alerting
- **Description:** Only a log-based shim exists; Sentry/PostHog/APM are seams-only.
- **Why it matters:** If the RE service goes down, nothing currently pages anyone.
- **Estimated complexity:** Medium (the seams already exist per the telemetry.ts design).
- **Dependencies:** None.

## P2 — Production improvements

- **P2-1:** Expand nutrition data beyond 50/810 dishes.
- **P2-2:** Expand comfort-hero mapping beyond 17/36 resolved heroes.
- **P2-3:** Populate PRIOR table for PanIndia/Global zones (187/810 dishes currently get no regional prior boost).
- **P2-4:** Fix RLS policies that re-evaluate `auth.uid()` per-row instead of `(select auth.uid())`.
- **P2-5:** Add a staging/approval gate before `fly_deploy.yml`'s auto-deploy.
- **P2-6:** Pin the Docker base/deploy image by digest, not tag.
- **P2-7:** Archive the dead `re_engine`-era ETL/validation scripts (`generate_re_seeds.py` and 3 validation files) that target dropped schemas.
- **P2-8:** Resolve the unindexed-FK and duplicate-index advisor findings.

## P3 — Future roadmap

- **P3-1:** Festival calendar mapping (currently fully absent).
- **P3-2:** Disease/health-condition dish suitability (currently fully absent; needs real clinical input, not AI-guessed).
- **P3-3:** Activate `s_pref` personalization once feedback volume (currently 9 rows) clears a real training threshold.
- **P3-4:** Build a real multi-hop ingredient/dish knowledge graph (current state is flat lookup tables everywhere).
- **P3-5:** Load-test the RE service at full 810-dish-catalogue scale and re-size the Fly.io machine accordingly.
</content>

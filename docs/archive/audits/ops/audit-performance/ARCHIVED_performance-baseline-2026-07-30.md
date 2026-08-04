# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Performance Baseline — 2026-07-30

REPORT ONLY — measurement-only by this skill's own design; no code changes,
no instrumentation left in the repo.

## Step 1 — Documented performance targets: FOUND

Unlike the skill's "no targets documented" branch, this repo does have
explicit, numeric, sourced performance targets. Found in:

- `docs/architecture/[ACTIVE]_DOC-P3-03A_Logic_Governance_Matrix_v1.0.md`
  (§07, "Latency Target" column) — per-function targets for every named
  logic function (A01–M01), e.g.:
  - Onboarding steps (A01–A07): `< 200ms` per step
  - `OnboardingConfidence` (A08): `< 50ms`
  - `GenerateClassPlan` (B02): `< 300ms`
  - Candidate generation (D01–D07): `< 200ms total`
  - Scoring (E01–E08): `< 200ms per slot`
  - Safety gates (H01–H04): `< 100ms per gate`, blocking
  - Context assembly (I01–I05): `< 500ms` (may include an external API call)
  - `processInteractionEvent` (J01): `< 100ms`
  - Trigger functions `DeriveDishAttribs`/`UpdateGenomeVector`: `< 500ms` /
    `< 200ms` per dish
- `docs/architecture/[ACTIVE]_DOC-P3-03_Business_Logic_Specification_v1.0.md`
  (line 82, 1431) — "Full pipeline must complete in < 800ms for Edge
  Function execution. Total end-to-end (network + render): < 3s on Pixel 3a
  reference device." Explicitly sourced: `[Source: DOC-10 §07, DOC-04 NFR]`.
- `docs/architecture/[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md`
  §18.2 "Latency targets (reproduced from source, not newly invented)" —
  the canonical per-endpoint table:
  | Endpoint | Target | Source |
  |---|---|---|
  | `/v1/consent` | `<200ms` | DOC-P3-03A §07 |
  | `/v1/onboarding` (per step) | `<200ms/step` | DOC-P3-03A §07 |
  | `/v1/recommendations` | `<800ms` Edge Function execution; `<3s` total end-to-end | DOC-P3-03 §02, DOC-04 NFR |
  | `/v1/events` | `<100ms` log-only; Never/Not-Today sub-path `<200ms` | DOC-P3-03A §07 |
  | `/v1/health` | `<50ms` | infrastructure check |

The original source of record is `docs/architecture/[ACTIVE]_DOC-04_PRD_v1.1.docx`
(NFR section) — the `.md` files above all explicitly cite it rather than
inventing their own numbers, which is the correct pattern this skill itself
requires.

**Conclusion for Step 1: targets are documented and authoritative — this is
not a "no targets found, ask the user" situation.**

## Step 2 — Mapping targets to measurable code, and why measurement stopped here

Mapped each target to a real code location:

| Target | Maps to | Found in repo |
|---|---|---|
| `/v1/recommendations` <800ms Edge Function | `supabase/functions/recommendations/handler.ts` (+ `re-client.ts`, `metrics.ts`, `fallback.ts`, `events.ts`) | Yes — source present |
| `/v1/consent` <200ms | `supabase/functions/consent/handler.ts` | Yes — source present |
| `/v1/household`-related | `supabase/functions/household/handler.ts`, `store.ts`, `schema.ts` | Yes — source present |
| Onboarding <200ms/step, total app launch/load time | Mobile app entry point under `mobile/app/`, `mobile/src/` | Yes — source present |
| DB trigger latency (K01/K02, <500ms/<200ms per dish) | Trigger functions defined in migration `010_trigger_functions_and_triggers.sql` | Yes — source present |

**Why no live measurement was taken:** every one of these targets is a
runtime metric (Edge Function execution time, DB trigger execution time,
mobile app render time on a Pixel 3a reference device) that requires either
a deployed/running Supabase project or a running local Supabase stack
(`supabase start` + `supabase functions serve`) with the seed data loaded,
plus a running mobile client to hit `<3s>` end-to-end. This session has:

- No linked/authenticated live Supabase project (no project ref, no
  credentials confirmed reachable in this environment).
- No local Supabase stack running (`supabase/config.toml` exists for local
  dev, but no stack was started as part of this report-only audit).
- No mobile app build/emulator running to measure end-to-end render time.

Per this skill's own governing principle — do not invent a target, and by
the same logic do not invent a "measured" number either — fabricating
timing figures without actually executing the code would produce a
misleading report, which the skill exists specifically to prevent. Rather
than simulate plausible-looking numbers, this run stops at the mapping
stage and reports the gap honestly.

## Step 3 — Measurement: NOT PERFORMED (environment gap, not a targets gap)

No timing instrumentation was added; no runs were executed; no numbers are
reported as measured or estimated. This section intentionally contains no
data — see Step 2 for why.

## Step 4 — What would be needed to actually run this audit

1. Either: (a) a reachable live Supabase project for this app (project ref
   + credentials), or (b) `supabase start` run locally with migrations
   `001`–`038` and seeds `100`–`121` applied (see the rollback-readiness
   report run alongside this one for known seed-completeness caveats around
   `101`/`102`).
2. `supabase functions serve` (or deployed Edge Functions) reachable to
   time `/v1/consent`, `/v1/onboarding`, `/v1/recommendations`, `/v1/events`,
   `/v1/health` directly with real HTTP calls, 5 runs each per this skill's
   own default.
3. For the mobile end-to-end `<3s>` target specifically: a running Expo
   build, ideally on or emulating the Pixel 3a reference device named in
   the NFR.
4. For DB trigger targets (K01/K02): direct timed `INSERT`/`UPDATE`
   statements against a live database with the trigger functions installed
   from migration `010`.

## Step 5 — Cleanup

N/A — no instrumentation was added to the codebase this run, so there is
nothing to remove or gate behind a debug flag.

## Audit completed 2026-07-30
Targets documented: Yes — 5 endpoint-level + ~20 function-level targets,
  all sourced to DOC-04 NFR / DOC-P3-03A / DOC-P3-03 / DOC-P3-06.
Metrics measured: 0
Targets met: N/A — not measured
NEEDS_OPTIMISATION: N/A — not measured
Estimated (not directly measured): 0

**Outcome: targets exist and are clearly documented, but no live or local
runtime was available in this session to actually measure against them.**
This report is a targets inventory + measurement plan, not a baseline —
recommend re-running this skill with either live Supabase access or a
local `supabase start` stack so real numbers can be recorded next time.

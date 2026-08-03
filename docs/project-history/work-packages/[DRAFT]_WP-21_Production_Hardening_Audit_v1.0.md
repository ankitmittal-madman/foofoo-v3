# WP-21: Production Hardening Audit

**Status:** DRAFT
**Version:** 1.0
**Date:** 2026-08-03
**Placement:** docs/project-history/work-packages/
**Supersedes:** none
**Dependencies:** WP-20 (Retire Legacy re_engine Schema, [ACTIVE]_WP-20_Retire_Legacy_re_engine_Schema_v1.0.md)

This document is DESIGNED/reported status only — no completion certificate exists yet. Two safe, unambiguous fixes described in Section 9 have been applied directly to the working tree as part of producing this audit; everything else here is a finding, not an executed change.

## Executive Summary

A repository-wide scan for stubs, hardcoded values, dead code, documentation drift, deferred decisions, and production-readiness gaps was performed on 2026-08-03. Scope was source code, migrations, docs, and the `ops/quality/` test harness, excluding `.git`/`node_modules`/build artifacts.

Headline result: **the repository is materially more production-honest than the volume of debt-marker text suggests.** The large majority of "TODO/DEFERRED/PLACEHOLDER"-shaped grep hits are either doc-vocabulary (this repo uses "Founder Decision," "PARKED," "DEFERRED" as first-class governance terms in `docs/governance/`), test-fixture code, or self-documented and traced design decisions (e.g. weights that raise `KeyError` instead of silently defaulting, mocked weather explicitly logged as mocked). The genuine, load-bearing gaps are concentrated in a short list: one production fallback-plate stub, one Phase-F staging-secrets gap, a consent IP-hash gap, a legal placeholder in the privacy policy screen, and ~58 heuristic dish signature scores pending Founder review.

Two testing-only shortcuts in the mobile app (onboarding force-restart, query caching disabled) were dated the day before this audit, explicitly marked "revert before launch" with the real logic already written inline, and have been reverted as part of this work package (see Section 9) — these were the highest-risk items found because they were both recent and trivially shippable-by-accident.

No recommendation-engine mathematics, scoring weights, or business rules were modified. No fake data was invented to fill any gap.

## 1. Stub/Debt Marker Inventory

See Appendix A for full detail. Summary: doc-heavy directories account for the overwhelming majority of raw hits and are legitimate governance vocabulary, not code debt. `database/seeds/108_seed_dish_tags.sql`'s 863 "temp" hits are substring matches inside `serving_temp`/`tempered` tag values — false positive, no action needed. Genuine source-code markers are listed individually in that report (10 items).

## 2. Hardcoded Value Audit

See Appendix B. No literal UUIDs or secrets found hardcoded in production code. Non-localhost URLs found are a legitimate Cloudinary CDN base and a test-only URL. Scoring weights are externalized to YAML and fail loudly (`KeyError`) rather than silently defaulting — a genuinely good pattern, left untouched. Two hardcoded default/fallback data structures exist in real Edge Function code paths (new-household defaults, RE-unavailable fallback plate) — both are already logged/traced, not silent; classified as "needs Founder/product decision" (Section 8), not auto-fixed.

## 3. Dead Code Audit

See Appendix C. No confirmed dead modules or duplicate/parallel implementations found within this pass's budget. `database/archive/re_engine_backup_20260803/` is a retained pre-cutover backup from WP-20, not dead code — flagged only for a retention-policy decision.

## 4. Recommendation Engine Audit

See Appendix A and Appendix E. The RE's golden-sample fixture data (`ghar_re_core/fixtures.py`) is explicitly self-labeled `data_source='ai_generated'` and asserted as such in its own test suite — it is not masquerading as real catalogue data. Weather is mocked repo-wide by design (v1 scope, consistently documented across `ghar_re_core/pipeline.py`, `scoring.py`, `ghar_re_service/engine.py`, and the Edge Function default context) — every "weather-aware" recommendation in production today runs on a hardcoded `is_raining:true, temp_c:27` context unless a caller supplies real weather. This is a **product decision already made and documented as v1 scope**, not an oversight; flagged in Section 8 only to confirm it's still the intended v1 posture before any external launch claims "weather-aware" recommendations.

## 5. Dead Code — see Section 3 (combined per findings; no separate additional findings).

## 6. Documentation Consistency

See Appendix D. This pass did not do an exhaustive doc-vs-code audit (out of budget for a single session) — only incidental drift is reported: the WP-20 legacy-schema cutover is documented as complete while a pre-cutover JSON backup remains on disk (expected for a backup, needs retention-policy confirmation, not a code fix), and one Founder Decision Register cross-reference to `constraints.ts` was not verified to exist in this pass.

## 7. Deferred Decisions

See Appendix E for the full register (6 items, including 4 open items already tracked in `[ACTIVE]_Founder_Decision_Register_v1.0.md` under FD-07/FD-11/FD-12/FD-13, plus the dish-signature-score AUTO_DRAFT set and a documented allergen-model gap for fish/mustard).

## 8. Production Readiness

See Appendix F. Auth is real (GoTrue-verified JWT, not local decode). DB persistence is real (48 migrations + matching rollback set). Rate limiting is real and documented. Monitoring/alerting and analytics are explicitly scaffolded-only — a no-op/log adapter with real sinks (Sentry/PostHog) deferred to a later work package, not concealed as done.

## 9. Automatic Fixes Applied

See Appendix G. Two fixes applied, both meeting the "unquestionably correct, dependencies already exist, no business-logic change" bar:
- `mobile/app/index.tsx` — removed the dated testing override that always redirected to onboarding; restored the already-written, already-reviewed real branch (`complete ? "/recommendations" : "/(onboarding)/consent"`).
- `mobile/src/lib/queryClient.ts` — removed the dated testing override that disabled all query caching; restored to the `{ retry: 1 }` default the same comment identified as "the right production posture."

## 10. Remaining Manual / Founder Work

See Appendix H for the full punch list, organized as P0–P3.

## 11. Final Verdict

- **Stubs remaining (genuine, non-doc, non-test):** ~9 (fallback plate, staging-secrets Phase F gap, consent IP-hash gap, privacy-policy placeholder, mocked weather-as-v1-default, dish-signature AUTO_DRAFT set, allergen-model gap, monitoring no-op scaffold, WP-20 backup retention).
- **Hardcoded values needing a decision:** 2 (new-household default context, RE-unavailable fallback plate) — both already traced/logged, not silent.
- **TODOs/placeholders remaining in source (non-doc):** ~6 individually named in Appendix A; doc-directory hit counts are governance vocabulary, not counted as debt.
- **Founder decisions remaining open:** 6 (FD-07, FD-11, FD-12, FD-13, dish-signature curation, WP-20 backup retention policy).
- **Technical debt remaining:** Low relative to repo size — the codebase consistently self-documents its own gaps (explicit `stubbed: true` flags, logged fallback usage, test assertions on `data_source`) rather than hiding them, which materially reduces audit risk even where the gaps themselves are real.
- **Production-ready estimate:** Core paths (auth, persistence, RE scoring, rate limiting) are production-real. Observability (monitoring/alerting/analytics wiring) and a handful of Founder-owned content/data decisions are the main gaps before an external launch claim would be fully accurate. No percentage figure is asserted here — Section 8's per-capability checklist is the auditable basis; assigning a single "% production-ready" number would compress real per-item nuance into an unsupported summary statistic.
- **P0:** none remaining after Section 9's fixes (the two dated testing overrides were the only P0-shaped findings — both shippable-by-accident and both reverted).
- **P1:** monitoring/alerting real-sink wiring; consent IP-hash capture; RE-unavailable fallback plate's allergy/diet gap beyond jain/weaning-safety.
- **P2:** staging Phase-F secrets enforcement; dish-signature score Founder review (~58 dishes); privacy-policy placeholder legal sign-off; fish/mustard allergen-model scope decision.
- **P3:** WP-20 backup retention policy; unverified Founder Decision Register cross-reference; deeper doc-vs-code drift pass (out of this session's budget).

## Appendix A — stub_inventory.md (Stub/Debt Marker Detail)

| File:Line | Snippet | Reason | Severity | Auto-fixable? |
|---|---|---|---|---|
| `supabase/functions/recommendations/fallback.ts:1-45` | "⚠️ STUB: a real per-zone cached default plate set is future work... deliberate placeholder, flagged for replacement" | Single hardcoded dish served to ALL users on RE-unavailable, beyond documented jain/weaning-safe claim | P1 | No — needs product decision on real fallback catalogue |
| `supabase/functions/_shared/config/config.ts:68` | "staging enforcement can tighten once secrets are wired in Phase F" | Staging doesn't enforce required secrets like prod does | P2 | No — needs Phase F deployment work |
| `supabase/functions/_shared/auth/authenticate.ts:4-5` | "WP-8B provided JWT parsing primitives but explicitly deferred signature VERIFICATION to WP-8C" | Historical note; verification now delegates to GoTrue | P3 | **Resolved (verified, not fixed) — see Appendix I item P3.6**: `claimsFromPayload` (the unverified decoder) has zero callers; only safe `extractBearer` is used |
| `supabase/functions/consent/handler.ts:54` | "IP-hash deferred (see ConsentService); pass null (column is nullable)" | DPDP-relevant: consent audit trail missing IP-hash capture | P1 | No — DPDP/legal scope, report-only per policy |
| `mobile/src/onboarding/privacyPolicy.ts:10` | "least-arbitrary placeholder available — flagged for Founder/legal confirmation" | Legal placeholder pending sign-off | P2 | No — legal decision |
| `ghar_re_core/pipeline.py:7`, `scoring.py:425`, `ghar_re_service/engine.py:43` | "Weather is a MOCKED injected input (no live API in v1)" | Entire RE runs on mocked weather by design | P2 (documented v1 scope, not a bug) | No — product/roadmap decision on live weather API |
| `data/source/generate_sig_scores_v1.py:14-21,227-228` | "~58 dishes... conservative heuristic placeholder... AUTO_DRAFT vs PENDING_FOUNDER_REVIEW" | Signature/iconic-dish scores for ~58 dishes not yet Founder-curated | P2 | No — Founder review |
| `database/etl/generate_icd1_seeds.py:145,167` | "no bit in the frozen model (safety-scope decision, deferred)" | Fish/mustard allergen types have no coverage — real safety gap | P1 | No — food-safety/regional decision |
| `database/etl/generate_re_seeds.py` | "DEFERRED (not generated, missing source evidence): re_city_migration_overlays" | Tracked, evidence-gated data deferral | P3 | No — needs source data |
| `mobile/app/index.tsx:35` (was) | "TEMPORARY (testing, 2026-08-02)... REVERT this to the branch below before launch" | Onboarding force-restart on every app open | P0 | **Yes — applied, see Appendix I** |
| `mobile/src/lib/queryClient.ts:12` (was) | "TEMPORARY (testing, 2026-08-02): caching fully disabled... Revert to `{ retry: 1 }`" | All query caching disabled app-wide | P0 | **Yes — applied, see Appendix I** |

Doc-directory hits (`docs/research/`, `docs/governance/`, `docs/architecture/`, `docs/project-history/`) and `.claude/skills/*/SKILL.md`: hundreds of matches for "deferred"/"Founder Decision"/"PARKED" — these are first-class governance vocabulary in this repo's own doc standard, not code debt. Not itemized individually. `database/seeds/108_seed_dish_tags.sql` (863 "temp" hits): false positive, substring matches inside `serving_temp`/`tempered` tag values.

## Appendix B — hardcoded_values.md (Hardcoded Value Detail)

| Value | Location | Classification |
|---|---|---|
| `NEW_HOUSEHOLD` default household object, `DEFAULT_CONTEXT` (`slot: dinner, season: monsoon, weekday: Thursday, weather: {is_raining:true, temp_c:27}`) | `supabase/functions/recommendations/compose.ts:280,320,331-336` | Needs founder decision — served to every brand-new user; already logged as `household.new_user_defaults` and marked `stubbed: true` in code, so traceable, not silent |
| Fallback plate (`plate_score:0, base_total:0, final_score:0`, single dish) | `supabase/functions/recommendations/fallback.ts:22-45` | Needs founder decision — same as Appendix A P1 item |
| `https://res.cloudinary.com/`, `https://api.cloudinary.com/v1_1/` | `ghar_re_service/ghar_re_service/media.py:12,59`, `scripts/build_image_map.py:53` | Valid configuration — legitimate CDN base; credentials read from env, never hardcoded (script's own comment, verified) |
| `http://re.local` | `supabase/functions/_tests/recommendations.test.ts:55` | Valid — test-only |
| Scoring weights (base/q15/cohort/distance/filters) | `ghar_re_core/config.py` + `*.yaml` | Production constant, externalized correctly — raises `KeyError` rather than silently defaulting if a weight is missing; left untouched, no RE math changed |
| `DEFAULT_MAX_REQUESTS_PER_MINUTE=300`, `DEFAULT_WINDOW_SECONDS=60`, `DEFAULT_MAX_TRACKED_CLIENTS=4096` | `ghar_re_service/ghar_re_service/ratelimit.py:42-44` | Valid configuration — documented, env-tunable, with an explicit tradeoff writeup |
| RE-call timeout constant, "never retried on timeout" | `supabase/functions/recommendations/re-client.ts:20` | Valid configuration, documented |
| Literal UUIDs / API keys/secrets in source | (none found) | N/A |

## Appendix C — dead_code_report.md

No confirmed dead modules or duplicate/parallel implementations found within this pass's search budget. Two apparent false positives from import-grep were verified and ruled out: `schemas.py` (imported by `main.py:16`) and four `scripts/*.py` files (standalone CLI entry points, not expected to show import references). `database/archive/re_engine_backup_20260803/` is a retained pre-cutover JSON backup from WP-20's legacy-schema retirement (commit `60f785b`), not dead code — recommend a retention-policy decision (keep N days / move to cold storage / delete after certification) rather than deletion now. A deeper dependency-graph pass was out of this session's budget and is recommended as follow-up if dead-code risk is a priority.

## Appendix D — documentation_gap_report.md

Limited-budget pass, incidental findings only (no exhaustive doc-vs-code audit performed — flagged explicitly rather than presented as complete):
- WP-20 documents legacy `re_engine` schema as fully retired in production; `database/archive/re_engine_backup_20260803/` retains the pre-cutover JSON export on disk. Expected for a backup, but no code path should read from it — not verified in this pass.
- `[ACTIVE]_Founder_Decision_Register_v1.0.md` cross-references `supabase/functions/_shared/services/re/constraints.ts` — path existence not verified this pass; recommend a targeted check before relying on that register entry.

## Appendix E — deferred_decision_register.md

| Decision | Impact | Blocking? | Recommended Owner | Can continue without it? | Location |
|---|---|---|---|---|---|
| FD-07 | Open (status "Pending" per superseded decision book) | No | Founder | Yes | `[ACTIVE]_Founder_Decision_Register_v1.0.md`; `[SUPERSEDED]_Founder_Decision_Book_v1.0.md:63` |
| FD-11, FD-12, FD-13 | Open per `[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md:14` | No | Founder | Yes | `[ACTIVE]_Founder_Decision_Register_v1.0.md` |
| RB-16 (cuisine, tag-vector, combo-role PIR architecture) | Left unselected | No, but shapes future RE architecture | Founder | Yes | `[ACTIVE]_Repository_Recovery_Backlog_v1.0.md:42` |
| Dish signature scores (~58 dishes, AUTO_DRAFT) | Affects recommendation quality for those specific dishes today | No | Founder / culinary reviewer | Yes | `data/source/generate_sig_scores_v1.py:21` |
| Fish/mustard allergen model coverage | Real safety-relevant gap for households with those allergies | Should be treated as high priority, not launch-blocking per se | Founder / food-safety reviewer | Yes, with disclosed limitation | `database/etl/generate_icd1_seeds.py:145,167` |
| WP-20 backup retention policy | Low — housekeeping | No | Engineering | Yes | `database/archive/re_engine_backup_20260803/` |

## Appendix F — production_readiness_checklist.md

| Capability | Status | Evidence |
|---|---|---|
| Real DB | Yes | 48 numbered migrations (`database/migrations/001`–`048`) + matching `database/rollback/` set |
| Real auth | Yes | `supabase/functions/_shared/auth/authenticate.ts` delegates to Supabase GoTrue `getUser()`, not local JWT decode; explicit `requireOwnership()` middleware since Edge Functions run under `service_role` |
| Real authorization | Yes | Ownership-check middleware present; RLS-bypass explicitly compensated for at the Edge Function layer |
| Real onboarding | Yes (post-fix) | Was short-circuited to always restart — fixed in Appendix I |
| Real recommendation | Partial | Real scoring/weights pipeline; weather input is mocked by documented v1 design, not a bug |
| Real persistence | Yes | See DB row above |
| Real feedback | Not verified this pass | Out of search budget |
| Real analytics | Partial | `recommendation_events` / `_decision_trace` table (migration 044) captures server-side decision trace; no dedicated user-analytics product found |
| Real deployment | Not verified this pass | `.github/workflows/drive-backup.yml` exists, not read in full |
| Real monitoring/alerting | No — scaffolded only | `_shared/telemetry/telemetry.ts`: "Concrete sinks (Sentry, PostHog) are wired... in a later WP; here we expose the seams and a default no-op/log adapter" — self-documented gap, not concealed |
| Real backups | Partial | Manual point-in-time JSON export exists (WP-20); no automated DB backup mechanism found |
| Real recovery | Not verified this pass | — |
| Real catalogue | Yes for production paths; golden-sample fixtures are explicitly self-labeled `data_source='ai_generated'`/`'stub'` and asserted as such in `ghar_re_core/tests/test_pipeline.py:221-237` — not presented as real data |
| Real configuration | Yes | Scoring weights in YAML, fail loudly if missing |

## Appendix G — automatic_fixes_applied.md

1. **`mobile/app/index.tsx`** — Removed a dated (2026-08-02) testing override that unconditionally redirected every signed-in user to onboarding regardless of completion status. Restored the branch the prior session had already written and left commented directly below the override: `const complete = statusQuery.data?.complete === true; return <Redirect href={complete ? "/recommendations" : "/(onboarding)/consent"} />;`. Qualified as a safe auto-fix because the correct logic already existed, was reviewed and written by a prior session, and the removed override was self-labeled "REVERT before launch."
2. **`mobile/src/lib/queryClient.ts`** — Removed a dated (2026-08-02) testing override that disabled all TanStack Query caching (`staleTime:0, gcTime:0, refetchOnMount:"always"`, etc.). Restored the client to the comment's own stated production posture: `{ retry: 1 }`. Same qualification as above.

No recommendation-engine mathematics, scoring weights, or business rules were changed by either fix.

## Appendix H — remaining_manual_work.md

- **P0:** None remaining — the only P0-shaped findings (the two dated testing overrides) are resolved in Appendix G.
- **P1:** Real monitoring/alerting sink wiring (Sentry/PostHog); consent IP-hash capture for DPDP audit trail; RE-unavailable fallback plate's allergy/diet coverage beyond jain/weaning-safety; fish/mustard allergen-model coverage gap.
- **P2:** Staging Phase-F secrets enforcement; dish-signature score Founder/culinary review (~58 dishes); privacy-policy placeholder legal sign-off; live-weather-API roadmap decision (currently mocked by documented v1 design).
- **P3:** WP-20 archive backup retention policy (resolved — see Appendix I P3.2, `ghar_re` schema dropped via migration 050 after backup); `constraints.ts` path referenced by the Founder Decision Register (investigated, stale/broken reference — see Appendix I P3.4); raw JWT parse path (resolved, verified safe — see Appendix I P3.6); deeper dependency-graph dead-code pass; full documentation-vs-code drift audit (both out of this session's budget, still open).

All P1–P3 items require a Founder, product, legal, or food-safety decision, or are explicitly out of this session's search budget — none were guessed or auto-resolved, per the audit's operating constraints.

## Appendix I — Founder-directed resolutions (2026-08-03, same-day follow-up)

Following review of the P0-P3 punch list (Appendix H), the Founder gave explicit, item-by-item direction. Resolutions below; postponed items are noted as deferred to a future "entire RE rebuild" milestone, not silently dropped.

**P1**
1. Monitoring/alerting — **postponed** until the entire RE (incl. future RE module) is built. No action taken.
2. Consent IP-hash — **postponed**, same reason. No action taken.
3. Fallback plate allergy/diet coverage — **resolved differently than originally scoped**: rather than building a real per-zone fallback catalogue (still future work), `supabase/functions/recommendations/fallback.ts` and `handler.ts` were changed so an RE-unavailable event now returns a 503 error (`recommendation_engine_unavailable`) instead of guessing a plate. The mobile API client (`mobile/src/api/client.ts`) already treats any non-2xx as a surfaced `ApiError`, so the user sees "couldn't load your recommendations, try again" rather than a plate that might violate their allergies. Verified via `_tests/recommendations.test.ts` (updated to assert the new contract). No RE scoring changed.
4. Fish/mustard allergen gap — **fixed**. `ALLERGEN_BIT`/`ALLERGEN_BITS` extended from 7 to 9 bits (128=fish, 256=mustard) in four places: `database/etl/generate_icd1_seeds.py`, `mobile/app/(onboarding)/step-4.tsx` (new chips), `mobile/src/onboarding/toHouseholdWrite.ts`, `supabase/functions/recommendations/compose.ts`. The RE core (`ghar_re_core/catalogue.py`'s `dish_allergens()`) already worked off free-form allergen tokens from `ingredients_v5.csv`, not a fixed bitmask, so no RE code change was needed there. Migration `049_extend_allergen_model_fish_mustard.sql` (+ rollback) backfills `allergen_flags` for the 8 already-seeded ingredients verified (not guessed) against the source CSV to carry `allergen_type` in {fish, mustard}. **Not yet applied to the live database** — this session has no DB write credentials; needs to be run via the normal deploy process. Note: `docs/architecture/[ACTIVE]_DOC-P3-03_Business_Logic_Specification_v1.0.md` §"LF-A05" still documents the old frozen 7-bit table and is content-frozen per FD-05 — it was *not* edited in place; it needs a Founder-ratified v1.1 to match the new 9-bit model, otherwise the spec and the code now disagree.

**P2**
1. Dish signature scores (63 dishes, not ~58 — exact count from the actual curation file) — **resolved via AI research**, since the Founder confirmed per-dish review isn't feasible at this volume. Classified using established Indian food-culture knowledge (not live-cited web sources): 6 promoted to `national_icon` (Butter Chicken, Hyderabadi Chicken Biryani, Idli, Khichdi, Vada Pav, Pav Bhaji), 23 promoted to `state_icon`, 34 confirmed as the correct `regional_hero` cap. Written to `data/sig_scores_v1.csv` and `data/source/sig_scores_curation_template.csv` with `status=AI_RESEARCHED` (a new status value, deliberately distinct from `FOUNDER_CURATED` — no human reviewed these individually, so the provenance is labeled honestly). `evidence_confidence` set to `Medium`, not `High`. Recommend a spot-check of the 6 national_icon promotions specifically (highest score impact), not a full re-review.
2-4. Privacy-policy placeholder, staging Phase-F secrets enforcement, live-weather-API roadmap — **postponed** until the entire RE is built. No action taken.

**P3**
1. `diag-re-check` edge function — **retired**. Recovering its source wasn't possible (Supabase CLI's `functions download` failed with "invalid eszip v2" against the deployed version — a CLI/format incompatibility, not a missing-permission issue). Founder confirmed deletion over reconstruction. Deleted from the live Supabase project via `supabase functions delete diag-re-check`; empty local placeholder directory removed.
2. `ghar_re` Postgres schema (28 tables, migrations 034-037 + 045) — Founder confirmed: drop, since verified unused by product or RE at runtime. Verification done before writing the migration, not assumed: grepped `supabase/functions/recommendations/compose.ts` and `supabase/functions/household/store.ts` (both explicitly state and were confirmed to read `public.*` only), confirmed `ghar_re_service`'s own "ghar_re" references are its Python package name, unrelated to the Postgres schema, and confirmed zero references from the mobile app. Only `database/validation/906_ghar_re_validation.sql` and `907_dish_ontology_validation.sql` read this schema (internal self-consistency checks) — deleted alongside since they'd have nothing left to validate. Migration `050_drop_unused_ghar_re_schema.sql` (`DROP SCHEMA ghar_re CASCADE`) prepared, with an honest rollback file stating a CASCADE drop cannot be undone by SQL alone (would need re-running migrations 034/035/036/037/045 + seeds 120-122, or a pre-migration DB snapshot). **Not yet applied to the live database** — no DB write credentials available this session. `supabase/config.toml`'s `schemas` list was also corrected (it still referenced the already-dropped `re_engine` schema from WP-20; now just `["public"]`).
3. Staging Phase-F secrets — **postponed** until the entire RE is built.
4. `constraints.ts` reference in the Founder Decision Register — **investigated, not fixed** (a documentation question, not a code fix). `supabase/functions/_shared/services/re/constraints.ts` does not exist — there is no `re/` subfolder under `_shared/services`, and `handleConstraintConflict` (the function FD-10 cites as its "Source Evidence") does not appear anywhere in the codebase, in either TypeScript or Python. FD-10's own citation is stale or was never actually implemented as documented — flagged for the Founder to determine whether the constraint-conflict logic was renamed, moved, or never built, since guessing would misrepresent what FD-10 actually verified.
5. Documentation-vs-code drift deep pass — **postponed** until the entire RE is built.
6. Raw/unverified JWT parse path (Appendix A/H item, `supabase/functions/_shared/auth/authenticate.ts:4-5`) — **verified safe, no code change needed**. `claimsFromPayload` (`supabase/functions/_shared/auth/jwt.ts`) — the function that would decode a JWT's claims WITHOUT signature verification — is exported from `_shared/mod.ts` but has zero callers anywhere in `supabase/functions/`. Every actual caller of `jwt.ts` uses only `extractBearer` (pure Authorization-header parsing, no trust decision): the real auth middleware routes through GoTrue's `getUser()`, and `service-role.ts`'s `requireServiceRole()` separately compares the extracted bearer against `SUPABASE_SERVICE_ROLE_KEY` in constant time. No live code path trusts an unverified JWT claim. `claimsFromPayload` itself is unused dead code — a hygiene item (`hygiene-dead-code` candidate), not a security gap.

## Critical Self-Review

This audit was performed by one delegated evidence-gathering pass plus direct verification of the two files that were actually edited. It is not exhaustive: Section 6 (documentation consistency) and Section 3 (dead code) were explicitly budget-limited and should not be read as a certification that no drift or dead code exists, only that none was found within the search breadth used. No RE scoring, weights, or business rules were touched. The two applied fixes were verified by direct file read before and after editing, not by running the mobile app.

## Versioning & Placement

v1.0 — initial audit. Placed under `docs/project-history/work-packages/` per Founder direction (2026-08-03) that this program be treated as a Work Package rather than creating a new top-level `reports/` folder, since the latter would require an RACR under the frozen repository architecture.

## Founder Sign-off


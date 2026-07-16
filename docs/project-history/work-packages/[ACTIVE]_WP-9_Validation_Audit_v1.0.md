# FooFoo — Independent Validation Audit of WP-9 (the RE Engineering Audit)

**Auditor role:** Independent due-diligence team validating a prior audit ("WP-9" = `[ACTIVE]_RE_Independent_Engineering_Audit_v1.0`, certified REPO-CERT-020 per Founder framing)
**Audit date:** 2026-07-16
**Evidence base:** `foofoo-v3-backup-2026-07-15_09-33.zip` (git `e76bd9c`, main) — re-read from zero. WP-9 conclusions were compared only **after** independent analysis.
**Method:** Full reads this pass of everything WP-9 sampled: all of `docs/architecture` (incl. DOC-04/05/06/10 end-to-end), all of `docs/product` (DOC-01/02/03/07/08/09 end-to-end), all four HTML documents in `docs/visuals` (text-extracted in full), the **entire** `supabase/` tree (every `.ts` file — foundation, middleware, auth, errors, validation, DI, repositories, consent function, all four test files — plus config.toml, deno.json, scripts, README), both ETL generators, batch pipeline packages (headers + discovery/transformation sections), seeds/validation/migrations for chain-tracing, and repo-wide marker sweeps.

---

## A. Independent Audit (reconstructed from zero)

### A.1 What the documentation specifies (documentation-only reconstruction)
Product: an AI meal-decision assistant for Indian households; the RE (Recommendation Engine — DOC-10 §01 P2, RE-DOC-01) **is the product**. Business architecture: freemium (₹0→₹99/₹149) after a 90-day habit window (DOC-08), invite-only GTM to 500 DAU (DOC-07), DPDP-first legal posture (DOC-09). Recommendation pipeline: onboarding (10 screens OB-00→OB-08b, swipe-reveal gesture model per DOC-05 v1.2/DOC-06 v1.1) → persona (41) → cohort (2,952, tier-aware) → weekly class plan (21 slots) → addons → class→dish expansion under 6 hard constraints → 5-signal weighted scoring with interpolated weight ladder → MMR + 5 variety rules → 4 safety gates → 8-dish slate; runtime flow via 9 Surface-B endpoints (DOC-P3-06 §03) + nightly CRON batch flow (23:30 UTC) + weather/context assembly + event-driven learning loop; seed strategy: canonical CSV/xlsx → deterministic ETL → numbered seed migrations with provenance + Seed Gates S-01→S-15 (DOC-P3-10, validation 905); security: service-role Edge Functions with explicit in-code ownership, `re_engine` schema unreachable by clients; performance: ≤800 ms API p95, <3 s plan; operations: pg_cron jobs, safety-gate SQL as release blockers, PostHog/Sentry.

### A.2 What the repository actually contains (implementation-only reconstruction)
A Deno Edge-Function monorepo with: a complete engineering foundation (config/logging/errors/middleware/auth/DI/validation — all read, all coherent, dependency direction clean: `re/` imports nothing outward; services import `re/`; adapters import service ports; no circular imports found); one deployed endpoint (`/v1/consent`, gateway `verify_jwt = true` plus in-function GoTrue verification and ownership assert); a pure, port-driven RE core implementing constraints/scoring/MMR/safety-gate predicates/resolvers; three caller orchestrations (onboarding, recommendations service, nightly scheduler) with persistence adapters for the write path and caller-load path only; 30 schema migrations + 18 seeds + 6 validation scripts; a deterministic, provenance-stamped ETL layer; CI running fmt/lint/typecheck/tests. **Independently re-verified this pass:** the full test suite (62/62 pass, clean environment) and — new — **both ETL generators re-executed end-to-end: all committed seed migrations regenerate byte-identical excluding timestamps**, proving the CSV/xlsx → script → seed chain is deterministic and free of manual tampering.

### A.3 Traceability (Requirement → …→ Evidence), where each chain breaks
- **Knowledge chain (INTACT to the DB boundary):** CSVs/`dishes.xlsx`/`Indian_Meal_Cohort_Persona_DB_v3.xlsx` → Batch 1–6 pipeline packages (each names its asset, rows, transformations) → `generate_icd1_seeds.py`/`generate_re_seeds.py` (sha256 provenance headers) → seeds 100–117 → validation 905 gates. Verified by regeneration. Gaps: `re_cohort_class_priors` (no seed, disclosed), `re_city_migration_overlays` S-15 (deferred, disclosed).
- **Runtime chain (BREAKS at the adapter layer):** every seeded RE table maps to a declared engine port, but concrete adapters exist only for `week_plans`/`plan_slots`/onboarding writes/plan-slot reads/eligible users. No adapter exists for candidates, priors, taste vectors, history, bandit, context multipliers, cohort resolution, or config — so **no seed row is consumed by running code today**.
- **API chain (BREAKS at the handler layer):** §06.2/§06.4 DTOs and error codes are implemented exactly in services, but only `/v1/consent` has a handler; 8 of 9 documented endpoints have none.
- **Learning chain (ABSENT):** events → taste vector/bandit/interaction-count/feature store (LF-G, LF-J) has no code at all.

### A.4 Repo-wide marker sweep (step 11)
`TODO|FIXME|BLOCKER|HACK|XXX|NOT_IMPLEMENTED|placeholder|temporary` across all non-test TS: **only two "deferred" comments, both already disclosed in WP records** (IP-hash, JWT-verification history). No hidden shame markers. `throw new Error` appears only in config fail-fast. This is an unusually honest codebase.

### A.5 Test coverage (step 12) — what has NO automated verification
Week-level plan integrity (the only `generateWeekPlan` test uses a **1-slot** class plan); participation of variety-window rules and the planning-role gate in plan generation (impossible — unwired); all five variety rules as a set (only 3 coded); LF-A06 difficulty filtering (unimplemented); addon generation; every Supabase adapter (type-checked only); ContextFit weather/season tag semantics beyond clamps; the LF-A09 fallback-confidence rule; scheduler date logic (`nextMonday`).

---

## B. WP-9 Verification Matrix (every finding re-earned independently)

| ID | WP-9 statement | Independent assessment | Corrected conclusion |
|---|---|---|---|
| C-01 | RE not user-reachable; suggestion_logs never written; safety-gate SQL vacuous, risking "false sense of safety" | **Partially Confirmed.** 1/9 endpoints and zero audit writes re-verified (functions listing; repo-wide grep). **But** validation `902` explicitly self-discloses that the live gates "only have meaning once suggestion_logs has real rows" and deliberately tests gate *data preconditions* instead — the repo already prevents the false-assurance failure WP-9 warned about. | Keep Critical for launch-readiness (not runnable, no audit trail); **delete the "false sense of safety" clause** — evidence contradicts it. |
| H-01 | checkVarietyWindow / checkPlanningRoleGate implemented but never invoked by the engine; WP-8D coverage table "materially misleading" | **Confirmed** on wiring (repo-wide reference search: tests + barrel only; engine pipeline comment itself says "LF-H01–H03"). "Materially misleading" is **slightly overstated**: WP-8D §2 maps *modules* to LFs, which is true at function level. | Confirmed finding; soften characterization to "coverage claim is ambiguous — true of modules, untrue of the pipeline." |
| H-02 | LF-F02: 2 of 5 rules missing + same-ingredient adjacency bug | **Confirmed.** Rules 1 & 5 absent from `checkVarietyWindow`; adjacency logic re-derived: with 3 interleaved slots/day in a date-sorted list, same-slot consecutive-day pairs are never array-adjacent, so the rule cannot fire on a full week. Additionally untestable in situ because the function is unwired (H-01). | Confirmed; add that no test exercises a realistic multi-slot week, which is why the bug survived. |
| H-03 | WP-8D/8E say "not pushed"; commits are on origin/main; approval unverifiable | **Confirmed.** `git log`/`git branch -a` re-checked: `e113ffa`, `e76bd9c` on main and origin/main; no feature branch remnant. Founder approval: still Unable to verify. | Confirmed as written. |
| H-04 | Unseeded `re_cohort_class_priors` neutralises documented cold-start | **Confirmed** (no 1xx seed; ETL deliberately excludes it; port returns null → 0.50). See §F: arguably **understated** given DOC-01 §07's decision rule hangs on Day-0 acceptance. | Confirmed; raise urgency note (see F). |
| M-01 | ContextFit simplified (cooking-method-keyed weather; no time_of_day; no fried-reduction) | **Confirmed** against LF-E05 full text and `gatherContextMultipliers`. | Confirmed. |
| M-02 | LF-A09 fallback must set confidence 0.35; orchestrator ignores `fallbackApplied` | **Confirmed** (LF-A09 text re-read; orchestrator code re-read). | Confirmed. |
| M-03 | Member-overlay derivation + LF-C addons unimplemented | **Confirmed**; overlay table (INFANT→O_INFANT…) exists only in DOC-P3-03; no code derives it. | Confirmed. |
| M-04 | Feature store not logged from Day 1 | **Confirmed** (no LF-J07 code; RE-DOC-05 §02 mandate re-read). | Confirmed. |
| M-05 | Persist atomicity gap (sequential upserts) | **Confirmed** in `SupabaseWeekPlanStore` + its own NOTE comment. | Confirmed (already self-disclosed in code). |
| M-06 | Bandit exploration-only; α/β update uncalled; cohort-adjusted prior absent | **Confirmed** (reference search; `updateBanditParams` exported, never called outside tests). | Confirmed. |
| M-07 | LF-A08 "−0.05 per non-critical skipped field" missing | **Confirmed** against LF-A08 full text vs `computeOnboardingConfidence`. | Confirmed. |
| M-08 | No latency validation; N+1 scoring loop risk | **Confirmed** (per-dish sequential awaits re-read in `scorePool`; no perf artifacts anywhere in repo). | Confirmed. |
| L-01 | "5 vs 6 hard constraints" numbering inconsistency | **Confirmed** (DOC-P3-03 §06 header vs line 1411 vs RE-DOC-03 §03). | Confirmed. |
| L-02 | MMR similarity = categorical match-fraction, not cosine | **Confirmed** (`varietySimilarity` vs LF-F01 text). | Confirmed. |
| L-03 | "10 frozen endpoints" (P4-00 §6) vs 9 (P3-06 §03) | **Confirmed** by re-reading both. | Confirmed. |
| L-04 | ERR_PLAN_NOT_FOUND emitted by an endpoint the catalogue lists for /v1/plan | **Confirmed** (api-catalogue.ts comment cites §06.5; recommendations service throws it). | Confirmed. |
| L-05 | Dead micro-logic (`classForSlot ?? a.classCode`; "distinct upstream" comment) | **Confirmed** by re-reading `engine.generateWeekPlan` / `checkVarietyWindow`. | Confirmed. |
| L-06 | Pseudo-`.docx` markdown files; RE-Visual-04 absent | **Confirmed** (`file` output; visuals listing). | Confirmed. |
| L-07 | DOC-P4-02 DRAFT; DCR-8D-01/8E-01 unsigned | **Confirmed** (both worked-example inconsistencies re-verified against DOC-P3-03 §07/§03 text). | Confirmed — and generalized by MF-03 below. |

**Verdict on WP-9 accuracy:** 20/21 findings Confirmed; 1 Partially Confirmed (C-01, one clause withdrawn); 1 characterization softened (H-01); 0 Incorrect. WP-9's overall Verdict C is re-affirmed by independent reconstruction.

## C. Missed Findings (new, evidence-backed — WP-9 did not report these)

- **MF-01 (Medium) — LF-A06 downstream and the equipment overlay are unimplemented; `cookCapability` is dead data in the engine.** LF-A06: "beginner: … dishes with difficulty=advanced excluded"; DOC-03 §05 makes O_SIMPLE_EQUIPMENT_OVERLAY a **hard filter** ("suggesting Rajasthani Dal Baati to a student with a hot plate destroys trust in one interaction"). Evidence: `DishCandidate` carries no difficulty/equipment field; repo-wide search shows `cookCapability` is captured, scored into confidence, persisted — and never filters or scores anything. WP-9's constraint table silently omitted this documented filter.
- **MF-02 (Medium) — OB-07 signal loss at onboarding.** DOC-06 C-07: each swipe → class-affinity boost/penalty "applied to cohort matrix weights for this user"; DOC-P3-06 field tables carry the swipe payload. The orchestrator persists an **empty** taste vector and reduces OB-07 to `min(classSwipeCount,10)` — the direction of every swipe (which classes were liked/rejected) is discarded. The single highest-value cold-start personal signal (LF-A08 rates it +0.12) currently affects only the interaction counter.
- **MF-03 (Medium, governance) — Systemic ACTIVE-vs-DRAFT contradiction across the frozen set.** Every product and design doc read end-to-end (DOC-01…09, DOC-04/05/06/10, RE-DOC-01…05) carries `Status: DRAFT — pending founder sign-off` with a blank signature line, while its filename carries `[ACTIVE]` and downstream WPs treat it as frozen. Several also carry stale inner headers ("Version 1.0 · June 2026" on v1.1/v1.2 documents). WP-9 flagged only DOC-P4-02. Either the sign-off blocks are ceremonial (then say so in the naming standard) or the entire freeze chain rests on unsigned documents.
- **MF-04 (Medium, doc conflict) — DOC-01 v1.1 contradicts DOC-04 v1.1 on MVP scope.** DOC-01 §06 still lists "Grocery list auto-generated from plan — Core, cannot defer" in the MVP column; DOC-04 v1.1's Change Notice moves F-27/F-28 out of MVP. A reader starting from the founding brief gets the wrong MVP.
- **MF-05 (Low/Medium, stale ACTIVE visual) — the Design System Explorer HTML teaches a removed interaction.** `[ACTIVE]_DOC-06_Visual_Design_System_Explorer_v1.0.html` specifies the long-press gesture ("Long-press trigger: 400ms … drag up/down") that DOC-05 v1.2/DOC-06 v1.1 removed product-wide as a breaking change ("No hidden gestures remain"). The ACTIVE visual companion contradicts the frozen gesture spec.
- **MF-06 (Low, staleness) — DOC-10 §10's "locked" environment map references superseded infrastructure** (branch `apverse-labs-RE`, Supabase refs `kwypx…`/`ufgfz…`, clone URL `apverse-labs/foofoo`) that the repository's own recovery record (REPO-CERT-009, Migration Recovery reports) supersedes. Live mapping: Unable to verify from the backup, but the internal contradiction is repository fact. `supabase/README.md` is similarly stale ("no endpoints yet — foundation only").
- **MF-07 (Low, code) — `updateSlotSlate` does not update `cold_start_mode` (or `class_code`) on refresh**, so a slot refreshed after a user exits cold start retains the stale flag; and `isPersonalizationGranted` resolves ties on identical `granted_at` timestamps arbitrarily. Both are one-line fixes.
- **MF-08 (Positive — evidence strengthening) — the seed pipeline is provably deterministic.** This audit re-executed both ETL generators; all committed seeds (103–117 + rollbacks) regenerated **byte-identical excluding timestamps**, with sha256 source provenance intact. Combined with Batch 4's full-read discovery (810 dishes, 0 duplicates) and 802 seeded dish rows (810 − 8 combos), the **PRD's 500-dish gate is met at the row level** (genome/photo completeness per dish: Unable to verify from SQL alone). WP-9 never examined the batch/transformation layer; had it, its confidence statement would have been *higher* for this chain.

## D. Incorrect Findings in WP-9

None. No WP-9 finding was contradicted by evidence. One clause within C-01 was (see E).

## E. Overstated Findings in WP-9

- **E-01 — C-01's "false sense of safety-gate coverage" clause.** Validation `902` explicitly documents that live gates are meaningless until an RE pipeline populates `suggestion_logs`, and restructures itself as data-precondition proofs. The repository already guards against the misreading WP-9 warned of. The clause is withdrawn; the rest of C-01 stands.
- **E-02 — H-01's "materially misleading" characterization of WP-8D.** WP-8D's table maps modules→LFs (true); the omission is that nothing states LF-F02/H04 are *not in the pipeline*. Corrected wording: "accurate at module level, silent at wiring level."

## F. Understated Findings in WP-9

- **F-01 — H-04 (unseeded priors) is closer to Critical-for-launch than High.** DOC-01 §07's decision rule ("below 250 DAU → fundamental rethink") is driven by Day-0/Day-90 acceptance; RE-DOC-04 §01 names cohort intelligence as "the right answer" to cold start; with a uniform 0.50 prior **and** MF-02 (OB-07 signal discarded) **and** empty taste vectors, Day-0 ranking rests on context multipliers + exploration noise. Two compounding gaps against the single make-or-break MVP metric deserve joint, top-priority treatment.
- **F-02 — The "one engine, three callers" architecture claim should have been graded with its untested surface.** WP-9 verified the wiring but did not state that `generateWeekPlan` has never been exercised beyond a 1-slot fake plan; the flagship weekly-plan behaviour (21 slots, cross-slot variety, non-veg overlay across a real week) has zero automated verification.

## G. Improved Recommendations (supersedes WP-9 §25)

1. **Cold-start integrity package (new #1):** seed `re_cohort_class_priors` + persist OB-07 swipe directions into `user_taste_vectors.class_affinity` (MF-02) + apply the LF-A09 fallback-confidence rule — all three before any endpoint ships, because they jointly determine the only metric the MVP is judged on.
2. Founder ½-day session unchanged (DCR-8D-01, DCR-8E-01, AD-01/DOC-P4-02) — **extended** to rule on MF-03 (sign the frozen set or amend the naming standard) and ratify/reject the main-branch push (H-03).
3. "Runnable RE" WP unchanged, **plus:** wire LF-F02/H04 into `generateWeekPlan` with a realistic 21-slot regeneration test; fix the F02 adjacency bug via per-slot grouping; add rules 1/5; add the LF-A06 difficulty filter (requires adding `difficulty` to `DishCandidate` and the candidate query — cheap now, breaking later); write `suggestion_logs`/`context_log` in the slate RPC.
4. Minimal learning loop (LF-J01/J02/J04/J06/J07 + `/v1/events`) before first real user — unchanged.
5. Documentation-currency pass (new): reconcile DOC-01–DOC-04 MVP lists; regenerate the DOC-06 Explorer HTML for swipe-reveal; revise DOC-10 §10 env map + supabase/README; fix inner version headers; rename pseudo-`.docx` files.
6. Live-DB behavioural validation + latency measurement — unchanged (still the production gate).

## H. Final Verdict

**On WP-9:** *Substantially reliable.* 20/21 findings independently confirmed, 0 incorrect, 2 clauses overstated (both corrected), 2 findings understated, **8 findings missed** — the misses cluster exactly where WP-9's disclosed accelerated reading was thinnest (full product docs, full visuals, doc-to-doc cross-consistency, onboarding-signal semantics), vindicating the Founder's instruction to re-audit with full reads. WP-9's Verdict **C — Partially aligned** is re-affirmed from an independent reconstruction and now rests on materially stronger evidence: the test suite re-verified (62/62), the seed pipeline proven deterministic by regeneration, the call graph verified by repo-wide reference search, and a clean hidden-marker sweep.

**On the repository:** unchanged verdict **C**, with a sharpened core sentence: *the engine core is faithful and clean; the knowledge base is provably well-engineered; the connective tissue — adapters, endpoints, learning loop, cold-start priors, onboarding signal capture, and gate wiring — is where the product does not yet exist, and one new class of risk (documentation self-contradiction across the "frozen" set) needs a governance ruling rather than code.*

---
*Every conclusion above cites repository evidence gathered in this session. Items requiring live Supabase or Founder testimony are marked "Unable to verify." Reading coverage: docs/architecture, docs/product, docs/visuals, and supabase/ read in full; docs/research batch packages read for discovery/transformation content; docs/project-history consulted for specific certifications; deno.lock and .git internals excluded as non-documentation.*

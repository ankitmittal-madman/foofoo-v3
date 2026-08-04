# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Ghar RE v1.0 — Status and Roadmap

**Status:** ACTIVE — ground-truth audit, verified directly against the repository at commit `db22b6b` (branch `main`).
**Version:** v1.0
**Date:** 2026-07-29
**Placement:** docs/architecture/
**Supersedes:** None — first as-built status document for the Python `ghar_re_core`/`ghar_re_service` RE.
**Dependencies:** RE-DOC-10 (Production Implementation Plan), RE-DOC-11 (Extensibility Review), `contracts/ghar-re-v1.schema.json`, `KNOWLEDGE.html`.

---

## Executive Summary

This document states, for every claim, what was **directly verified by inspection or execution** — a file read, a test run, a live query — as distinct from what a prior document, session summary, or `KNOWLEDGE.html` merely asserts. Where a document's claim and the repository's actual state disagreed, both are stated explicitly rather than silently reconciled. No new engineering was performed to produce this document.

**Headline finding, not previously documented anywhere:** this repository contains **two independent recommendation engines**. A legacy TypeScript RE (`supabase/functions/_shared/services/re/*.ts`, backed by the `re_engine`/`re_meal_classes`/`re_cohort_class_priors` schema and the entire FD-01–FD-18 decision history in the Founder Decision Register) is **not imported by any live edge function** — it is reachable only from its own three test files. The live, deployed recommendation path is the Python `ghar_re_core`/`ghar_re_service` pair (RE-DOC-10/11), which the legacy engine's own migration 034 explicitly calls "the OLD persona/cohort/weight-ladder RE" and states is "retired." No Founder Decision Register entry records this retirement as a decision — it is a fact about which code path executes, not a ratified statement anywhere in governance.

---

## 1. Verified — complete, with evidence

| Claim | Verdict | Evidence |
|---|---|---|
| `ghar_re_core` is an installable package; `ghar_re_service` imports it, never reimplements | **TRUE** | `pyproject.toml` declares `ghar-re-core` as a real `setuptools` package, `pip show ghar-re-core` resolves to `/usr/local/lib/python3.11/dist-packages`. `ghar_re_service/ghar_re_service/{engine,modules,providers}.py` import `from ghar_re_core import pipeline, scoring, config, catalogue` directly. `ghar_re_service/ghar_re_service/` contains no `scoring.py`/`derivation.py`/`pairing.py` of its own — the only files are `auth.py, engine.py, lifecycle.py, main.py, modules.py, providers.py, ratelimit.py, schemas.py, version.py`. |
| RE verifies HMAC signature on `/v1/recommendations`, rejects unsigned/tampered/stale | **TRUE** | `ghar_re_service/ghar_re_service/main.py` registers `verify_signature` as ASGI middleware over `SIGNED_PATHS = {"/v1/recommendations"}`, returning 401 with reasons `missing_signature`/`malformed_signature`/`stale_signature`/`invalid_signature` before any body parsing. `ghar_re_service/tests/test_auth.py` exercises all four rejection paths plus a valid-signature success case through `TestClient`. |
| Real household/answer/context/event tables exist in `public`, not just the golden-sample `ghar_re` schema | **TRUE, with one correction to the brief's own premise** | No `public.households` table exists, by design: `public.profiles` (migration `005_profiles.sql`) is the household root, and migration `038_household_answers_context_and_events.sql`'s own header states this explicitly ("A separate `households` table is therefore NOT created here"). What exists: `public.profiles` (005), `public.household_members` (006, altered by `033` for the conditions vocabulary and by `038` to add `age`), `public.household_answers` (038, new), `public.household_context` (038, new), `public.recommendation_events` (038, new), `public.feedback_events` (038, new). Separately, `ghar_re.households` (migration `035`) does exist and is exactly what its own name implies: the golden-sample offline schema, not live application data — confirmed by `034`'s header ("this is a NEW, isolated schema `ghar_re` and does NOT touch public.dishes / re_engine.* or the real 810-dish catalogue"). |
| `compose.ts` reads real tables, not `fixtures.py` | **TRUE** | `supabase/functions/recommendations/compose.ts`'s `loadHouseholdRaw` issues three concurrent Supabase reads against `profiles`, `household_answers`, `household_members`. It has no import of, or reference to, `ghar_re_core.fixtures` — that module is Python and is not reachable from Deno code at all; the two languages do not share a runtime. The one fallback path (`NEW_HOUSEHOLD`) fires only when a caller has no `profiles` row — a genuinely new, not-yet-onboarded user — and is a hardcoded neutral default, not a read from the golden sample. |
| `events.ts` writes real rows, not log-only | **TRUE, with one documented exception** | `recordRecommendationEvent` inserts into `public.recommendation_events` with `data_source: "real"` on every call **except** when the household is `stubbed` (no `profiles` row exists), in which case there is no valid `profile_id` to satisfy the table's `NOT NULL` foreign key, and the function correctly skips the write — the structured log line is the only record for that one case, and this is stated in the function's own comment, not silent. |
| Full test suite pass/fail counts | **Python: 77/77 passing, executed this session.** **Deno: could not be executed — see §3.** | `python3 -m pytest ghar_re_core/tests/ ghar_re_service/tests/ -q` → `77 passed, 1 warning`. Deno: `deno test --allow-env --allow-read _tests/` fails immediately with `JSR package manifest for '@std/assert' failed to load ... 403 Forbidden` — the sandbox's outbound proxy blocks `jsr.io` (confirmed separately: `curl` to `registry.npmjs.org` returns `200`, `curl` to `jsr.io` returns `403`). A static count found **81 declared `Deno.test()` cases across 6 files** (`candidate_repository.test.ts` 9, `consent.test.ts` 16, `foundation.test.ts` 8, `re_core.test.ts` 28, `re_integration.test.ts` 10, `recommendations.test.ts` 10) — this is a count of declarations, not a confirmation that they pass. |
| `contracts/ghar-re-v1.schema.json` is the single file both sides reference | **TRUE** | `find . -name "ghar-re-v1.schema.json" -not -path "./.git/*"` returns exactly one path. `ghar_re_service/ghar_re_service/schemas.py` and `supabase/functions/recommendations/contract.ts` both reference that exact path (the latter via a direct `import ... with { type: "json" }`). `backend-ci.yml`'s `contract-check` job asserts this count in CI on every push touching `contracts/**`. |
| `fly.toml` matches what was last committed | **TRUE** | `git diff origin/main -- ghar_re_service/fly.toml` returns zero lines. Contains `GHAR_RE_RATE_LIMIT_PER_MINUTE = "300"`, `force_https = true`, and an `[http_service.concurrency]` block with `soft_limit = 200` / `hard_limit = 250`. |
| CI workflows exist and actually gate ruff/mypy | **TRUE** | `.github/workflows/re-ci.yml`'s `verify` job runs `python3 -m ruff check`, `python3 -m ruff format --check`, and `python3 -m mypy` as separate steps before pytest. Re-executed live this session: `ruff check` → "All checks passed!"; `mypy` → "Success: no issues found in 25 source files". `backend-ci.yml` separately gates `deno fmt --check`, `deno lint`, `deno check`, and `deno test` for the Edge Function side. |
| Catalogue is still the 39-dish golden sample; no real catalogue introduced | **TRUE** | `ghar_re_core.fixtures.DISHES` has 39 entries, `HOUSEHOLDS` has 7. The baked bundle (`ghar_re_service/data/bundle/catalogue.json`) also has exactly 39. A repo-wide grep of `ghar_re_core/*.py` and `ghar_re_service/ghar_re_service/*.py` for any database driver (`psycopg`, `asyncpg`, `sqlalchemy`) or a reference to `public.dishes` returns nothing — the RE has zero database code, consistent with RE-DOC-10 §1's frozen boundary. |

## 2. Cannot be verified from the repository alone

Per the audit's own scope: this covers repository state only. None of the following was checked, and none is claimed:

- Whether the Fly.io app exists, is running, or is reachable. **Nothing has been deployed** — confirmed by `ghar_re_service/README.md`'s own "PREPARED, NOT DEPLOYED" banner and by the absence of any Fly credentials or `flyctl` binary in this environment (attempts to install it are blocked: the sandbox proxy returns 403 on `fly.io`).
- Whether the deployed `GHAR_RE_SERVICE_SECRET` (if any exists) matches the value Supabase holds.
- Live traffic volume, `rate_limited_total` in production, or whether `Fly-Client-IP` is actually populated by Fly's proxy as documented.
- Real Deno test outcomes (§1, `jsr.io` blocked) — the 81-test count is structural, not a pass confirmation.

## 3. Discrepancies found — reported, not silently fixed

Per the audit's stop condition, these are flagged for a separate decision, not corrected here.

1. **A stale comment in `supabase/functions/recommendations/handler.ts` (lines 91–94) claims the live household table doesn't exist yet.** It reads: `// Fetch household + context (STUB until the live table exists — see compose.ts)` and `// TODO(founder-decision): once the live households table exists, enforce ownership here...`. Both `compose.ts`'s own header ("wired to live tables in Phase C.5") and migration `038` directly contradict this — the tables have existed since Phase C.5. The `TODO` is therefore not blocked on a missing table; it is blocked on nobody having wired the call yet.

2. **`requireOwnership` exists, is tested, and is used elsewhere in this exact codebase — but is not called in the recommendations handler.** `supabase/functions/_shared/auth/authenticate.ts` exports it; `supabase/functions/consent/handler.ts` calls it; `supabase/functions/_tests/consent.test.ts` tests it directly. The recommendations handler accepts an attacker-supplied `body.household_id` (line 76: `const householdId = (typeof body.household_id === "string" ? body.household_id : null) ?? claims.userId ?? null;`) and passes it straight to `loadHouseholdRaw` with **no check that the authenticated caller owns that household**. Any authenticated user can currently request — and, via `recordRecommendationEvent`, cause a write of — another household's recommendation data by supplying its `profile_id` in the request body. This is a live authorization gap, not a documentation gap; the fix (`requireOwnership(claims, householdId)` before the `loadHousehold` call) is a one-line change using an already-tested function, but it is a security-relevant code change and is explicitly out of scope for this audit per its stop condition.

3. **`public.household_context` is provisioned but entirely unwired.** The table exists (migration 038), has RLS, and has one read function (`compose.ts`'s `loadLatestContext`) — but that function is never called from `handler.ts`, and no code path anywhere writes a row to it. Context is currently always either the caller-supplied `context` object in the request body, or a hardcoded `DEFAULT_CONTEXT` (dinner / monsoon / Thursday / raining). This is not a bug in what's shipped — nothing claims otherwise — but it means "the household's most recent stored context" described in migration 038's own comment is aspirational, not a working feature yet.

4. **The Phase C fallback plate is a single hardcoded dish, not the "cached-per-zone default plate set" RE-DOC-10 §11 specifies.** `supabase/functions/recommendations/fallback.ts` returns one pan-India comfort plate (Moong Dal Khichdi) regardless of the caller's region, on every RE failure. This is disclosed in the file's own comment ("⚠️ STUB... future work"), so it is not a silent gap, but it is a real divergence from what §11 of the frozen implementation plan describes.

5. **Two parallel recommendation engines exist in one repository, and no governance document records the second one's retirement as a decision.** See the Executive Summary. The Founder Decision Register's entire RE section (§9, RE-01 through RE-06) and most of §7's FD-01–FD-18 describe and govern the TypeScript engine and its `re_engine`/`re_meal_classes`/`re_cohort_class_priors` schema. That engine is not on the live request path (§ confirmed above). RE-DOC-10/11 — which govern the engine that *is* live — cite none of FD-01–FD-18 and are not cited by the Decision Register. Whether the legacy engine's code, its dedicated test files, and its schema should be formally retired, archived, or kept as a reference is a decision this audit surfaces but does not make.

## 4. Parked items

### 4.1 The G6 protein-balance pairing gap

**File:** `ghar_re_core/pairing.py`, function `compat(d, l)`, lines 82–91.

The function computes a soft pairing-compatibility score. Its G6 term ("protein-veg balance: pulse/protein liquid + veg dry, or vice versa") declares `protein_cat = {"dal_lentil", "kebab", "egg_dish", "curry"}` (line 91) but the actual test on the next line only checks membership in `{"dal_lentil"}` (line 92, `l_protein = bool(set(l.dish_category) & {"dal_lentil"}) or l.diet in ("non_veg", "egg")`). A liquid dish whose category is `kebab`, `egg_dish`, or `curry` therefore does not earn the `b_protein` bonus unless its `diet` happens to also be `non_veg`/`egg` — narrower than the four-category rule the code itself names.

The gap is documented in the code (a `noqa: F841` comment explains it was surfaced by `ruff`, not by design intent) and is deliberately **not fixed**, because widening the check to `set(l.dish_category) & protein_cat` changes scoring output for affected plates — a recommendation-quality decision requiring Founder review, not a lint cleanup. The golden-master regression test (`ghar_re_core/tests/test_golden_master.py`) will fail the moment this line changes, which is the intended trip-wire. This remains an explicit TODO, unchanged since Phase C.5.

### 4.2 Whether onboarding should collect real member ages

Migration `038` added `public.household_members.age` as a **nullable** column, deliberately: the current onboarding flow does not collect it, and the migration's own comment states plainly that backfilling a fabricated number into existing rows "would be inventing user data." `compose.ts`'s `toMemberAge` supplies a documented role-derived default age (`weaning: 1, toddler: 3, child: 9, teen: 15, senior: 70, adult: 32`) purely to satisfy `contracts/ghar-re-v1.schema.json`'s `MemberAge.age` being a required field — the actual safety-critical filters (weaning floor, senior ceiling) key off the household member's `role`/`conditions`, which onboarding does collect, not off this placeholder number.

Whether the onboarding flow should be extended to collect real ages (making the RE's age-based filters more precise than role-derived defaults currently allow) is an open product question. No canonical document commits to an answer either way — this is stated as genuinely undecided, not inferred.

## 5. What remains before public launch

Grounded specifically in the canonical documents' own safety-gate and cutover language — cited, not paraphrased into a new roadmap:

- **Allergen hidden-derivative table.** `docs/architecture/ghar-re/ghar_re_v1_0_core_spine_FROZEN.md` §A3 states verbatim: *"this is the BASIC pass on explicit ingredient flags only. The hidden-derivative layer (e.g. hing -> wheat/gluten) is the deferred `allergen_hidden_derivative` table and MUST be folded in before public launch. Until then allergen filtering is not safe-complete."* The same document's §D ("Safety — must complete BEFORE public launch") and its SP-F13 tracking row (status: `OPEN — PRE-LAUNCH`) repeat this. The table itself exists at the schema level (`ghar_re.allergen_hidden_derivatives`, migration `036`) but is explicitly inert (`is_active boolean NOT NULL DEFAULT false`) pending population and wiring into filter A3 — confirmed directly in `036`'s own header comment.
- **Jain filter completeness.** The Core Spine's §A2 defines the Jain hard filter as `pass_jain(x,H) = (not H.is_jain) OR (x.jain_compatible == 'Y')`, dependent entirely on `dish_compatible` being correctly derived for every catalogue dish. This is correct today against the 39-dish golden sample (the filter logic itself is implemented and covered by `ghar_re_core/tests/`), but its completeness against the real 810-dish catalogue is a data-population question, not a code question, and is untested until that catalogue lands (see next item).
- **The real-catalogue cutover (RE-DOC-10 Phase G).** RE-DOC-10 §2 names this explicitly as a phase "separate from this document's scope." The Core Spine specifies exactly what the cutover must supply: (a) the 810-dish catalogue itself (§1, `IDF(i) = ln((N+1)/(df_i+1)) + 1` with `N = 810`, and §A "the cheap first pass that shrinks 810 to the eligible pool"); (b) graded per-dish **signature scores**, `sig(x) in [0,1]` (§B4), currently only proxy-derivable from `tier`/`is_user_facing` per the doc's own note, with real authoring deferred to "the parameter pass (Step 5 / Knowledge Base)"; (c) the full **region × slot (× season) `PRIOR` table** (§B8), stated as "shape here; full population = Step 5" with only illustrative seed examples currently authored; (d) **`dish_macro` nutrition data** (protein/fibre/fat/carbs/sugar/sodium), tracked as SP-F11, status `OPEN` in the same document's deferred-work table. None of (a)–(d) has landed — the RE runs exclusively against the 39-dish golden sample today (§1 above).

## 6. What is genuinely undecided — not converted into a roadmap

Per this document's own instruction against inventing sequencing that no canonical source commits to:

- **v2 personalization timing.** RE-DOC-11 §7/§8 defines the `ScoringModule` protocol precisely so a learned personalization module can slot in later "with zero changes to the composition loop," but no document — RE-DOC-10, RE-DOC-11, the Core Spine, or the Founder Decision Register — states *when* v2 personalization begins. Stated as open, not scheduled.
- **Whether the legacy TypeScript RE and its schema (`re_engine.*`, `re_meal_classes`, `re_cohort_class_priors`) should be formally retired, archived, or kept.** See §3 item 5. This audit surfaces the fact; no document decides its disposition.
- **The Supabase→Fly reachability decision's operational consequences at scale.** The public-ingress + HMAC + rate-limit design (this repo's most recent commit, `db22b6b`) is a settled architectural decision, but its concrete parameters (the 300/min default, `Fly-Client-IP` trust) are explicitly marked in `ghar_re_service/README.md` as unverified against real traffic — not a timeline question, a measurement one, deferred until a real deploy exists.

## Critical Self-Review

Every "TRUE" verdict in §1 is backed by a command actually run or a file actually read during this session, cited by path, migration number, or test name — never by restating a prior session's summary as fact. The Deno test count in §1 is explicitly labeled as a declaration count, not a pass confirmation, because the actual test run failed on a network block outside this session's control; conflating "81 tests exist" with "81 tests pass" would have been exactly the kind of unearned claim this document exists to avoid. The two-engines finding (Executive Summary, §3 item 5) was not anticipated by the audit brief — it emerged from checking whether the Founder Decision Register's RE-related content (FD-01–18, RE-01–06, all describing `_shared/services/re/`) matches the code actually running on the recommendations path, and it does not. This is reported as a fact requiring a decision, not resolved unilaterally.

## Versioning & Placement

v1.0, filed under `docs/architecture/`, adjacent to RE-DOC-10/11 per the existing numbering convention for this document series. First version; nothing superseded.

Founder sign-off: _______________________ Date: ___________

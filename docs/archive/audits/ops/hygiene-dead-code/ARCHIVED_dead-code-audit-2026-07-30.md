# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Dead Code Audit — 2026-07-30

REPORT ONLY. Per `.claude/skills/hygiene-dead-code/SKILL.md` Step 3, nothing has been
removed or modified. This report is Step 3 of that skill's methodology, adapted from its
TS/JS-only Step 1 greps to cover the repo's actual polyglot surface: TypeScript in
`mobile/` and `supabase/functions/`, Python in `ghar_re_core/` and `ghar_re_service/`.

Branch: `claude/foofoo-skills-dotfiles-e93096` (commit `ee93914` at time of audit).

## Methodology note (read before the findings table)

For "unused exports," a plain textual name-count was used per candidate: 0 other
occurrences anywhere in the tree = genuinely dead; occurrences only within the declaring
file itself (e.g. a `Props` type used solely to type its own component's signature) were
**not** flagged — that is a real, if narrowly-scoped, consumer, not dead code. 351 TS/TSX
exports and 195 Python top-level `def`/`class` names were checked this way; pytest test
functions (`test_*`, fixtures) were excluded from the Python pass since they are invoked
by the test runner, not by name reference, and Expo-router files under `mobile/app/` were
excluded from "orphaned file" checks since file-based routing has no explicit importer by
design.

## Summary

| Category | Found | Safe to remove | Needs review |
|---|---|---|---|
| Unused exports/functions/classes | 8 | 5 | 3 |
| Orphaned files | 3 (+1 already tracked, not counted as new) | 0 | 3 |
| Stray console.*/print debug calls | 0 | 0 | 0 |
| Commented-out code blocks (5+ lines) | 0 | 0 | 0 |
| Stale TODO/FIXME (30+ days, or since 2026-07-13 repo inception) | 0 | 0 | 0 |

## Findings

| File | Line | Type | Content preview | Safe to remove | Reason |
|---|---|---|---|---|---|
| `mobile/src/theme/theme.ts` | 62 | Unused export (const) | `export const BottomTabInset = Platform.select({ ios: 50, android: 80 }) ?? 0;` | Yes | Zero references anywhere in the repo, including within its own file. No screen or component reads it. |
| `mobile/src/theme/theme.ts` | 63 | Unused export (const) | `export const MaxContentWidth = 800;` | Yes | Zero references anywhere in the repo, including within its own file. |
| `supabase/functions/_shared/config/env.ts` | 34 | Unused export (type) | `export type EnvVarName = keyof typeof ENV_VARS;` | Yes | Zero references anywhere; `config.ts`'s typed loader (the sole intended consumer per the file's own header) does not import it. Pure leftover type alias. |
| `supabase/functions/recommendations/metrics.ts` | 72 | Unused export (function) | `export function resetMetricsForTests(): void {` | Yes | Explicitly test-only per its own docstring, but no test file (`_tests/recommendations.test.ts` or otherwise) calls it. Genuinely unused test helper. |
| `ghar_re_core/seedgen.py` | 57 | Unused function | `def combo_uuid(name):` | Yes | Companion to `dish_uuid`/`hh_uuid` in the same file; those two are used by the generator, `combo_uuid` is called nowhere — zero references anywhere, including within its own file. |
| `supabase/functions/recommendations/metrics.ts` | 60 | Unused export (function) | `export function snapshotMetrics(): Counters {` | No | Zero callers anywhere, but the file's own header states this whole module is a deliberately minimal placeholder "meant to be replaced wholesale once Phase F picks a real deploy target with real monitoring" — `snapshotMetrics` reads as the intended external accessor for that future monitoring surface, not simple leftover code. Confirm with the Founder whether Phase F still needs it before deleting. |
| `supabase/functions/recommendations/compose.ts` | 281 | Unused export (function) | `export async function loadLatestContext(ctx, profileId)` | No | Implements "load the household's most recent stored context" exactly as its docstring describes, but `recommendations/handler.ts` never calls it — the handler goes straight to `DEFAULT_CONTEXT` merged with any request-body override, silently skipping the stored-context lookup. This looks like a built-but-not-wired functional gap (same shape as the already-known `orchestrator.ts` finding below), not dead code — deleting it would remove a real capability that may just need to be wired in, so this needs a product/engineering decision, not a delete. |
| `supabase/functions/_shared/services/adapters/supabase-stores.ts` (`SupabaseEligibleUsersStore`, line 256) + `supabase/functions/_shared/services/scheduler/nightly-plan.ts` (`NightlyPlanScheduler`) | 256 / — | Unused export (class) | `export class SupabaseEligibleUsersStore implements EligibleUsersStore {` | No | Fully implemented nightly-plan CRON path (LF-L01, DOC-P3-03 §14) exercised only by `_tests/re_integration.test.ts` — no deployed Edge Function or scheduled job actually invokes `NightlyPlanScheduler`/`SupabaseEligibleUsersStore` in production. Same "fully built, never wired" shape as the already-flagged `OnboardingOrchestrator` (see below); flagging for the same Founder/engineering decision rather than deletion. |

### Orphaned files

| File(s) | Safe to remove | Reason |
|---|---|---|
| `mobile/src/components/ThemedText.tsx`, `mobile/src/components/ThemedView.tsx`, `mobile/src/hooks/useTheme.ts` | No | An entire parallel theming system, imported only by each other — no screen or component under `mobile/app/` or `mobile/src/onboarding/` uses them. Every live screen instead uses `mobile/src/theme/index.tsx`'s `useTheme()`. The code's own comments confirm this directly: `mobile/src/hooks/useTheme.ts`'s header says "Used by the older ThemedText/ThemedView components," and `mobile/src/theme/index.tsx`'s header calls out "not the older light/dark `@/hooks/useTheme`." This is a two-competing-implementations case (old theming vs. current `@/theme`) per the skill's own Step 2 guidance — needs a human decision on whether the old trio is truly superseded-and-removable or partially salvageable, not an automatic delete. |
| `supabase/functions/_shared/services/onboarding/orchestrator.ts` | N/A — already tracked | Already identified in `docs/archive/audits/ops/audit-edge-functions/ARCHIVED_edge-function-audit.md` (Finding 1) as a fully-built `OnboardingOrchestrator` never wired to a deployed Edge Function. Re-confirmed present and still unwired during this pass; not re-flagged as a fresh finding, per instructions — see that report for the existing NEEDS_REVIEW writeup. |

## Categories checked clean

- **Stray console.*/print debug calls**: full grep across `mobile/`, `supabase/`, `ops/`, `ghar_re_core/`, `ghar_re_service/` for `console.(log|warn|error|debug|info)` (`.ts/.tsx/.js/.mjs`) and `print(` (`.py`), excluding the sanctioned loggers (`supabase/functions/_shared/logging/logger.ts`, `mobile/src/lib/logger.ts`, `ghar_re_service/ghar_re_service/lifecycle.py`'s `LOG`, `ghar_re_core/decision_log.py`) and the already-accepted CLI exceptions (`ops/scripts/export-txn-logs.mjs`, `ghar_re_service/ghar_re_service/scripts/export_bundle.py`, `scripts/build_catalogue.py`, `scripts/golden_master_real_catalogue_report.py`, `ghar_re_core/seedgen.py`'s `main()`, `ghar_re_core/pipeline.py`'s `__main__` demo block). Zero unexplained hits — this session's earlier logging-infrastructure work holds.
- **Commented-out code blocks**: scanned for 5+ consecutive comment lines containing code-like syntax (`;{}()=`) in both `//`-style and `#`-style comments. One candidate surfaced in `ghar_re_core/knowledge.py` (lines 59–69) but on inspection is a long prose explanation of a data-transcription decision (contains `->` and parentheses in normal sentences), not commented-out code — dismissed as a false positive. No genuine commented-out blocks found in either language.
- **Stale TODO/FIXME**: only one `TODO` exists in the entire polyglot scan — `supabase/functions/_shared/config/config.ts:68` (`// staging enforcement can tighten once secrets are wired in Phase F (deployment). [TODO Phase F]`), introduced 2026-07-28 per `git log -S`, i.e. 3 days before this audit against a repo history that only starts 2026-07-13. Not stale by any reasonable reading of "30+ days" against this short history.

## Next step

This report requires explicit user confirmation before Step 4 (applying removals) per the
skill's mandatory gate — no items have been removed. The 5 "safe to remove" items above are
what would be proposed next; the "needs review" items each require their own explicit
decision and are not proposed for automatic deletion under any confirmation.


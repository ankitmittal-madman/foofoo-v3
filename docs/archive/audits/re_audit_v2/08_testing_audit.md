STATUS: ARCHIVED
Reason: Superseded by docs/active/ (2026-08-04 documentation restructure). This audit remains the evidentiary source for docs/active/CURRENT_STATUS.md, OPEN_ITEMS.md, ROADMAP.md, and LAUNCH_BLOCKERS.md.

# Testing Audit (fresh, 2026-08-04) — all suites actually executed this session, not assumed

| Layer | Test files | Executed result |
|---|---|---|
| `ghar_re_core` (Python unit/golden-master) | 14 files | **111 passed** |
| `ghar_re_service` (Python unit/integration) | 6 files | **69 passed** |
| `ops/quality/suites` (contract/black-box/security/planning) | 4 files | **501 passed, 26 skipped** (skips are gated on DB/browser env vars not set here, honestly recorded per the suite's own policy, not hidden) |
| `supabase/functions/_tests` (Deno) | 6 files, 74 cases | **74 passed** (Deno v2.9.4 confirmed installed, tests actually run) |
| Mobile (`mobile/`) | **0 files** | No jest config, no `*.test.ts(x)` anywhere, no test script in `package.json` |
| UI/E2E (`ops/quality/ui/*.mjs`, Playwright) | 3 scripts | Inventoried only — gated on `GHAR_WEB_URL`/`expo start --web`, not runnable in this environment |

**Total executed and passing this session: 254 backend/engine tests (111+69+74) + 501 quality-gate
tests = 755 passing, 0 failing, 26 honestly-skipped.**

## Coverage by the 8 journeys audited in `06_e2e_workflow_audit.md`

| Journey | Backend/engine coverage | Mobile UI coverage |
|---|---|---|
| Signup/login | None found | Zero |
| Onboarding | Strong (32 Deno tests + quality-gate suite) | Zero |
| Recommendation generation | Strong (18 Deno + core/service/golden-master + 15-persona black-box suite) | Zero |
| Explanation UI | Contract-shape only | Zero — feature doesn't exist |
| Feedback capture | Strong (12 Deno tests) | Zero — and the 2 live UI call sites are themselves untested |
| History/past plans | N/A | Zero — feature doesn't exist |
| Profile editing | N/A | Zero — feature doesn't exist |
| Cold-start/calibration | `test_calibration.py` | Zero |

## Single biggest gap
**The entire mobile app has zero automated test coverage of any kind.** Every other layer
(Edge Functions, RE core, RE service, cross-cutting quality gate) is well-tested and currently
100% green. This asymmetry means a mobile-side regression (e.g. a broken navigation route, a
crash on a specific screen) has no automated safety net today.
</content>

# Logging Infrastructure — Install (Mixed Mode) — 2026-07-30

Ran against an existing partial install: this repo already had a sanctioned structured logger
for the edge-function layer (`supabase/functions/_shared/logging/logger.ts`) and a structured
JSON logger for the Python service layer (`ghar_re_service/ghar_re_service/lifecycle.py`,
`log_event()`). Neither was replaced or duplicated. The genuine gaps (mobile client logger,
change log, transaction export, user journey logger, RE decision logger) were scaffolded.

## Components scaffolded/present

| Component | Status | Location |
|---|---|---|
| System Logger (edge functions) | Already present, kept authoritative | `supabase/functions/_shared/logging/logger.ts` |
| System Logger (Python service) | Already present, kept authoritative | `ghar_re_service/ghar_re_service/lifecycle.py` (`_make_logger`/`log_event`) |
| Lightweight client logger (mobile) | Scaffolded | `mobile/src/lib/logger.ts` |
| User Journey Logger | Scaffolded + wired into 3 handlers | `supabase/functions/_shared/logging/userJourney.ts` |
| Decision Logger (RE) | Scaffolded + wired into `assemble_7` | `ghar_re_core/decision_log.py` |
| Transaction export script | Scaffolded | `ops/scripts/export-txn-logs.mjs` |
| Change log | Scaffolded | `CHANGELOG.md` |
| Output dirs for export script | Created (empty, `.gitkeep`) | `ops/logs/session-log/users/`, `ops/logs/session-log/system/` |

## Compliance gaps

| File | Line | Issue | Suggested fix |
|---|---|---|---|
| `mobile/src/auth/supabaseClient.ts` | 11 (pre-fix) | Raw `console.warn` for missing env vars | Fixed this session — now calls `logger.warn(...)` from the new `mobile/src/lib/logger.ts` |
| `ops/scripts/export-txn-logs.mjs` | multiple | Uses `console.log`/`console.error` directly | Accepted exception — a standalone CLI script, same convention as the existing `ghar_re_service/ghar_re_service/scripts/export_bundle.py`'s `print()`-based CLI output; not product/request-path code, so the "never call console.* directly" rule (which targets app code funneled through a structured sink) does not apply here. |

Full-repo grep after the fix (`console.(log|warn|error)` in `*.ts/*.tsx/*.js/*.jsx`, excluding
`node_modules`, the logger files themselves, and `userJourney`): **zero remaining hits.**
`*.mjs` files are excluded from that grep's include-list by the skill's own Step 7 pattern; the
one hit found by extending the check manually (`ops/scripts/export-txn-logs.mjs`) is the accepted CLI
exception above.

## Change log status

Last updated: 2026-07-30 (created this session) | Recent commits without entry: 0 (the two most
recent commits — `dd2b824`, `c7904bb` — are referenced in the new `[Unreleased]` entry as prior
context; this session's own changes are recorded in the same entry).

## RE decision logger — design note (flagged per skill Step 5 for a sanity check)

**Decision point chosen:** `ghar_re_core/pairing.py`'s `assemble_7()` — the single function that
turns every scored candidate plate into the final 7-plate dish pool actually served for one
household + context. `pipeline.recommend()` calls it exactly once per request and returns its
result as-is, so it is the concrete "class plan -> dish pool" decision named in this repo's
Repository Philosophy.

**What gets logged:** the served plates (rank, label, score), the top 5 highest-scoring
candidates that did NOT make it in — each tagged with the real reason it lost (no-duplicate hero
guard, discovery-dial cap, or simply scored lower) — and a one-line plain-English summary
naming the top choice.

**Safety constraints honored:**
- Uses Python's stdlib `logging` only (`logging.getLogger("ghar_re_core.decision")`), matching
  `lifecycle.py`'s existing convention; no new dependency.
- `ghar_re_core` stays a pure domain package — the new module attaches no handlers itself; it is
  inert until a host process (e.g. `ghar_re_service`) configures one.
- Zero scoring/ranking/selection logic changed. The only functional edit is one new optional
  keyword argument (`household_label=None`) on `assemble_7`, purely so the log line can name the
  household; existing positional callers are unaffected, and the sole real caller
  (`pipeline.recommend`) was updated to pass it through.
- Verified against `ghar_re_core/tests/`: **19/19 tests passed**, including
  `test_golden_master.py`, both before and after the change — confirming the logging addition
  changed no scored/ranked output.

## Test results (`ghar_re_core`)

```
$ python3 -m pytest ghar_re_core/tests/ -q
...................                                                      [100%]
19 passed in 0.14s
```

(Environment note: `pyyaml` and `pytest` were not present in the system Python 3.11 interpreter
that `ghar_re_core` imports against and had to be installed this session — `ghar_re_service`'s own
`pyproject.toml` lists these as real dependencies, so this is a local-environment gap, not a
project gap.)

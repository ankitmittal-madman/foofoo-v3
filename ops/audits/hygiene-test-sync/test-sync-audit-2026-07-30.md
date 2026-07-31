# Test-App Sync Audit — 2026-07-30

## Outcome: NOT APPLICABLE

Per the skill's own prerequisite ("if the project has no separate test
mirror of business logic ... tell the user this skill doesn't apply and
stop"), this repo does not have the pattern this skill targets.

## What was checked

- `find . -maxdepth 2 -type d -iname "*test*"` → `ghar_re_core/tests`,
  `ghar_re_service/tests`. Both import the real implementation directly:
  `ghar_re_core/tests/test_pipeline.py`, `test_golden_master.py`,
  `ghar_re_service/tests/test_auth.py`, `test_service.py`, `test_bundle.py`
  all `import ghar_re_core` / exercise the live FastAPI app — none
  re-declares scoring weights, constraint rules, or type shapes
  independently.
- `supabase/functions/_tests/` — same pattern, exercises the real handlers.
- `mobile/` — no test directory with a re-implementation of business logic
  exists at all.
- Grep for duplicated weight/score constants outside `ghar_re_core` across
  `mobile/` and `supabase/functions/_tests/` — zero hits.

## Conclusion

This project tests by importing the real code directly everywhere, which
by construction can't drift the way a separate mirror can. No source of
truth / mirror pair exists to compare or sync. No fixes applied.

# FooFoo — Master Change Log
*Every code change goes here. Format is at the bottom of this file.*

---

## [Unreleased]

### Added
- `CHANGELOG.md` (this file) — initialised by the `install-logging-infrastructure` skill.
- Lightweight client logger `mobile/src/lib/logger.ts` (Expo/React Native, AsyncStorage-backed,
  hot-path friendly) — replaces the bare `console.warn` in `mobile/src/auth/supabaseClient.ts`.
- Transaction export script `scripts/export-txn-logs.mjs` — exports
  `public.recommendation_events` / `public.feedback_events` / `public.interaction_events` /
  `public.suggestion_logs` rows to plain-English per-user and per-system daily log files under
  `ops/logs/session-log/`.
- User Journey Logger `supabase/functions/_shared/logging/userJourney.ts` — plain-English,
  per-profile narrative log built on top of the existing structured
  `_shared/logging/logger.ts`, covering consent, onboarding/household writes, and
  recommendation-request outcomes.
- Decision logger `ghar_re_core/decision_log.py` — logs the Assemble-7 dish-pool decision
  (winners, top alternatives considered, plain-English reasoning) from
  `ghar_re_core/pairing.py`'s `assemble_7()`, using Python's stdlib `logging` in the same
  structured-JSON convention as `ghar_re_service/lifecycle.py`. Logging-only: does not alter
  scoring, ranking, or the plates returned (verified against the golden-master test).
- `logs/hygiene-reports/logging-compliance.md` — logging infrastructure install/compliance report.

### Changed
- `mobile/src/auth/supabaseClient.ts` — startup env-var check now logs via the new client logger
  instead of a raw `console.warn`.
- `ghar_re_core/pairing.py` (`assemble_7`) — added an optional `household_label` parameter and a
  one-line call to `decision_log.log_assemble7_decision(...)` at the end of the function, after
  the final plate list is decided. No existing behaviour, signature (for existing positional
  callers), or return value changed.
- `ghar_re_core/pipeline.py` (`recommend`) — passes `household["label"]` through to
  `pairing.assemble_7` so decision-log entries can name the household.

### Context (prior session, referenced by this entry)
- `dd2b824` — imported all remaining org dotfiles skills into `.claude/skills/` and amended the
  Skill Activation Policy so every installed skill runs proactively per session need.
- `c7904bb` — recorded that skill-import/activation-policy change as Session 45 in
  `KNOWLEDGE.html`.

---

## Change Log Entry Format

When adding an entry, use this template:

```markdown
## [vX.Y.Z] — [Milestone Name] — YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

---
*This file lives at the project root. Every Claude Code session that produces code must add an
entry here.*

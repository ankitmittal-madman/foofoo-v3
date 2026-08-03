"""
ghar_re_core.training — the s_pref offline training/eval pipeline (Phase 3, not fit, not shipped).

Nested under the existing `ghar_re_core` package rather than a new top-level folder, per
CLAUDE.md's Placement Rule (no top-level folder without an approved RACR; this architecture is
frozen pending Founder approval) — this is the nearest compliant location, matching the plan's own
suggested placement exactly (§3.4: "New file: ghar_re_core/training/train_pref_model.py").

This package NEVER touches Postgres directly (RE-DOC-10 §1: Edge Functions own 100% of DB
access, even for training) — it reads an offline feedback export (a JSONL file, produced manually
by a data owner via a SELECT against feedback_events/recommendation_events, not built by this
repo) and is never invoked against real production data by anything in this plan; there is no
real data yet (0 production feedback_events rows) to justify running it for real.
"""

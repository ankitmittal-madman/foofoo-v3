"""
ghar_re_core.training — the s_pref offline training/eval pipeline (Phase 3, not fit, not shipped).

Nested under the existing `ghar_re_core` package rather than a new top-level folder, per
CLAUDE.md's Placement Rule (no top-level folder without an approved RACR; this architecture is
frozen pending Founder approval) — this is the nearest compliant location, matching the plan's own
suggested placement exactly (§3.4: "New file: ghar_re_core/training/train_pref_model.py").

This package NEVER touches Postgres directly (RE-DOC-10 §1: Edge Functions own 100% of DB
access, even for training). It reads a JSONL export produced by a data owner through the
service-role-only `ml.preference_training_export_rows()` database function. Production training
remains fail-closed until volume, household diversity, identity attribution, and holdout gates pass.
"""

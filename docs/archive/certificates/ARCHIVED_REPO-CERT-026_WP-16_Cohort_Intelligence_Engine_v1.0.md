# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# [ACTIVE]_REPO-CERT-026_WP-16_Cohort_Intelligence_Engine_v1.0

**Status:** ACTIVE
**Version:** v1.0
**Date:** 2026-08-03
**Placement:** docs/archive/certificates/ARCHIVED_REPO-CERT-026_WP-16_Cohort_Intelligence_Engine_v1.0.md
**Certifies:** docs/archive/implementation/work-packages/ARCHIVED_WP-16_Cohort_Intelligence_Engine_v1.0.md (and its shipped increments WP-16.1 foreign-cuisine demote, WP-16.2 lifecycle_stage + real time_pressure + migrant-only overlay + per-user logs)
**Supersedes:** N/A

---

## What this certifies

WP-16 (Cohort Intelligence Engine — the learned, migration-blended, graded class-affinity model that replaced WP-15's binary `S_cohort`) was **executed** across commits `14294c1` (WP-16.1), `d1fbfb7` (WP-16.2) and is fully green in the current tree (`b066db5`). This certificate records the real execution output so the WP-16 work package may be read as COMPLETE. WP-16's compositional successor is certified separately (REPO-CERT-025 / WP-17).

## Execution evidence

### 1. The trained model artifact (learned from the excel, not copied)
```
$ python -c "import json; m=json.load(open('.../cohort_class_model.json'))"
features:        ['state_ut','region_archetype','city_tier_code','main_cohort_id',
                  'lifecycle_stage','time_pressure','nonveg_mode']   (7, all recomputable from theta)
label examples:  1,735,776   |   slot×day-type partitions: 8
model_type:      factorized log-linear (Naive-Bayes-style), pure-Python/JSON (no numpy/sklearn at runtime)
```
Trained offline from `Indian_Meal_Cohort_Persona_DB_v3.xlsx :: Weekly_Class_Plan_v3` (2,952 cohorts × 7 days), weighted primary=3/secondary=2/tertiary=1. Generalizes to feature combinations the excel never enumerated — a learned model, not a row lookup.

### 2. WP-16 test suite — green
```
$ python -m pytest ghar_re_core/tests/test_cohort_intel.py -q
8 passed
```
Covers: features complete & recomputable from theta; lifecycle_stage + banded time_pressure derived (the WP-16.2 toddler-cohort fix); graded/slot-specific/bounded affinity; reproduces a real cohort's primary class (learned-from-excel fidelity); generalizes to a feature combo; City_Migration overlay shifts the plan (MP-in-Mumbai science); 2-letter home_state code normalized end-to-end (the confirmed production bug); ranked sub-cohort membership.

### 3. Confirmed production bug fixed (WP-16 root cause)
The live app writes `profiles.home_state` as a 2-letter code (`MP`); the engine keys on full names. Unnormalized, the entire regional/cohort layer silently no-ops (test_10 MP/Mumbai got cross-regional plates). `knowledge.normalize_state` (36-state map) applied at the top of `derive_theta` AND in the `recommendations` edge function `compose.ts` — verified identical output for code vs full name.

### 4. WP-16.1 foreign-cuisine cold-start demote
`s_foreign(dish)` = 1.0 for zone=Global (Chinese/continental); a cold-start-strong, decaying demote (`foreign_demote_effective`) subtracted so foreign dishes with no cohort anchor stop crowding a brand-new regional household's slate (test_13 Gujarat "Veg Burger + Corn Chowder"). Soft demote, never a hard filter; decays with interaction volume.

### 5. WP-16.2 sub-cohort granularity + honesty of the plateau
`lifecycle_stage` (infant/toddler/school_child/teen/elder/pregnancy) + numeric `time_pressure` added so a dual-income toddler family resolves to the toddler cohort, not the family average; City_Migration overlay gated to genuine migrants; per-user Markdown session logs written to `ops/logs/session-log/`. This session also honestly established the learned model's **~37% overlap plateau** with a specific precomputed cohort — the finding that motivated the WP-17 compositional layer (REPO-CERT-025).

## Honest limitations (carried from the WP, not hidden)
- `feedback_events` has 0 production rows, so `w_cohort_effective` = cold-start for every live household — the decay curve exists, the data to move along it does not.
- The learned model alone plateaus at ~37% cohort overlap; WP-17's compositional layer is what closes the persona-specificity gap. WP-16 is the generalizing smoothing term underneath it.

---

## Founder Sign-off


# [ACTIVE]_REPO-CERT-025_WP-17_Compositional_Cohort_Plan_v1.0

**Status:** ACTIVE
**Version:** v1.0
**Date:** 2026-08-03
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-025_WP-17_Compositional_Cohort_Plan_v1.0.md
**Certifies:** docs/project-history/work-packages/[DRAFT]_WP-17_Compositional_Cohort_Plan_v1.0.md
**Supersedes:** N/A

---

## What this certifies

WP-17 (Compositional Cohort Plan + full nutritionist/chef dish→class coverage) was **executed**, not merely designed. This certificate records the real execution output; the WP-17 work package may be read as COMPLETE against it.

## Execution evidence

### 1. Dish→class coverage (#5) — full, from 202/810 → 810/810
```
$ python -m ghar_re_service.scripts.classify_dishes
  wrote dish_class_map.csv: 810/810 mapped (98 curated_exact, 712 chef_rubric, 87 chef low-confidence <0.4)
```
Diet-safety of derived rows verified by test (`test_real_catalogue_coverage_is_full_and_honest`): no veg dish is chef-mapped to an egg/nonveg-marked class. Spot-checks confirmed hero-ingredient routing: Rajma→LD_RAJMA_CHOLE_LEGUME, Chettinad Fish Curry→LD_FISH_CURRY_RICE, Mutton Rogan Josh→LD_MUTTON_SUNDAY_CURRY, Sabudana Khichdi→BF_FASTING_PHALAHARI, Idli→BF_STEAMED_FERMENTED_LIGHT, Masala Dosa→BF_FERMENTED_CREPE_PAN.

### 2. Compositional plan — S14_T1_P10 benchmark self-arrived at
MH/Pune couple + toddler (veg), the S14_T1_P10 shape:
```
resolved personas:  P10 family_with_toddler  match=1.0   |   P11 family_with_school_kids  match=0.429
compositional LUNCH plan (top): LD_CHILD_MILD_PLATE 1.00, LD_DAL_ROTI_SABZI 0.74,
                                LD_SIMPLE_GREEN_VEG_SABZI 0.74, LD_LIGHT_KHICHDI 0.55,
                                LD_MAHARASHTRIAN_PITLA_BHAKRI 0.41, LD_COCONUT_VEG_STEW 0.41
compositional DINNER plan (top): DN_CHILD_FRIENDLY_DINNER 1.00, DN_LIGHT_DAL_RICE 1.00,
                                 LD_CHILD_MILD_PLATE 0.70, LD_MAHARASHTRIAN_PITLA_BHAKRI 0.41
```
Mild/child/traditional-Maharashtrian classes lead across all three main slots — derived from Persona_Master + State_Profile + spine science, not copied from Cohort_Matrix.

### 3. Test suites — all green
```
$ python -m pytest ghar_re_core/tests/ -q
43 passed

$ cd ghar_re_service && python -m pytest -q
62 passed, 1 warning
```
Includes 7 new `test_cohort_plan.py` cases (persona resolution, graded/bounded/slot-specific plan, persona-core ∩ regional grounding, diet gate, lifecycle reshaping toddler vs DINK, migration-overlay-migrant-only) and the updated coverage/affinity tests. Golden master regenerated for 4 cases (`single_professional_blr`, `jain_couple_ahmedabad`, `couple_toddler_pune`, `migrant_bihar_mumbai`).

### 4. CI gates — all green
```
$ ruff check ghar_re_core/ && ruff check ghar_re_service/ghar_re_service/   → All checks passed!
$ ruff format --check ghar_re_service/ghar_re_service/                       → all formatted
$ python -m mypy ghar_re_core ghar_re_service/ghar_re_service                → Success: no issues found in 35 source files
$ python -m ghar_re_service.scripts.export_bundle --check                    → OK: bundle is current (sha256:d23f30d661accef2)
```

### 5. Artifacts produced
- `ghar_re_core/cohort_plan.py` (compositional derivation), `cohort_intel.class_affinity` fusion
- `ghar_re_service/scripts/classify_dishes.py` → `data/source/class_first_v1/dish_class_map.csv` (810 rows)
- `dish_class_overrides.csv` retired; bundle rebuilt with the new map
- `ops/logs/session-log/{test_10,test_13,test_14}.md` regenerated with compositional reasoning

## Honest limitations (carried from the WP, not hidden)
- 87 low-confidence dish mappings (mostly desserts/beverages/chutneys) — reviewable in `dish_class_map.csv` via the `confidence` column; they contribute only weak `S_cohort`.
- `feedback_events` still has 0 production rows, so `w_cohort_effective` = cold-start for every live household — the decay mechanism exists, the data to move along it does not.
- The two temporary testing changes (frontend caching off in `queryClient.ts`, always-onboarding in `index.tsx`) remain in place and must be reverted before launch — outside WP-17 scope.

---

## Founder Sign-off


# [DRAFT]_WP-18_Onboarding_Plan_Recipe_Flow_v1.0

**Status:** DRAFT — backend shipped and tested this session; edge + mobile wiring in progress. DRAFT until a companion certificate documents full-stack execution.
**Version:** v1.0
**Date:** 2026-08-03
**Placement:** docs/project-history/work-packages/[DRAFT]_WP-18_Onboarding_Plan_Recipe_Flow_v1.0.md
**Supersedes:** N/A — new user-facing flow on top of WP-17 (compositional plan) + WP-17.1 (multi-membership dish→class).
**Dependencies:** WP-17 / WP-17.1 (compositional cohort plan + full multi-membership dish→class map), Core Spine (scoring), the RE service (`/v1` API), Cloudinary (dish images), Supabase (persistence).

---

## Executive Summary

WP-18 turns the engine's output into the actual onboarding→plan→recipe product flow the Founder specified:

1. **Cold-start preference primer** — after onboarding, show **15 diverse top dishes** to like/seed.
2. **Daily meal plan** — **Breakfast / Lunch / Dinner**, each with **4–5 dish options**.
3. **Weekly class plan** — for each day × slot, the **top-3 meal CLASSES** to select and finalize.
4. **Reconciliation** — once a day's class is finalized, that day shows **only dishes of that class**.
5. **Recipe screen** — each meal opens a full recipe, with a **Cloudinary image**.

The engine surfaces are shipped and tested this session as `ghar_re_core.meal_planner` + five signed RE endpoints. The reconciliation guarantee (4) is enforced end-to-end and covered by tests. Multi-membership (WP-17.1) makes it work in practice: because a dish can belong to a primary class **and** the secondary classes it also fits, the behavioural DN_ dinner classes (child-friendly, family-comfort) reconcile to real dishes instead of falling back to regional plates — the thin-coverage failure observed for test_17.

## 1. Engine surfaces (`ghar_re_core.meal_planner`) — SHIPPED
| Fn | Surface | Contract |
|---|---|---|
| `cold_start_top15` | 1 | 15 diverse (per-class/per-cuisine capped), eligible, slot-tagged dishes |
| `slot_options` | 2 | a slot's 4–5 best eligible dishes |
| `weekly_class_plan` | 3 | 7 days × slots, top-3 **dish-backed** classes (with `dish_count`) |
| `dishes_for_class` | 4 | RECONCILIATION: only dishes whose class-set contains the chosen class |

Nothing here re-decides eligibility or invents a score — it ranks/groups what `scoring` already produces (`scoring.eligible` stays the sole filter). Returns plain JSON.

## 2. Service endpoints (`ghar_re_service`) — SHIPPED
`POST /v1/cold-start`, `/v1/meal-plan`, `/v1/weekly-plan`, `/v1/class-dishes`, `/v1/recipe` — all signed + rate-limited, translation-only (parse → `engine.plan_*` → serialize). `engine.py` attaches media; `media.py` builds Cloudinary URLs + serves the recipe store.

## 3. Recipes — SHIPPED (offline, cached)
`scripts/generate_recipes.py` composes a structured recipe per dish (intro, ingredient list from real data, method steps ordered by the dish's own cooking_method + category, real times, serving suggestion) → `recipes_v1.json` (baked in the bundle). Tagged `auto_draft_from_attributes`; quantities are qualitative ("to taste") — no gram amounts are invented (FD-11).

## 4. Images — CONFIGURED, pending account details
`media.image_url(dish)` builds a deterministic Cloudinary URL: `res.cloudinary.com/<CLOUD>/image/upload/<TRANSFORM>/<FOLDER>/<slug>.<ext>`, all env-overridable (`CLOUDINARY_CLOUD_NAME/_DISH_FOLDER/_DISH_TRANSFORM`). Returns `None` (app placeholder) until the cloud name is set. **Pending Founder input:** cloud name, folder/naming convention, coverage, transforms.

## 5. Persistence + mobile — IN PROGRESS
- Supabase: user's liked dishes (cold-start) + finalized weekly plan (day→slot→class).
- Edge functions to proxy the signed RE calls + persist selections.
- Mobile: cold-start top-15 screen, daily plan, weekly plan selection, recipe detail.

## 6. Validation (this session)
- 48 core tests (incl. `test_meal_planner.py`: cold-start diversity, slot options, weekly shape, reconciliation contract, Jain eligibility) + 68 service tests (incl. `test_planning.py` e2e for all 5 endpoints incl. reconciliation). All pass.
- ruff + format + mypy (39 files) + `export_bundle --check` green. Bundle rebuilt with `recipes_v1.json`.

## 7. Critical Self-Review
- **Reconciliation honesty:** dishes for a finalized class are filtered to that class's membership set — the plan and dish list cannot disagree. Multi-membership widens the pool without loosening the rule.
- **Thin classes:** `weekly_class_plan` only offers classes with `dish_count ≥ 1` and reports the count, so the UI never finalizes an empty class. Multi-membership largely resolves the DN_ starvation; any residual is visible, not silent.
- **Recipes are drafts, labelled as such** — not authoritative, refine later.
- **Images degrade gracefully** to a placeholder until the real Cloudinary account is wired.

---

## Versioning & Placement
New: `ghar_re_core/meal_planner.py`, `ghar_re_service/media.py`, `scripts/generate_recipes.py`, `data/source/recipes_v1.json`, `tests/test_meal_planner.py`, `tests/test_planning.py`, 5 endpoints. Placement validated; no new top-level folder.

## Founder Sign-off


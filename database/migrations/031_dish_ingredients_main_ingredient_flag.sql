-- Migration: 031_dish_ingredients_main_ingredient_flag.sql
-- Implements: SER-002 (Founder-approved) — adds the structural capability for
--   CandidateRepository's mainIngredientClass field (FD-11, the last of the four original
--   WP-8F blockers per REPO-CERT-019) to eventually be computed. Does NOT populate any data;
--   the derivation rule and the actual flagged rows remain FD-11's separate, still-pending
--   Founder deliverable.
-- Logical functions: feeds DishCandidate.mainIngredientClass (LF-D/E variety and scoring),
--   once FD-11's rule is ratified and the data is loaded — neither of which happens here.
-- Governance refs: [ACTIVE]_SER-002_dish_ingredients_main_ingredient_flag_v1.0.md
--   (approved as written, promoted DRAFT -> ACTIVE alongside this migration).
--
-- Why a boolean, not a rank/weight column: FD-11's derivation rule (by weight/quantity, by
--   source listing order, or a curated override table) is still unratified. A rank or weight
--   column would presuppose one of those rules; a boolean is the minimal structure consistent
--   with any of them, including a curated override table that simply flags rows true/false.
--
-- Why no uniqueness constraint: a dish may have more than one dominant ingredient (a mixed
--   dal, a combo-style dish, two co-equal proteins) — the column must support multiple TRUE
--   rows per dish_id. Restricting to one TRUE row per dish would be a fabricated constraint
--   this table's own use case doesn't require.
--
-- Verified before writing this migration: public.dish_ingredients (migration 009) has no
--   existing column expressing ingredient dominance; no view, trigger, function, or index
--   references a column of this name. Adding NOT NULL DEFAULT false means every existing row
--   becomes false on migration — no existing query's result set changes, since nothing
--   currently reads this column.

ALTER TABLE public.dish_ingredients
  ADD COLUMN is_main_ingredient boolean NOT NULL DEFAULT false;

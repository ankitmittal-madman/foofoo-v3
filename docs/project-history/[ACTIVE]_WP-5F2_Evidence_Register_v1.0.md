# WP-5F2 Evidence Register v1.0

**Status:** ACTIVE — evidence register (raw execution artifacts)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_WP-5F2_Evidence_Register_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5F2 Execution Report, Validation Report, Decision Log.

---

## 1. Environment evidence

- Engine: `PostgreSQL 15.18 (Debian 15.18-1.pgdg13+1) on x86_64-pc-linux-gnu`.
- Container date: `2026-07-13`.
- Pre-migration base-table count: `0` (empty).
- Roles created: `anon` (rolbypassrls=f), `authenticated` (f), `service_role` (t) — mirrors Supabase.
- **No Supabase MCP call was made; production project `slsqtlygeekdppuyiiff` was never contacted.**

### 1.1 Compatibility bootstrap (verbatim — harness only, NOT a repo migration)
```sql
CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN BYPASSRLS;
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO anon, authenticated, service_role;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE TABLE auth.users (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), email text);
CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE
  AS $$ SELECT nullif(current_setting('request.jwt.claims', true)::json ->> 'sub','')::uuid; $$;
GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;
```

## 2. Migration evidence (28/28 PASS)
Every file 001→028 applied with `ON_ERROR_STOP=1`, rc=0, ~92–180 ms each. Post-build: 62 base tables; 6 partition children (`interaction_events_2026_07/08/09`, `suggestion_logs_2026_07/08/09`).

## 3. Seed evidence
- 100/101/102 all rc=0.
- `re_engine.re_meal_classes` (9 rows) slot values: `ADDON_DIABETIC={snack}`, `ADDON_INFANT={snack}`, `BF_LIGHT_GRAIN/BF_SOUTH_FERMENTED/BF_STUFFED_FLATBREAD={breakfast}`, `COMBO_RICE_DAL_VEG/LUNCH_DAL_SABZI_ROTI={lunch}`, `DIN_CURRY_ROTI/DIN_NON_VEG_MAIN={dinner}`.
- Trigger-derived dishes: `Poha` → vegan/is_jain=f/allergen=0; `Aloo Poha with Peanuts` → vegan/f/1; `Butter Chicken` → non_veg/f/2.

## 4. Validation evidence (key raw outputs)
- 900-1: `table_count=62, expected=62, pass=t`.
- 900-2: `(0 rows)` ← VAL2-01.
- 900-3: `proname` = 5 rows (incl. `fn_assign_tag_vector_positions`); `tgname` = 4 rows.
- 900-4: `should_be_false = t` (authenticated HAS UPDATE on diet_type).
- 900-5: `count = 20`.
- 900-6: `should_be_false = f` (authenticated has NO re_engine USAGE — correct).
- 900-7: S-02=5/5 ✅, S-05=8/8 ✅; S-01,03,04,06–15 fail (illustrative, IDR-001).
- 901-1: `Poha | vegan | f | 0`.
- 901-4: `NOTICE: PASS: dish allergen_flags updated from 1 to 33 …`.
- 901-5: `ERROR: FAIL: authenticated role was able to write diet_type directly` (no insufficient_privilege raised).
- 902-1..3 correct; 902-4 `SKIPPED` (no profile fixture).
- 903 cross-user `SKIPPED`; anon write `PASS`; re_engine invisibility `PASS`.
- 904-1 all tiers `1.00 | t`; 904-2 `PASS` (CHECK rejects sum 2.5); 904-3 `dish_not_today λ=0.35`; smoke `PASS`.

## 5. SEC-901T5 diagnostic evidence (WP-04DC method, executed)
```
has_column_privilege('authenticated','public.dishes','diet_type','UPDATE') = t
BEGIN; SET ROLE authenticated;
  set_config('request.jwt.claims', '{"sub":"…","role":"authenticated"}', true) → claim_set=t
  UPDATE public.dishes SET diet_type='vegan' WHERE name='Poha';  → "UPDATE 0"
RESET ROLE; ROLLBACK;
post-check: Poha still diet_type=vegan (unchanged)
```
**Interpretation:** privilege present (GRANT gap real) BUT 0 rows affected (RLS default-deny held) → data safe → 901 Test 5 test-design defect; GRANT gap = defense-in-depth item for WP-5D.

## 6. Rollback evidence
- Seeded loud-fail: `028` → `ERROR: check constraint "re_weight_ladder_config_check" is violated by some row`; `027` → `ERROR: column "show_question_key" … contains null values`.
- Pristine teardown (fresh unseeded rebuild): 28/28 rollbacks 028→001 rc=0; end state `base_tables=0`, `re_engine_schema_exists=false`, `fn_ functions=0`, `partition_children=0`.

## Critical Self-Review

- **Considered** committing the bootstrap SQL into `database/`. **Rejected** — it is not a repository migration; committing it risks being mistaken for one (the brief forbids new migrations). It is preserved verbatim here instead.
- **Limitation:** raw psql transcripts are summarised here, not attached as separate log files; the commands are reproducible verbatim from this register against any empty PostgreSQL 15.

## Founder Sign-off

Founder acceptance of the WP-5F2 Evidence Register: _______________________ Date: ___________

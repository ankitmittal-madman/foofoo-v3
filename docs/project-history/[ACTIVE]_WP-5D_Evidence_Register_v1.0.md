# WP-5D Evidence Register v1.0

**Status:** ACTIVE — evidence register (read-only live-DB introspection + repository comparison)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_WP-5D_Evidence_Register_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5B Migration Recovery Report §4 (first named the 3 candidates); WP-5F2 Execution (SEC-901T5 / GRANT-gap root-cause); Migration ledger of production project `slsqtlygeekdppuyiiff`.

---

All evidence below was gathered by **read-only** queries against the production Supabase project `slsqtlygeekdppuyiiff` (migration ledger + catalog introspection). **No production object was modified.** Live SQL text is preserved as evidence; it was read, never executed locally.

## 1. Production migration ledger (31 tracked migrations)

| Version | Name | In repo? |
|---|---|---|
| 20260706085821 … 20260706092303 | `001_…` – `025_…` | ✅ (names match) |
| 20260708141613 | `026_meal_classes_mirror_slot_array` | ✅ |
| 20260709115033 | `routing_rules_show_question_key_nullable` | ✅ as `027_…` (repo added ordinal) |
| 20260709183446 | `weight_ladder_config_numeric_weights` | ✅ as `028_…` (repo added ordinal) |
| 20260710101630 | **`pf1_security_hardening`** | ❌ MISSING |
| 20260710104454 | **`103_production_cuisines`** | ❌ MISSING |
| 20260710104859 | **`103_production_ingredients`** | ❌ MISSING |

Diff verified complete: exactly **3 migrations missing** from the repo; the candidate list was accurate, nothing extra, nothing obsolete. No repo migration is absent from production.

## 2. `pf1_security_hardening` — exact applied SQL (recovered verbatim from `supabase_migrations.schema_migrations`)

```sql
-- Finding 1: fn_assign_tag_vector_positions — the one genuinely RPC-exploitable function
REVOKE EXECUTE ON FUNCTION public.fn_assign_tag_vector_positions() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fn_assign_tag_vector_positions() TO service_role;
ALTER FUNCTION public.fn_assign_tag_vector_positions() SET search_path = public, pg_catalog;

-- Finding 2: AGR-001 completion — close INSERT/REFERENCES alongside the existing UPDATE revoke
REVOKE INSERT, UPDATE, REFERENCES (
  diet_type, is_jain, allergen_flags, genome_vector,
  popularity_score, acceptance_rate_7d, acceptance_rate_30d
) ON public.dishes FROM authenticated, anon;

-- Finding 3: RPC exposure cleanup on the remaining trigger / event-trigger functions
REVOKE EXECUTE ON FUNCTION public.fn_derive_dish_attributes() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fn_derive_dish_attributes() TO service_role;
REVOKE EXECUTE ON FUNCTION public.fn_propagate_ingredient_change() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fn_propagate_ingredient_change() TO service_role;
REVOKE EXECUTE ON FUNCTION public.fn_update_dish_genome_vector() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fn_update_dish_genome_vector() TO service_role;
REVOKE EXECUTE ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;   -- ← dangling dependency (see §4)

-- Finding 4: pin search_path on all 5 flagged functions
ALTER FUNCTION public.fn_derive_dish_attributes()      SET search_path = public, pg_catalog;
ALTER FUNCTION public.fn_propagate_ingredient_change() SET search_path = public, pg_catalog;
ALTER FUNCTION public.fn_update_dish_genome_vector()   SET search_path = public, pg_catalog;
ALTER FUNCTION public.fn_sync_profile_allergen_union() SET search_path = public, pg_catalog;
```
- Confidence in TEXT: **HIGH** (verbatim from the ledger, not reconstructed).
- All 5 `fn_*` functions it targets exist in the repo (migrations 010 + 023) — those lines are canonical-clean.
- Its `REVOKE INSERT, UPDATE, REFERENCES (…) ON public.dishes` **completes** migration 008's partial column-`REVOKE UPDATE` — this is the fix WP-5F2 proved was needed (the GRANT-level defense-in-depth gap).
- **One line references `public.rls_auto_enable()`** — an object no repo migration creates (see §4).

## 3. `103_production_cuisines` / `103_production_ingredients` — shape (NOT recovered)

| Migration | Statement head | Size | Kind |
|---|---|---|---|
| 103_production_cuisines | `INSERT INTO public.cuisines (name, display_name, …) VALUES ('punjabi', …)` | 21,703 chars | pure INSERT (production data) |
| 103_production_ingredients | `INSERT INTO public.ingredients (…) VALUES ('turmeric', …) ON CONFLICT (name) DO NOTHING` | 31,453 chars | pure INSERT (production data) |

Both are **production seed DATA** loading real cuisines/ingredients rows. Content deliberately **not reproduced** here (WP-5D forbids generating production seed data).

## 4. Untracked production objects (no migration provenance)

- **`public.rls_auto_enable()`** — `event_trigger` function, `SECURITY DEFINER`, owner `postgres`. Full def (verbatim):
```sql
CREATE OR REPLACE FUNCTION public.rls_auto_enable()
 RETURNS event_trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'pg_catalog'
AS $function$
DECLARE cmd record;
BEGIN
  FOR cmd IN SELECT * FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE','CREATE TABLE AS','SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
    IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public')
       AND cmd.schema_name NOT IN ('pg_catalog','information_schema')
       AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION WHEN OTHERS THEN
        RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
    ELSE
      RAISE LOG 'rls_auto_enable: skip % (…)', cmd.object_identity, cmd.schema_name;
    END IF;
  END LOOP;
END;
$function$
```
- **`ensure_rls`** — event trigger, `ON ddl_command_end`, owner `postgres`, `EXECUTE FUNCTION rls_auto_enable()`. Equivalent DDL: `CREATE EVENT TRIGGER ensure_rls ON ddl_command_end EXECUTE FUNCTION public.rls_auto_enable();`
- Evidence of no provenance: `migrations_creating = null` (no ledger statement creates `rls_auto_enable`); it is mentioned only by `pf1`.
- The other 6 production event triggers (`issue_graphql_placeholder`, `issue_pg_cron_access`, `issue_pg_graphql_access`, `issue_pg_net_access`, `pgrst_ddl_watch`, `pgrst_drop_watch`) are owner `supabase_admin` = **Supabase platform** objects, correctly not repo artifacts.
- Public functions in production = exactly the 5 repo-defined `fn_*` + `rls_auto_enable` (no other untracked functions).

## 5. Measured schema-state drift (production vs WP-5F2 clean-room build)

| Metric | Production | Repo clean-room (WP-5F2) | Match? |
|---|---|---|---|
| Base tables (public+re_engine, excl. partition children) | 62 | 62 | ✅ |
| Public policies | 24 | 24 (23 from mig 019 + cuisines) | ✅ |
| Public tables with RLS ENABLED | **33** | **20** | ✗ **+13 drift** |
| Internal audit tables with RLS enabled | 7 (audit_log, coverage_gap_log, derivation_conflicts, etl_job_runs, feature_flags, push_notification_logs, safety_gate_log) | 0 (mig 019 intentionally leaves them without RLS) | ✗ |

The +13 (7 internal audit tables + 6 partition children) is caused **entirely by the untracked `ensure_rls` event trigger** auto-enabling RLS on every created public table. This explains the "live = 33" figure WP-04DA observed. Not a security problem (RLS-enabled-without-policy = default-deny; service_role bypasses), but a **documented divergence from the frozen migration-019 design**.

## Critical Self-Review

- **Considered** dumping the full 103_* INSERT bodies as evidence. **Rejected** — WP-5D forbids generating production seed data; their shape/size is sufficient to classify them.
- **Limitation:** parity was assessed at the migration level plus the objects surfaced by `pf1`'s dependency and an RLS-count check; a byte-level full-schema `pg_dump` diff (every index/constraint) is a WP-5G live-cert activity, not repeated here.

## Founder Sign-off

Founder acceptance of the WP-5D Evidence Register: _______________________ Date: ___________

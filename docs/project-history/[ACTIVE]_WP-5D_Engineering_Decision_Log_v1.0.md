# WP-5D Engineering Decision Log v1.0

**Status:** ACTIVE — decision log
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_WP-5D_Engineering_Decision_Log_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5D Evidence Register; WP-5F2 Execution Report; migration 019 (frozen RLS design); Migration Recovery Report §4.

---

## Classifications (STEP 4)

| Migration | Class | Evidence | Action |
|---|---|---|---|
| `pf1_security_hardening` | **A — Canonical engineering** | Security/privilege hardening (function EXECUTE lockdown, search_path pinning, completion of migration-008's AGR-001 column REVOKE). Engineering, not data/environment. | Recover — **BLOCKED** (see D-03) |
| `103_production_cuisines` | **B — Production deployment (data)** | 21.7 KB pure `INSERT INTO public.cuisines … VALUES` (real cuisines) | **Not recovered** — production seed data; env-specific; explicitly forbidden by WP-5D |
| `103_production_ingredients` | **B — Production deployment (data)** | 31.5 KB pure `INSERT INTO public.ingredients … ON CONFLICT DO NOTHING` (real ingredients) | **Not recovered** — same |

## Decisions

| ID | Decision | Verdict | Reasoning |
|---|---|---|---|
| D-01 | Use read-only production introspection as recovery evidence | MADE | Brief authorizes "live database evidence"; migration-ledger + catalog reads modify nothing |
| D-02 | Recover `pf1` **text** verbatim from the ledger (not reconstruct) | MADE | `supabase_migrations.schema_migrations.statements` holds the exact applied SQL → HIGH-confidence, zero fabrication |
| D-03 | **Do NOT commit** `pf1` as a repo migration this session | MADE | `pf1` REVOKEs EXECUTE on `public.rls_auto_enable()`, which **no repo migration creates** → committing it alone makes the repo non-self-rebuildable (violates STEP 7). Every alternative crosses a line reserved to the Founder (D-05) |
| D-04 | `103_*` are NOT canonical; exclude from repo | MADE | Production seed DATA; brief forbids generating production seeds; repo's canonical seed story is illustrative seeds 100–102 under IDR-001 |
| D-05 | Escalate the `rls_auto_enable`/`ensure_rls` canonical-status question to the Founder | MADE | These untracked, postgres-owned objects auto-enable RLS on every public table — which **conflicts with frozen migration 019's deliberate design** (internal audit tables intentionally without RLS). Bringing them into canonical schema is a schema/architecture change; "Do NOT modify frozen architecture / redesign schema" forbids me deciding it unilaterally |
| D-06 | Do NOT modify `pf1` (e.g., drop/guard the `rls_auto_enable` line) to force clean-room applicability | MADE | Would break byte-parity with production — defeats WP-5D's own objective. Fidelity over convenience |
| D-07 | Flag the 027/028 naming divergence; do NOT rename anything | MADE | Repo files carry `027_`/`028_` ordinals; production ledger names are bare. Bulk renaming needs explicit Founder authorization (Naming Standard §6); recorded as a parity note only |
| D-08 | Commit WP-5D **documentation only**; no `database/` change | MADE | WP-5D reconciles and reports; the sole canonical recovery (pf1) is blocked pending D-05. Honest partial outcome per STEP 6 |

## The pf1 recovery blocker — options presented to the Founder (not chosen here)

1. **Adopt the RLS-overlay as canonical:** author a migration creating `rls_auto_enable()` + `ensure_rls`, then commit `pf1` verbatim. ⚠️ Forces auto-RLS onto internal audit tables, contradicting migration 019's frozen intent — a real behavioral/architecture change. Needs architecture review.
2. **Treat the overlay as production-operational (non-canonical):** commit a canonical `pf1` with the single `rls_auto_enable` REVOKE line omitted/quarantined and documented as environment-specific. ✅ Keeps clean-room rebuildable; ✗ not byte-identical to production (documented, principled deviation).
3. **Defer pf1 entirely** until the overlay decision is made. (Current state.)

## Critical Self-Review

- **Considered** committing `pf1` verbatim as `029_security_hardening.sql` for maximal parity. **Rejected** — it would not apply on a fresh repo-only build (dangling `rls_auto_enable`), making the "complete source of truth" claim false, which is the opposite of WP-5D's goal.
- **Considered** silently classifying `rls_auto_enable` as non-canonical and shipping option 2. **Rejected as a unilateral act** — its RLS behavior contradicts frozen migration 019; the classification is genuinely the Founder's architecture call, so it is escalated, not assumed.

## Founder Sign-off

Founder acceptance of the WP-5D Engineering Decision Log: _______________________ Date: ___________

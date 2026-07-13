# WP-5D Validation Report v1.0

**Status:** ACTIVE — validation report
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_WP-5D_Validation_Report_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5D Evidence Register, Decision Log; WP-5F2 Execution Report (rebuildability baseline).

---

## 1. Repository integrity after WP-5D (STEP 7)

WP-5D committed **no `database/` change**, so the execution-proven state from WP-5F2 is preserved unchanged.

| Check | Result | Basis |
|---|---|---|
| Migration numbering intact | ✅ | no migration added/renamed/removed |
| Dependency chain intact | ✅ | no DDL touched |
| Rollback chain intact (28/28) | ✅ | no rollback touched |
| No schema contradiction introduced | ✅ | repo SQL byte-identical to `92a717c` |
| Repository still rebuildable | ✅ | WP-5F2 clean-room result stands (001–028 apply, teardown to empty) |
| Frozen architecture untouched | ✅ | `rls_auto_enable` overlay deliberately NOT introduced |

## 2. Would the recovered `pf1` rebuild cleanly? (forward-looking)

**No — not as-is.** Verbatim `pf1` includes `REVOKE EXECUTE ON FUNCTION public.rls_auto_enable() …`; `rls_auto_enable()` is created by no repo migration, so a fresh repo-only build would error on that line. This is the precise, evidence-backed reason `pf1` is not committed this session (Decision Log D-03/D-05). The other 15 statements in `pf1` reference only repo-present objects (the 5 `fn_*` functions, `public.dishes`) and would apply cleanly.

## 3. Cross-check against WP-5F2 / WP-04DA (regression)

| Prior observation | WP-5D verdict |
|---|---|
| WP-5F2: authenticated holds column UPDATE despite mig-008 REVOKE (GRANT gap) | ✅ CONFIRMED — `pf1` Finding 2 is exactly the fix (`REVOKE INSERT, UPDATE, REFERENCES (…) ON dishes`) |
| WP-5F2: SEC-901T5 data-safe via RLS; GRANT gap = defense-in-depth for WP-5D | ✅ CONFIRMED — `pf1` is that defense-in-depth migration |
| WP-04DA: live RLS-enabled count = 33 (vs repo ~19–20) | ✅ EXPLAINED — the untracked `ensure_rls` event trigger auto-enables RLS on +13 tables (7 internal audit + 6 partition children) |
| WP-5F2 clean-room: 62 base tables, 24 policies | ✅ MATCH production (62 / 24) |

No prior conclusion rejected; WP-04DA's unexplained "33" is now root-caused.

## 4. Parity impact summary

- **Identical:** base tables (62), policies (24), migrations 001–028 content.
- **Divergent:** RLS-enabled table count (33 prod vs 20 repo) due to untracked `ensure_rls`; `pf1` absent; `103_*` seed data absent (intentional); 027/028 filename ordinals vs bare ledger names.

## Critical Self-Review

- **Considered** running another local clean-room to "prove" `pf1` fails on `rls_auto_enable`. **Rejected as unnecessary** — the failure mode is deterministic and self-evident from the SQL (`REVOKE … ON FUNCTION` a non-existent function errors); re-executing would add cost without new information. The WP-5F2 clean-room already established the baseline.
- **Limitation:** validation is at migration/object level, not a full `pg_dump` byte diff (WP-5G).

## Founder Sign-off

Founder acceptance of the WP-5D Validation Report: _______________________ Date: ___________

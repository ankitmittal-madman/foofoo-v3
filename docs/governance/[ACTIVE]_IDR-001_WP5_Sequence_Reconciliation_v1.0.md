# IDR-001 — WP-5 Sequence Reconciliation v1.0

**Status:** ACTIVE — Interpretation Decision Record (raised, awaiting Founder ratification)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/governance/[ACTIVE]_IDR-001_WP5_Sequence_Reconciliation_v1.0.md
**Supersedes:** None
**Dependencies:** [ACTIVE]_Repository_Recovery_Work_Package_Plan_v1.0; [ACTIVE]_Repository_Recovery_Roadmap_v1.0; WP-5F brief (this session's Founder command).

---

## 1. Discovery

The committed **Repository Recovery Work Package Plan v1.0** defines the WP-5 series as:

| Plan | Meaning |
|---|---|
| WP-5A | Audit |
| WP-5B | Migration Recovery |
| WP-5C | Rollback Recovery |
| WP-5D | Execution Recovery (re-run/certify WP-4B/4C/4DB) |
| WP-5E | Repository Freeze (templates/runbooks/RACR/naming/errata) |
| WP-5F | **Repository Green Certification** |

This session's Founder command instead defines **WP-5F = Clean-Room Repository Validation**, and its Step 9 recommends three follow-on packages:

| Brief | Meaning |
|---|---|
| WP-5D | **Production Migration Recovery** (the 3 live-only migrations) |
| WP-5E | **Execution Evidence Recovery** |
| WP-5G | **Repository Green Certification** |

The two numbering schemes diverge: the plan has no "Clean-Room Validation" WP and no "Production Migration Recovery" WP, and it uses 5F (not 5G) for Green Certification.

## 2. Interpretation applied this session

Per CLAUDE.md precedence (Founder Decisions rank above Project Workflow/APDF), the **live Founder command is authoritative for this session.** WP-5F was therefore executed as Clean-Room Validation, and the follow-on recommendations use the brief's labels (5D Production-Migration-Recovery, 5E Execution-Evidence, 5G Green). The committed WP Plan is **not edited** (never rewrite a superseded/ratified plan in place); this IDR records the reconciliation additively.

## 3. Mapping (brief ↔ committed plan)

- Brief **WP-5D (Production Migration Recovery)** — *new*; no equivalent in the plan. Covers the three applied-but-missing migrations (`pf1_security_hardening`, `103_production_cuisines`, `103_production_ingredients`) recorded in Migration_Recovery_Report §4.
- Brief **WP-5E (Execution Evidence Recovery)** ≈ plan **WP-5D (Execution Recovery)**, extended to also fix SEED-01 and VALIDATION-01 (found in WP-5F).
- Brief **WP-5G (Green Certification)** ≈ plan **WP-5F (Green Certification)**.
- Plan **WP-5E (Repository Freeze)** has no explicit brief counterpart; its governance items (templates, runbooks, RACR, naming errata, freeze certificate) remain open and should be folded into WP-5E or a distinct freeze package at Founder discretion.

## 4. Decision required from Founder

Ratify one canonical WP-5 numbering going forward (adopt the brief's scheme, keep the plan's, or issue a merged scheme), so future sessions cite one map. Until ratified, this IDR is the reconciliation of record.

## Critical Self-Review

- **Considered** silently renumbering to match the committed plan (calling this session "WP-5F′" = the plan's future 5F). **Rejected** — the Founder's live command explicitly titled it WP-5F Clean-Room Validation; honoring the command and recording the divergence is more faithful than overriding it to fit a prior plan.
- **Considered** editing the WP Plan to insert the new packages. **Rejected** — the plan is a Founder-facing artifact; changing numbering is a Founder decision, so this is raised as an IDR, not applied.

## Versioning & Placement

`[ACTIVE]_IDR-001_WP5_Sequence_Reconciliation_v1.0.md` → docs/governance/. New file; supersedes nothing.

## Founder Sign-off

Founder ratification of the reconciled WP-5 numbering: _______________________ Date: ___________

# Repository Recovery Risk Register v1.0

**Status:** ACTIVE — Risk register, report only
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/governance/[ACTIVE]_Repository_Recovery_Risk_Register_v1.0.md
**Supersedes:** None — first Repository Recovery Risk Register
**Dependencies:** Repository_Completeness_Audit_v1_0, Repository_Recovery_Backlog_v1_0. Scoped to recovery risk only; the product/technical Risk Register (PM-SUPP-02) is unaffected and not superseded.

---

## Executive Summary

Per Step 8, every gap is classified across five risk dimensions and one recovery-complexity rating. Dimensions: **Repository** (can the repo represent its own truth?), **Architecture** (is the design at risk?), **Implementation** (does it block building?), **Production** (does it endanger a live/deployed system?), **Trust** (does it risk "described mistaken for done"?). Complexity: Low / Medium / High / Critical.

The dominant risk is **repository self-sufficiency**: the repo cannot rebuild its own database. Architecture risk is uniformly low — every missing item has a known, frozen, or fully-described design; nothing missing is a lost *decision*.

## 1. Risk Table

| ID | Gap | Repo | Arch | Impl | Prod | Trust | Complexity |
|---|---|---|---|---|---|---|---|
| RR-01 | Forward migrations 021–026 absent (incl. `re_dish_regional_affinity`) | **Critical** | Low | High | High | High | **High** |
| RR-02 | Rollbacks 020–026 absent (authored, lost) | High | Low | Medium | High | Medium | Medium |
| RR-03 | Rollbacks 001–019 never authored | High | Low | Medium | High | Low | Medium |
| RR-04 | WP-4B/WP-4C/WP-4DB executed without certificate | Medium | Low | Medium | Medium | **High** | Medium |
| RR-05 | WP-4A / WP-4C design docs absent | Low | Low | Low | Low | Medium | Low |
| RR-06 | Engineering templates + runbooks absent | Low | Low | Low | Low | Low | Low |
| RR-07 | RACR process undefined (named in CLAUDE.md) | Medium | Low | Low | Low | Low | Low |
| RR-08 | Naming inconsistency (3 conventions) | Low | Low | Low | Low | Medium | Low |
| RR-09 | REPO-BOOT-03 §6 overstates DB completeness | Low | Low | Low | Low | **High** | Low |
| RR-10 | Live-DB state unverified vs. repo (28 mig / 143 rows is a doc claim) | Medium | Low | Medium | Medium | Medium | Low |

## 2. Rationale for the Critical rating (RR-01)

A repository that cannot regenerate its production schema from its own migrations has lost its defining property as the source of truth for the database. Any clean-environment rebuild (staging recreation, disaster recovery, new contributor) would produce a schema **missing `re_dish_regional_affinity` and five other objects**, silently diverging from production. This is why RR-01 is the only Critical entry and why WP-5B is the first recovery work after this audit.

## 3. Rationale for the High Trust risks (RR-04, RR-09)

RR-04: filenames like "...Certification..." and "WP-4B ✅ complete" imply completion the repository cannot prove — the exact failure mode ("described = done") that this project's governance was built to prevent (CLAUDE.md lifecycle rule). RR-09: a *certificate* (the highest-trust artifact class) contains an inaccurate completeness claim; left unsigned-and-uncorrected it could be inherited as fact.

## 4. Non-goals

Product/launch risks (DPDP age-gate, cold-start quality, dish-DB completeness) remain owned by PM-SUPP-02 and are explicitly out of this register's scope.

## Critical Self-Review

- **Considered** rating RR-01 Architecture as High. **Rejected** — the *design* of 021–026 is fully described (WP-02 §7.6, Freeze Packs) and frozen; the risk is to the repository's representation, not to the architecture itself. Overstating architecture risk would misdirect recovery effort toward re-deciding settled design.
- **Considered** omitting RR-10 (unverified live DB) as "not a gap." **Kept** — the gap between an unverified doc claim and observed reality is itself a risk the recovery must close (via introspection in WP-5B), and naming it prevents a future session from treating "143 rows" as established fact.

## Versioning & Placement

`[ACTIVE]_Repository_Recovery_Risk_Register_v1.0.md` → `docs/governance/`. New file; supersedes nothing.

## Founder Sign-off

Founder acceptance of the Repository Recovery Risk Register: _______________________ Date: ___________

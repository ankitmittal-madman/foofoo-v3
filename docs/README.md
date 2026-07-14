# FooFoo Documentation Index
Start here. AI assistants: read CLAUDE.md at repo root first for operating rules.

| Folder | Contains | Start with |
|---|---|---|
| product/ | What FooFoo is, market context | DOC-01_Product_Brief |
| architecture/ | Schema, RE design, UX, PRD | DOC-10_Technical_Architecture |
| governance/ | Standing rules, frozen decisions | APDF_Framework_Base, AGR-005/006 |
| project-history/work-packages/ | Every work package | Latest REPO-WP-* by number |
| project-history/certificates/ | Proof of actual execution | REPO-CERT-006 (GREEN cert); REPO-BOOT-03 (history) |
| research/ | Batch1-6 discovery process | Batch1_Discovery_Report |
| roadmaps/ | What's next | FooFoo_Project_Roadmap |
| visuals/ | Interactive RE pipeline explainers | RE-Visual-01_Pipeline_Explorer |

**Repository status (as of 2026-07-14):** CERTIFIED GREEN — see
`project-history/certificates/[ACTIVE]_REPO-CERT-006_Repository_Green_Certification_v1.0.md`.
The Repository Recovery Program (WP-5A → WP-5G) is complete; the Repository Gate is PASSED.
Next gate: Data Gate (Seed Engineering).

_The two gaps previously listed here are resolved and this note is corrected accordingly:_
- ~~Migrations 001-019 have no rollback files~~ → **Resolved (WP-5C).** All 29 migrations
  (001–029) have a paired rollback; the 001→029 build and 029→001 teardown are execution-proven
  (REPO-CERT-003 / REPO-CERT-006).
- ~~WP-4B and WP-4DB have design documents only, no execution certificates~~ → **Superseded.**
  No WP-4B/4DB-specific certificate was ever produced, but the seed load (100–102) and validation
  (900–904) they would have certified are now executed and certified via the WP-5F2 clean-room
  (REPO-CERT-003) and the GREEN certification (REPO-CERT-006).

**Remaining documented (non-blocking) maintenance** — per WP-5G §2, none affects rebuild/rollback:
- 9 legacy `Copy of _ACTIVE__…` filenames pending Founder-authorized normalization
  (tracked in `governance/[ACTIVE]_Repository_Naming_Exception_Register_v1.0.md`).
- Validation-script cleanup (900 Check 2 vacuous; Check 3/5 and 901 Test 1 stale) — WP-04DA scope.
- Production Operational Overlay (`rls_auto_enable`/`ensure_rls`, Option B) intentionally excluded —
  see `project-history/work-packages/[ACTIVE]_WP-5D_Production_Parity_Completion_v1.0.md`.
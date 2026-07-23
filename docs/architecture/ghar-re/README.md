# Ghar RE v1.0 — Canonical Specification Set

The authoritative, FROZEN specifications the recommendation engine is built against. Moved here
from `docs/temp/` for permanent reference. Filenames are preserved (not renamed to the repository
naming standard) because the codebase cites them by these exact names in comments (e.g. "Core
Spine §S2", "KB §R3") and bulk-renaming requires explicit Founder authorization.

| File | Role | Status |
|---|---|---|
| `ghar_re_v1_0_core_spine_FROZEN.md` | Core scoring spine (§S1 feature space, §S2 filters+BASE, §S3 Q15 gain, §S4 pairing/assemble-7) | FROZEN |
| `ghar_re_v1_0_derivation_D1_D7_FROZEN.md` | Household intelligence layer D1–D7 (raw Q1–Q15 → θ) | FROZEN |
| `ghar_knowledge_base_v0_2.md` | Knowledge Base — parameter VALUES the frozen spine reads (structure frozen, cells living) | FROZEN structure / working data |
| `ghar_re_v1_derivation_layer_reconciled.md` | Rationale/reasoning behind D1–D7 (superseded for implementation by the FROZEN version) | Reference |
| `Final_RE_-_Markdown_File.md` | Research: weather, pairing guardrails, carb defaults, modes, deferred register | Research |
| `Ghar_RE_Project_Context_and_Mission_v1_0.md` | Project context & mission | Reference |

**Implemented by:** `ghar_re_core/` (the domain package — the one tested implementation of this
math) and hosted by `ghar_re_service/` (the FastAPI service). See also RE-DOC-10 (Production
Implementation Plan) and RE-DOC-11 (Extensibility Review).

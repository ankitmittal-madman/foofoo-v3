# [ACTIVE]_Batch2_Discovery_Report_v1.1

**Supersedes:** `Batch2_Discovery_Report_v1.0` (all content inherited unchanged except the three targeted items below)
**Status:** APPROVED — ACTIVE — FROZEN

## Revision Summary (v1.0 → v1.1) — targeted only, per Task 1

1. **DQ IDs renamed** to the permanent convention: `DQ-B2-01/02/03` → **`B2-DQ-001/002/003`**.
2. **Duplicate classification strengthened** on `B2-DQ-001` (was `DQ-B2-01`) — see below. Classification uses the six permanent categories (True / Intentional / Language / Version-Patch / Alias / Unknown duplicate).
3. **Batch vs. cumulative metrics separated** — §9 of v1.0 reported Batch-2-only numbers without saying so explicitly; this revision adds one line making that scope explicit and pointing to `DOC-P3-11` §25 for cumulative project figures.

No other content changed. No restructuring performed.

---

## B2-DQ-001 (renamed from DQ-B2-01) — Strengthened Classification

7 duplicate/near-duplicate rows in `ingredient_aliases_v2.csv`, now classified into exactly one category each (Discovery observed and counted them; this classification step is the Canonicalization-stage judgment call the permanent rule requires — performed here, at the Canonicalization boundary, not silently in Discovery):

| Pair | Rows | Classification | Reasoning |
|---|---|---|---|
| `sesame_oil` / "til ka tel" / hindi | 137, 155 | **Version/Patch duplicate** | Fields 100% identical except `is_updated`/`last_update_date`; row 155 is a 20-05-2026 patch-batch re-insertion of row 137 |
| `spring_onion` / "hara pyaaz" / hindi | 57, 163 | **Version/Patch duplicate** | Same pattern as above |
| `vinegar` / "sirka" / hindi | 143, 161 | **Version/Patch duplicate** | Same pattern as above |
| `baby_corn` / "baby corn" — english vs. hindi | 56, 166 | **Language duplicate** | Identical alias text, genuinely different `language` tag — plausibly correct (untranslated English loanword used in Hindi speech), not an error |
| `broccoli` / "broccoli" — english vs. hindi | 55, 165 | **Language duplicate** | Same pattern |
| `mozzarella` / "mozzarella" — english vs. hindi | 106, 160 | **Language duplicate** | Same pattern |
| `noodles` / "noodles" — english vs. hindi | 81, 157 | **Language duplicate** | Same pattern |

**0 True duplicates, 0 Intentional duplicates, 0 Alias duplicates, 0 Unknown.** Every one of the 7 resolved cleanly into either Version/Patch or Language — no ambiguous case required a Founder decision at this stage.

---

## §9 Scope Note (targeted addition)

All counts and findings in this report (v1.0 content, unchanged) are **Batch 2 only**. For cumulative project-wide statistics across Batch 1 + Batch 2, see `DOC-P3-11` §25.

---

*(Sections 0–8, 10, and the Founder Approval Gate are inherited verbatim from v1.0 — not reproduced here. See v1.0 for full text.)*

---

## Regression Review

- ✅ Only the 3 targeted items above changed
- ✅ No entity, attribute, relationship, or vocabulary finding altered
- ✅ No restructuring, no new sections beyond the 2 required by Task 1
- ✅ v1.0 retained as superseded

**Status: APPROVED — ACTIVE — FROZEN.**

Founder sign-off: _______________________ Date: ___________

# [ACTIVE]_DOC-P3-12_Governance_Improvement_Backlog_v1.2

**Version:** 1.2 (supersedes v1.1)
**Date:** 2026-07-02

## Revision Summary (v1.1 → v1.2)

Per Task 5 (project checkpoint): every existing entry classified as Keep / Resolved / Merged / Future Cleanup / Rejected. **Nothing removed** — this document remains the permanent parking lot through Batch 6.

## Current Entries

| GB-ID | Title | Priority | Deferred Until | Checkpoint Classification | Reasoning |
|---|---|---|---|---|---|
| GB-001 | Visual Impact Chain renderer | Low | Post-Batch-6 review | **Keep** | Still valid, still low priority, still purely cosmetic — no new evidence changes its status |
| GB-002 | Resolution Order Kanban view | Low | Post-Batch-6 review | **Keep** | Same reasoning |
| GB-003 | Individual dishes may need true multi-cuisine tagging (one-to-many), similar to how `regional_origin` already works as a multi-valued genome dimension — currently `dishes.cuisine_id` is single-valued. | Low | No current feature requires it | **New (2026-07-17)** | Surfaced during FD-12 (`dish_combos` cuisine tie-break) investigation: several dish-combo mixed-cuisine cases trace back to individual dishes plausibly belonging to more than one cuisine, which a single-valued `cuisine_id` FK cannot express. Deferred — no current feature (scoring, variety, combo tie-break) requires multi-valued dish cuisine; noted here so it isn't rediscovered from scratch later. |

**0 Resolved, 0 Merged, 0 Future Cleanup, 0 Rejected this checkpoint** — GB-001/002 are exactly as valid and exactly as low-priority as when logged; GB-003 is a new entry, not a reclassification.

Founder sign-off: _______________________ Date: ___________

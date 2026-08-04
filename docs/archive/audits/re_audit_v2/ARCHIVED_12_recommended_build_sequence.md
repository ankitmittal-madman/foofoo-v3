# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

STATUS: ARCHIVED
Reason: Superseded by docs/active/ (2026-08-04 documentation restructure). This audit remains the evidentiary source for docs/active/CURRENT_STATUS.md, OPEN_ITEMS.md, ROADMAP.md, and LAUNCH_BLOCKERS.md.

# Recommended Build Sequence (fresh, 2026-08-04)

1. **P0-1** — trace the recommendation_events-vs-plan-persistence gap (read-only investigation, do this before anything else — it might change the priority of everything below it).
2. **P0-3** — decide the fate of the two parallel recommendation surfaces (a decision, not a build task — unblocks 3 other items at once).
3. **P0-4** — feedback UI on the active surface (depends on #2).
4. **P1-2** — explanation UI on the active surface (depends on #2; can be built alongside #3).
5. **P0-2** — DPDP export/delete UI (can run in parallel with 2-4, no dependency).
6. **P1-4** — profile/preferences edit screen (natural home for #5 if not shipped standalone).
7. **P1-3** — history/past-plans view.
8. **P1-1** — leaked-password-protection toggle (trivial, do any time, no reason to wait).
9. **P1-7** — real monitoring/alerting (do before public beta — right now nothing pages anyone).
10. **P1-5** — mobile test coverage (highest value once 3-7 stabilize the surfaces being tested; don't build extensive tests against a UI about to be reworked).
11. **P1-6** — wire cosine-distance into pairing/scoring (needs a Founder-level scoring-change decision; can happen any time after that decision is made).
12. **P2 items** — data-completeness and hygiene work, ongoing, not blocking.
13. **P3 items** — deferred until real usage data (feedback volume) or real domain input (clinical/festival data) exists.
</content>

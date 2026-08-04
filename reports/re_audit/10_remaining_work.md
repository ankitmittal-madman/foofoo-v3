# Phase 10 — Remaining Work (prioritized, evidence-grounded)

Status: DRAFT (working audit output). Every item below is grounded in a specific finding from
reports 01-09; nothing here invents scope beyond what the canonical documents or this audit's own
evidence already names. Priorities: **P0** (safety/security, must-fix before any public launch or
before adding new features), **P1** (closes a real functional gap in the shipped v1 scope), **P2**
(spec-acknowledged v2/v3 work, not urgent), **P3** (hygiene/cleanup, no functional risk).

## P0 — safety, security, certification gaps

1. **Allergen hidden-derivative filtering is not safe-complete.** The Core Spine itself (report 04
   §3, report 05 §1 SP-F13) tags this `OPEN — PRE-LAUNCH`. The schema that would carry it no longer
   even exists (dropped with the rest of `ghar_re` in migration 050, report 07 §1) — this must be
   redesigned against the live `public` schema, not merely "unpaused." Concretely: define where
   hidden-derivative rows live now (e.g. a new `public.allergen_hidden_derivatives` table), populate
   known cases (hing→wheat/gluten being the canonical example named in the spine), and fold the
   result into hard filter A3. **Do not launch publicly without this.**
2. **Certify or reclassify WP-19 alias batches 2-22.** Report 06 §4: 749 of 786 committed alias rows
   have no Founder-signed execution certificate — only batch 1 (37 rows) does. Per CLAUDE.md's own
   Work Package lifecycle rule, these should not be treated as CERTIFIED until either a certificate is
   produced (if they were in fact deployed) or their status is corrected to DESIGNED.
3. **Confirm the recommendations-handler per-zone fallback.** RE-DOC-12 flagged the edge-function
   fallback as one hardcoded pan-India dish, not the per-zone set RE-DOC-10 §11 specifies; report 02
   could not re-verify whether this was fixed in the 195 commits since (it was out of the
   `ghar_re_core` file set audited this pass). This needs a direct check of
   `supabase/functions/recommendations/fallback.ts` before it can be marked closed either way.

## P1 — functional gaps in the shipped v1 scope

4. **Decide the fate of the 4 unwired research CSVs.** `ingredient_aliases_v2.csv`,
   `term_synonyms_v2.csv`, `recipes_v1.json`, `dish_images_v1.json` (report 06 §5) sit fully outside
   any ETL path. Given the naming overlap with the alias-seed work (WP-19), confirm with the Founder
   whether these were meant to feed `dish_name_synonyms` and never got wired, or are genuinely
   superseded raw material safe to archive.
5. **Orphaned-table disposition.** ~11 tables with zero app-code references (report 07 §2) — resolve
   each as either intentionally-provisioned forward work (keep, document why) or dead weight
   (archive per the hygiene-dead-code skill's own confirmation-gated process, not deleted silently).
6. **G6 pairing bug** (`pairing.py:99-110`, report 02, 09 §6) — already a tracked, Founder-level
   decision (fixing it changes golden-master scoring output), not a silent defect. Include it in the
   next scoring-review cycle rather than leaving it perpetually deferred with no decision date.
7. **Vegan/halal/no-beef dietary filters.** Report 04 §4: vegan exists as a schema value but is absent
   from the live scoring engine's diet enum; halal has no implementation anywhere; no-beef/no-pork is
   prose-only. If the product roadmap commits to serving vegan/halal households, this is a real gap,
   not merely a documentation one — needs a decision on priority, not assumed already covered.
8. **Weather/comfort-hero coverage beyond the golden sample.** Report 05 §6: comfort-hero mapping
   covers only 10 named dishes (`knowledge.py:218-227`); coverage against the full 802-810-dish
   catalogue is unverified and, per the small mapping size, likely low. This directly bears on
   whether the weather layer is actually useful once the real-catalogue cutover happens.

## P2 — spec-acknowledged v2/v3 work (deferred by the canonical docs themselves, not urgent)

9. **Real 810-dish catalogue cutover into the live scoring engine** (RE-DOC-10 §2 Phase G;
   Core Spine SP-F10). This is the single largest deferred item: the live RE runs on a 39-dish golden
   sample (report 02, 03), and the real catalogue's knowledge-layer population (full PRIOR
   region×slot×season table, full-catalogue signature scores, full-catalogue `dish_macro` nutrition,
   full-catalogue comfort-hero mapping) is explicitly named by the spine as the dedicated "Step 5"
   pass, not yet done.
10. **Activate `s_pref` personal-history learning** once real feedback density clears the FD-11 gate
    (`min_real_events: 10000`, `min_households: 500`, report 09 §3). The pipeline is built and
    honestly gated — this is a matter of waiting for real usage volume, not further engineering, but
    should be tracked as a concrete milestone rather than left silently inert indefinitely.
11. **Ingredient substitution graph** (SP-F14) and **festival calendar boost** (report 03 dim 16) —
    both explicitly tagged `OPEN`/`[later]` by the Core Spine itself; no urgency implied by any
    canonical source.
12. **Cosine-similarity/embedding cross-cuisine discovery** (SP-F6, report 03) — spec-only today; a
    genuine v2 feature, not a v1 regression.
13. **4-state evolution/confidence model, MMR variety, Never/Not-Today decay** (RE-DOC-01-05
    concepts) — these were superseded by different, evidenced mechanisms in the actually-built
    engine (report 02, 01 §B), not silently dropped. If the Founder wants the *specific* algorithms
    (MMR λ=0.7, exponential Not-Today decay) rather than their functional replacements, that is a new
    engineering decision, not a bug fix — flag as a design choice to explicitly ratify or formally
    supersede in governance, since no document currently records that spec generation 1's algorithms
    were intentionally replaced.

## P3 — hygiene / documentation cleanup

14. **Non-conforming validation filename** — `database/validation/WP-3D_Check2_Fix_Reference.sql`
    (report 07 §5) violates the naming standard; needs Founder-authorized rename, not silently fixed.
15. **Stale re_engine/ghar_re seed files** — seeds 110-121 (report 06 §2-3) target schemas that no
    longer exist; recommend a header note or archive move (Founder documentation decision).
16. **Legacy TypeScript RE code disposition** — RE-DOC-12 already surfaced that the code (not just
    the schema) may still exist on disk with no governance decision recording its retirement; this
    audit did not re-check whether the `.ts` files themselves were removed alongside the schema drop
    — worth a follow-up grep for `_shared/services/re/*.ts` before considering this fully closed.

## What this audit deliberately did NOT do (per its own no-fabrication mandate)

- Did not invent food-science, nutrition, or regional-preference data to "complete" any of the above.
- Did not fabricate execution certificates for the uncertified WP-19 batches.
- Did not attempt the allergen hidden-derivative population itself — the spine explicitly says not
  to attempt this without safety verification, and this audit has no clinical/regulatory authority to
  supply that verification.
- Did not deploy anything, run live Supabase queries, or verify Fly.io reachability — outside this
  audit's evidence base (repository state only, consistent with RE-DOC-12/13's own stated scope).

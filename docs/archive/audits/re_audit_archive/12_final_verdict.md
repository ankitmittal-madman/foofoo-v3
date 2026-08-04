STATUS: ARCHIVED
Reason: Superseded by docs/archive/audits/re_audit_v2/ (the 2026-08-04 clean-room re-audit), which is itself superseded by docs/active/. Kept for historical reference only.

# Phase 12 — Final Verdict

Status: DRAFT (working audit output). Synthesizes reports 01-11. No new evidence gathered in this
file — every number below is carried forward from a cited report.

## Quantitative verdict

| Dimension | % implemented | Basis |
|---|---|---|
| Algorithm (v1 shipped scope) | **~80%** | report 11 |
| Algorithm (spec-generation-1 concepts: MMR/4-state/decay-suppression) | **0% (deliberate replacement)** | report 11 |
| Meal Genome (literal RE-DOC-02 fields) | **0% literal / ~70% functional-equivalent** | report 03, 11 |
| Meal Genome (real-catalogue data population) | **~30%** | report 03 |
| Food Ontology / Graph | **~35%** | report 04 |
| Knowledge Layer (blended: research/weather/pairings/regional/safety/seed-quality) | **~45%** (range 10-90% depending on component, see report 11 table) | report 05, 11 |
| Database (schema hygiene/RLS/lifecycle) | **~85%** | report 07, 11 |
| Seed Data (core catalogue vs alias/legacy) | **~99% catalogue / ~5% certified aliases** | report 06, 11 |
| Research → executable config coverage | **~25%** | report 05 |
| Production Readiness (deployment + spine's own pre-launch gates) | **CORRECTED (2026-08-04): ~40-60%, not 0-20%.** Deployment is live and healthy (report 07 §6, report 11 §Deployment — this session's "nothing deployed" claim was stale). 3 of 5 spine-named gates now met (contract/CI, deployment, catalogue cutover); allergen hidden-derivative graph and full nutrition/PRIOR knowledge-population remain the real gaps. | report 07, 11 |

**Documentation-only vs executable, overall**: a large fraction of spec generation 1
(RE-DOC-01-05 — cohort matrix, MMR, 4-state model, Never/Not-Today decay) remains **documentation
only** — not because it was neglected, but because spec generation 2 (RE-DOC-10-13 / Core Spine)
superseded it with a different, evidenced design that IS executable and IS tested (93/93 passing,
report 02, 09). No governance document currently records that supersession as a decision — this is
the single biggest "silent" gap this audit surfaces, echoing the same category of finding RE-DOC-12
already made about the two-engine question.

## Highest-risk missing pieces (ranked)

1. **Allergen hidden-derivative filtering** (P0, safety) — the Core Spine's own words: allergen
   filtering "is not safe-complete" without it. The schema that would carry it was dropped along
   with the rest of `ghar_re` (migration 050) and needs to be rebuilt against `public`, not merely
   re-enabled.
2. **Real 810-dish catalogue cutover into the live scoring engine** — the entire knowledge layer
   (PRIOR table, full signature scores, full nutrition vector, full comfort-hero mapping) is
   authored for a 39-dish golden sample only. Every genome/ontology/knowledge percentage above is
   capped by this single fact.
3. **Uncertified alias-seed batches (2-22, 749 rows)** — a governance/proof gap, not necessarily a
   data gap, but per CLAUDE.md's own rule these cannot currently be called COMPLETED.
4. **No governance record of the spec-generation-1 → spec-generation-2 pivot** — MMR, the 4-state
   model, and Never/Not-Today decay are absent from the live engine with no Founder Decision Register
   entry saying this was intended. Same category of gap as the (already-resolved-by-schema-drop)
   two-engine finding RE-DOC-12 made.
5. **Personal-history learning (`s_pref`) is built but permanently off** without a tracked milestone
   for when the FD-11 density gate (10,000 real events / 500 households) will be checked again.

## What should be completed before adding any new features

In order: (1) resolve the allergen hidden-derivative gap — this is the one item every canonical
source calls a hard pre-launch blocker; (2) get a Founder decision recorded on the
spec-generation-1→2 pivot, so this stops being a silent discrepancy every future audit has to
rediscover; (3) certify or reclassify the WP-19 batches 2-22; (4) plan the real-catalogue cutover
(Phase G) as its own tracked work package, since it is the single dependency almost every other
"partial"/"unverified" finding in this audit traces back to. Everything in report 10's P2/P3 lists
can reasonably wait.

## Prioritized implementation roadmap (P0-P3)

**P0 — before any public launch:**
- Rebuild and populate allergen hidden-derivative filtering against the live `public` schema.
- Verify/fix the recommendations-handler per-zone fallback (unconfirmed status, report 02).
- Certify (or formally reclassify to DESIGNED) WP-19 alias batches 2-22.

**P1 — closes real v1-scope gaps:**
- Decide disposition of the 4 unwired research CSVs (aliases/synonyms/recipes/images).
- Resolve ~11 orphaned tables (archive or document intentional provisioning).
- Make a Founder-level call on the G6 pairing bug (fix now vs. formally re-defer with a date).
- Decide whether vegan/halal/no-beef support is in scope for near-term launch; if yes, this is
  unbuilt, not partially built.
- Assess comfort-hero/weather coverage needs once the real-catalogue cutover is scoped (currently
  only 10 named dishes covered).

**P2 — spec-acknowledged v2/v3, not urgent:**
- Real 810-dish catalogue cutover (Phase G) — the largest single item, feeds nearly every other gap.
- Activate `s_pref` once the FD-11 density gate clears; track this as a milestone, not an open-ended
  wait.
- Ingredient substitution graph (SP-F14), festival calendar boost, cosine/embedding cross-cuisine
  discovery (SP-F6) — all explicitly deferred by the spine itself.
- Formal ratification (or supersession) of spec-generation-1's MMR/4-state/decay-suppression
  concepts, once the Founder has weighed in per item 2 above.

**P3 — hygiene:**
- Rename/relocate the non-conforming `WP-3D_Check2_Fix_Reference.sql` validation file (Founder
  authorization required per the naming standard's bulk-rename rule).
- Header-note or archive the now-dead `re_engine`/`ghar_re` seed files (110-121).
- Confirm the legacy TypeScript RE's `.ts` files were retired alongside its schema, or flag them for
  the same disposition decision.

## Critical Self-Review

This verdict is a synthesis of reports 01-11, which are themselves each traceable to specific
file:line/count evidence gathered by four parallel evidence-gathering passes plus this session's own
direct reading of RE-DOC-01-05, RE-DOC-10-13, and the FROZEN Core Spine. No claim in this document
was fabricated; where a sub-report flagged something as unverified or unconfirmed (the edge-function
per-zone fallback status, the .ts legacy code's on-disk fate, full-catalogue tag-row population),
that uncertainty is preserved here rather than resolved by assumption. This audit did not gain live
Supabase or Fly.io access and makes no claim about the state of any deployed system — every finding
above is a repository-state finding, consistent with the scope RE-DOC-12/13 themselves already
established as this codebase's own audit convention.

## Versioning & Placement

Working audit output, `reports/re_audit/`, generated 2026-08-04. Not a governed document under the
Naming Standard (no `[STATUS]_..._vX.Y` filename applies — this is an audit report, not a spec,
runbook, or certificate). If the Founder wants this promoted into governance, it should be
re-filed under `docs/project-history/certificates/` or `docs/architecture/` with a proper header,
not left as a bare working report.

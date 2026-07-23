# Ghar RE v1.0 — Project Context & Working Mission

*Everything in this document is carried over from the FooFoo project and is non-conflicting with the 4 canonical Ghar RE documents. It exists so this new Project has the repo/infra facts, reusable data, and working discipline without re-importing anything about the old (retired) Recommendation Engine design.*

---

## 1. What this project is

FooFoo is an AI-powered meal decision assistant for Indian households — personalizes daily Breakfast/Lunch/Dinner plans based on household profile, regional food identity, dietary/religious constraints, and learned preferences. Primary persona: Meera, 32, family meal planner. Target: Indian household market, Android-first MVP.

**We are NOT starting a new application.** We are continuing inside the existing FooFoo repository to preserve authentication, UI, the Supabase project, APIs, deployment configuration, infrastructure, and Git history. **Only the Recommendation Engine is being redesigned**, per the 4 canonical Ghar RE documents already uploaded to this Project. Those documents are the sole source of truth for RE architecture — nothing else, old or new, overrides them.

## 2. What is RETIRED (do not resurrect)

The old Recommendation Engine design — 41 fixed personas, cohort-based `FinalScore` scoring, class-first candidate generation, the interaction-count weight ladder, the 4-state (DAU-based) evolution model — is fully superseded. It does not apply to this Project. If old terminology (persona, cohort, class plan, weight ladder tiers) surfaces anywhere, treat it as legacy vocabulary, not a design constraint.

## 3. Tech stack & infrastructure (unchanged, still applies)

- **Repo:** `ankitmittal-madman/foofoo-v3` on GitHub — the one active build repo. Old `apverse-labs/foofoo` and `apverse-labs/foofoo-v2` are archive only.
- **Stack:** React Native + Expo SDK 52+, Supabase (ap-south-1), Deno Edge Functions, TanStack Query, Vercel.
- **Supabase project:** `cmkswalqpmmqojwdmqbv` (named `foofoo-v3`, ap-south-1). Stale project IDs from earlier resets are defunct.
- **Architecture pattern:** DDD/hexagonal (ports and adapters) — the Recommendation Engine is a sovereign, versioned module, not a feature. This principle still holds for Ghar RE: RE logic should not leak into the app codebase; the app talks to RE only via a versioned API contract.
- **Claude Code has authenticated write access** to the repo via `.mcp.json` + token. It never commits or pushes to `main` without explicit founder approval.

## 4. Reusable data assets (data only — NOT the old schema)

These CSV/XLSX files exist and can seed parts of the new Ghar RE spec. Reuse the **data points**, not any old table structure — the new schema should be designed fresh around the 4 canonical documents.

| File | Feeds into Ghar RE… |
|---|---|
| `region_food_affinity.csv` | `PRIOR[zone][slot]` regional/comfort-hero table (§B8 of Core Spine) — the single biggest open item |
| `ingredient_aliases_v2.csv` + `term_synonyms_v2.csv` | Closes most of the ingredient alias/tokenization gaps (coriander_seeds, cumin_powder, basmati_rice, mixed_vegetables, grated_coconut, fish_fillet) |
| `dishes.xlsx` (810 dishes, classified: main ingredient, class, logic, confidence) | Head start on `hero_role` tagging (dry/liquid/single/standalone) and the `ING` ingredient-overlap block |
| `cuisines_v4.csv` / `cuisine_groups_v4.csv` | Maps onto the cuisine-distance hierarchy (§3.4 of Core Spine) |
| `dish_combos_v2.csv` / `dish_combo_items_v2.csv` | Reference for standalone/combo dish flagging |
| `tags_v4.csv` | Candidate source for Sensory-group tags (taste, texture, richness, mouthfeel, aroma) |
| `ingredients_v5.csv` | Base ingredient master — diet_type, allergen flags, Jain-compatibility, vegan flags already present |

**Known limitation carried over:** Hindi dish names don't always string-match English ingredient names in the alias tables — some dual-ingredient dishes may show only one component. Worth a pass before relying on `ING`-block distance for those dishes.

**Not solved by any existing data (build fresh):**
- Allergen hidden-derivative table (e.g. hing → wheat) — safety-critical, must be verified new
- Graded signature/iconicity scores (`sig(x)`)
- `dish_macro` real nutrition dataset (protein/fat/carbs/fibre/sodium)
- Cold-start 3×5 like-tap matrix — this is a founder decision, not a data-derivable item

## 5. Working discipline (carried over — still applies)

- **Evidence-first:** no assertion without a real command/query/read to back it. No issue closed through inference or assumption.
- **Docs win on conflict:** if existing code, database, prompts, or naming conflict with the 4 canonical Ghar RE documents, the documents win. If a requirement is genuinely missing from the documents, stop and ask — never invent architecture.
- **No mixing old and new:** never blend old RE concepts (personas, cohorts, class plans) with the new architecture, even for "compatibility."
- **Audit before code:** for any repo-touching work, the sequence is inspect → explain findings → propose exact changes → wait for approval → implement → verify → commit.
- **Claude Code discipline:** every response involving Claude Code includes a ready-to-paste prompt plus the exact list of files/artefacts it needs. Claude Code never commits/pushes to `main` without explicit approval.
- **Safety gate before public launch (non-negotiable):** the allergen hidden-derivative table and Jain hard filters must be verified complete before any public launch. This is a launch gate, not a build blocker — building can proceed in parallel.

## 6. Immediate build stance (as agreed)

Build against the 4 canonical documents as authoritative now. In parallel, run one data-population pass using the reusable CSVs above (§4). Treat the safety-critical items, the nutrition dataset, and the cold-start matrix as scheduled founder-decision items — not blockers to starting.

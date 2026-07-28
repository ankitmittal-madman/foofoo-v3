# Ghar RE v1.0 — Extensibility Review
*(Companion to: RE-DOC-10 Production Implementation Plan. Does not revisit the frozen architecture — reviews whether the implementation plan accidentally froze implementation choices where it should have frozen interfaces instead.)*

> **Scope discipline:** every item below assumes the Founder Decision (Python RE, stateless, Edge Functions own DB/auth, service boundary fixed) as permanent. Nothing here proposes changing what runs where — only what's *pluggable within* the RE, so the engine can grow for 5–10 years without the API contract or service boundary ever needing to move.

---

## Summary — priority at a glance

| # | Area | Priority | One-line fix |
|---|---|---|---|
| 3 | Project structure (domain duplication) | **Critical** | Service hosts `ghar_re/` as a dependency; never re-implements it |
| 5 | API forward/backward compatibility | **Critical** | Explicit "ignore unknown fields, additive-only" rule, documented and enforced in CI |
| 6 | Explainability payload | **Critical** | Replace 3 fixed fields with an open `contributions[]` list |
| 1 | Catalogue loading | High | `CatalogueProvider` interface; one adapter shipped now |
| 2 | Knowledge/config loading | High | `ConfigProvider` interface; one adapter shipped now |
| 7 | Scoring module protocol | High | Formal `ScoringModule` interface + registry, not ad hoc functions |
| 8 | ML integration | High | Learned modules implement the same protocol as rule modules |
| 4 | HTTP framework | Medium | Keep FastAPI; just don't let it leak past the route layer |
| 9 | Config schema evolution | Medium | Version the config object itself, independent of API version |

---

## 1. Catalogue loading

**Current design:** RE loads a build-time-baked local snapshot (JSON/parquet) directly at startup; the loading code and the in-memory catalogue structure are the same thing.

**Future risk:** every scoring/pairing module ends up reaching into "the loaded dict" directly. When you later want Postgres-direct reads, a Redis-cached layer, object storage, or a dedicated catalogue microservice, you're not swapping one function — you're auditing every call site that assumed the local-snapshot shape.

**Would freezing an interface be better?** Yes. Define a `CatalogueProvider` protocol — `load() -> CatalogueSnapshot`, plus read methods (`get_dish(id)`, `by_zone(zone)`, `by_hero_role(role)`) — and make every downstream module depend only on the returned `CatalogueSnapshot` object, never on *how* it arrived. Ship exactly one adapter now: `LocalSnapshotCatalogueProvider`, matching today's plan. A future `PostgresCatalogueProvider` or `CatalogueServiceProvider` is then a new adapter class with zero changes to derivation/scoring/pairing.

**Why it matters:** the catalogue is near-certain to outgrow a single baked-in file — real-time price/availability feeds and the deferred variant graph are already named in your own docs as future dependencies on catalogue data. Cheap to interface now; expensive to retrofit once 800+ dishes' worth of call sites assume raw-dict access.

**Priority: High.**

---

## 2. Knowledge Base / config loading

**Current design:** YAML files read directly via per-file loader functions at startup.

**Future risk:** locks "config" to mean "YAML on disk." Blocks remote config, per-experiment config (different `gamma` tables for an A/B test), or feature-flag-gated parameter sets — all plausible v2/v3 needs given your own docs already anticipate learned, per-user `gamma` cells.

**Would freezing an interface be better?** Yes, same pattern as §1. Define a `ConfigProvider` returning a single strongly-typed `EngineConfig` object (a pydantic model mirroring today's YAML shape). Ship one adapter — `YamlFileConfigProvider` — now. Scoring/derivation code depends only on `EngineConfig`, never on file paths or YAML parsing. A future `RemoteConfigProvider` or `FeatureFlagConfigProvider` slots in behind the same interface.

**Why it matters:** config is explicitly the thing meant to change *often* (your own README: "tuning = edit config, re-run"), so it's the layer most likely to need a richer source sooner rather than later.

**Priority: High.**

---

## 3. Project structure — is `ghar_re_service/` duplicating logic?

**Current design (as drafted in RE-DOC-10):** `ghar_re_service/app/{derivation,scoring,pairing}/` as newly-written modules "ported from" `ghar_re/`, with the original `ghar_re/` demoted to offline tooling.

**Is this the correct thing to freeze?** No — and this is the most important correction in this whole review. As written, this creates **two implementations of the same math**: the validated 16-test reference in `ghar_re/`, and a separately-written copy inside the service. That's precisely the "two slightly different understandings of the same logic" risk the frozen architecture's principle #1 ("recommendation mathematics exist in exactly one production implementation") exists to prevent — just recreated one layer down, inside the codebase, instead of across services.

**Recommended improvement:** `ghar_re/` (derivation, scoring, pairing, knowledge, pipeline) becomes the actual **domain package** — installed as a proper local dependency, not copied. `ghar_re_service/` becomes a **thin hosting shell only**: HTTP routing, request/response (de)serialization, provider wiring (§1/§2), health endpoints, logging. It *imports and calls* `ghar_re`, it does not reimplement it. Concretely: `ghar_re_service/pyproject.toml` declares `ghar_re` as a path dependency (or split into a small monorepo: `packages/ghar_re_core/` + `packages/ghar_re_api/`).

**Why it matters:** this is the one item worth fixing *before* Phase B starts writing code, because once two copies of `scoring.py` exist and drift even slightly, there's no longer a clean answer to "which one is correct" — exactly the failure mode your frozen decision was written to avoid.

**Priority: Critical — resolve before Phase B.**

---

## 4. HTTP framework

**Current design:** FastAPI named directly in `main.py`.

**Is that the correct thing to freeze?** Mostly yes — HTTP framework choice is not on your list of expected 5–10 year changes (unlike catalogue source or ML integration), so this doesn't need an abstraction layer for its own sake. The real risk isn't "FastAPI is wrong," it's **FastAPI leaking past the route layer** — e.g. if request-validation logic gets written as FastAPI dependency-injection functions that the domain code also relies on, or if pydantic models used for HTTP parsing double as the domain's internal types.

**Recommended improvement:** keep FastAPI, but enforce a layering rule: request/response models live in a framework-agnostic `schemas/` module (plain pydantic or dataclasses validated against `contracts/ghar-re-v1.schema.json`) with zero FastAPI imports. `main.py`'s route handlers are a thin translation layer only: parse → call `ghar_re.pipeline` → serialize. If a framework swap or a second protocol (gRPC, for a future internal vector-search service) is ever needed, only `main.py` changes.

**Why it matters:** distinguishes "the interface is the contract" (frozen) from "the framework is an implementation detail" (swappable) — the whole point of this review.

**Priority: Medium** — low regret today, but worth stating the discipline explicitly while the codebase is small enough that it's free.

---

## 5. API evolution — request/response forward/backward compatibility

**Current design:** URL-path versioning (`/v1/`) exists, but no explicit rule governs what happens *within* v1 as fields are added over time.

**Future risk:** without a stated rule, the natural failure mode is someone adding a field under time pressure, both sides quietly agreeing to deploy in lockstep "just this once," and that habit becoming permanent — silently reintroducing the tight coupling the two-runtime split was supposed to avoid.

**Recommended improvement — codify explicit compatibility rules, not just the versioning mechanism:**
1. Both sides configure schema validation in **additive/open mode** — unknown fields are ignored, never rejected.
2. New fields are **always optional**, with a sensible default assumed by older clients.
3. **Never repurpose or change the meaning of an existing field** — add a new one and deprecate the old one over a documented window instead.
4. Only a genuinely breaking change (removing a field, changing a type, changing meaning) bumps the URL version to `/v2/`, and both versions run concurrently during migration.

**Why it matters:** this is the actual mechanism — not just the URL prefix — that lets the engine grow (new score terms, personalization metadata, future explainability fields) for years without forcing synchronized deploys across the two services.

**Priority: Critical** — decide the rule before the first field ever gets added, not after.

---

## 6. Explainability payload

**Current design:** `score_breakdown: { base, gain_q15, pairing_compat }` — three hardcoded named fields.

**Is this the correct thing to freeze?** No — this is the clearest single case in the whole review of freezing an implementation choice instead of a contract. Your own Core Spine doc already commits internally to `BASE = Σ_k W_k · conf_k · m_k(x)`, an **open, registrable set of modules** — "new rules are added by registering a new module + its weight, never by editing the existing equation." A fixed 3-field struct at the *wire* level directly contradicts that principle at the *API* level: every new scoring module (a personalization term, a negative-prior demotion, an ML-inferred adjustment) would require a schema change and a client update, exactly what the internal design was built to avoid.

**Recommended improvement:** replace the fixed struct with an open list:
```json
"contributions": [
  { "module": "m_palette", "value": 0.82, "weight": 1.00, "confidence": 1.0 },
  { "module": "m_weather", "value": 0.40, "weight": 0.40, "confidence": 1.0 },
  { "module": "s_pref",    "value": 0.15, "weight": 1.00, "confidence": 0.6 }
]
```
Keep a small number of stable top-level aggregates (`base_total`, `gain_multiplier`, `final_score`) as named fields, since those are genuine architectural concepts — everything module-level goes in the open list. New modules append; nothing upstream needs to change.

**Why it matters:** this maps the internal module contract directly onto the wire format, at essentially zero extra cost now, and is exactly the kind of choice that's expensive once real clients have hardcoded three field names.

**Priority: Critical.**

---

## 7. Plugin / module architecture inside the engine

**Current design:** modules are described conceptually (a function of dish/profile/context) but no formal interface or registry exists yet.

**Recommended improvement:** define a `ScoringModule` protocol with one method: `score(dish, profile, context) -> ModuleResult`, where `ModuleResult = { value, confidence, metadata, explanation }`. Maintain a simple ordered registry (module instances + config-driven weights) that BASE composition iterates over. Adding a new signal becomes "append to the registry + add a weight to config" — never touching the composition loop, and it's the same shape §6 needs on the wire.

**Why it matters:** turns "the equation's form is invariant across versions" (your own Core Spine design principle) from a documentation promise into something the type system actually enforces.

**Priority: High.**

---

## 8. ML integration

**Current design:** "training offline, inference inside the RE" is stated as a principle, but nothing yet specifies how a learned module plugs into the same call path as a rule-based one.

**Recommended improvement:** because of the `ScoringModule` protocol in §7, a learned module (an embedding-similarity term, `S_pref`, a future ranking model) implements the **identical** protocol — the registry doesn't need to know or care whether a module is a hand-authored formula or a loaded model artifact. Treat model artifacts the same way as catalogue/config (§1/§2): versioned, immutable, loaded at startup through a `ModelArtifactProvider`. Retraining and redeploying a model becomes a deploy, not a code change.

**Why it matters:** avoids a scramble later to retrofit ML modules into code that assumed only formulas — and costs nothing extra, since it's the same interface shape §7 already needs for ordinary rule modules.

**Priority: High.**

---

## 9. Configuration evolution

**Current design:** `config_version` is already tracked as a string — good — but nothing states how the config's *schema* itself grows (a 5th Q15 objective, a whole new YAML file for an experimentation layer).

**Recommended improvement:** version the `EngineConfig` object itself (from §2), validated at load with its own internal version field, and treat config-schema evolution as an axis independent of API version — new optional config sections shouldn't require an API version bump, matching the "three independent version axes" principle the frozen plan already established for API/engine/config generally, just applied specifically to config's own internal shape.

**Why it matters:** config is the layer expected to change most frequently — it deserves the lowest-friction, safest path to grow.

**Priority: Medium.**

---

## What NOT to over-build (avoiding premature abstraction)

Per the review's own instruction — these interfaces should be **defined now, with exactly one adapter each**, not accompanied by speculative infrastructure nobody needs yet:
- No plugin marketplace or dynamic/runtime module loading — a static, code-reviewed registry is enough for years.
- No second `CatalogueProvider` or `ConfigProvider` implementation until a real second need appears (YAGNI still applies to the *adapters*, even while the *interface* is worth fixing now).
- No generic feature-flag service — the `ConfigProvider` interface leaves room for one later; don't build it speculatively.
- Don't abstract the HTTP framework itself (§4) — only the layering discipline around it.

---

## Net effect

Fixing §3 and §6 before Phase B starts, and codifying §5's compatibility rule in the same PR that defines the schema, are the three changes that most determine whether this engine can grow for a decade without a rewrite. §1/§2/§7/§8 are the same pattern (provider/protocol interfaces, one adapter each) applied consistently, and are cheap precisely because they're being decided before any code depends on the wrong shape.

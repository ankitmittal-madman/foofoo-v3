# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# [DRAFT]_WP-8G_Recommendation_Variety_on_Refresh_v1.0

**Status:** DRAFT — proposed, not built. No code, contract, or service change has been made yet.
**Version:** v1.0
**Date:** 2026-08-02
**Placement:** docs/archive/implementation/work-packages/ARCHIVED_WP-8G_Recommendation_Variety_on_Refresh_v1.0.md
**Builds on:** WP-8D RE Core (REPO-CERT-014), WP-8E RE Integration Layer (REPO-CERT-015).
**Governance basis (frozen, consumed not modified):** contracts/ghar-re-v1.schema.json (single source of truth, backend-ci.yml contract-check job), RE-DOC-10 §9/§11 (frozen architecture: Edge Functions own auth/DB, the RE owns math; no second translation layer), RE-DOC-11 §6 (pass plates[]/contributions[] through as-is).

---

## Executive Summary

**The problem (confirmed live, not assumed):** pressing "Refresh" on the recommendations screen calls `POST /v1/recommendations` again, but returns the **identical** plates every time. Verified against live traffic: 9 consecutive successful calls for the same household (`recommendation_events`, profile `52ade0e4-...`, 2026-08-02 03:07:15–03:10:39 UTC) — every call `outcome = success`, no errors. This is not a bug in the sense of something broken; it is Phase 1's documented, deliberate scope ("proves the wire, not the UI" — `mobile/app/recommendations.tsx`'s own doc comment) meeting a real user expectation that "Refresh" should show something different.

**Why it's like this (three confirmed, independent facts):**
1. `mobile/src/api/recommendations.ts`'s `postRecommendations()` sends no context overrides — every call uses the server's fixed `DEFAULT_CONTEXT` (dinner, monsoon, Thursday).
2. The live recommendation engine (`ghar_re_core`, deployed on Fly.io as `ghar_re_service`) is **fully deterministic** — grepped `pipeline.py`/`scoring.py`/`engine.py`/`schemas.py` for `seed`/`random`/`shuffle`: no match anywhere. Same household + same context + same catalogue always produces the same top-N list.
3. `contracts/ghar-re-v1.schema.json` (the one schema both `recommendations/contract.ts` and `ghar_re_service/schemas.py` read — enforced by `backend-ci.yml`'s `contract-check` job) has **no field** for excluding already-served dishes or varying the result run-to-run.

**Why this is a real work package, not a quick patch:** `recommendations/handler.ts` states its own architecture rule explicitly in its doc comment — *"Pass through plates[]/contributions[] AS-IS (RE-DOC-11 §6) — no second translation layer."* Faking variety by re-ranking or filtering the RE's response inside the Edge Function would silently violate that documented, deliberate boundary (the RE owns recommendation math; Edge Functions do not). A real fix therefore touches the shared contract and the Fly.io service, not just the Edge Function — which needs its own scoped design, review, and a coordinated redeploy, not an incidental fix bundled into an unrelated debugging session.

This WP is **DESIGNED only**. It proposes the shape of a fix; it does not implement one. Per this repo's Work Package lifecycle rule, its Status may only move to COMPLETED once a companion certificate exists in `docs/project-history/certificates/` with real execution output.

---

## 1. Proposed approach (for review, not yet approved)

Two independent options, not mutually exclusive:

**A. Server-side exclusion (the "real" fix — touches the frozen contract):**
- Add an optional `exclude_dish_ids: string[]` field to `contracts/ghar-re-v1.schema.json`'s request shape.
- `ghar_re_service` (`ghar_re_core/pipeline.py` / `scoring.py`) filters those ids out of the eligible candidate pool before scoring — the RE still owns all recommendation math; nothing moves to the Edge Function.
- `recommendations/compose.ts`/`handler.ts` populates `exclude_dish_ids` from the household's own `recommendation_events.plates` history (e.g. the last N served dish ids, already recorded — no new storage needed).
- Requires: contract change reviewed on both sides (per `backend-ci.yml`'s contract-check job, which already guards "both sides reference the shared file"), a `ghar_re_service` code change, and a **Fly.io redeploy** — out of scope for an Edge-Function-only session.

**B. Context-driven variety (no contract change, smaller scope):**
- `recommendations/handler.ts` already accepts a client-supplied `context` override (`body.context`, line ~106) that legitimately changes results *because it changes the actual request* (different slot/season/weekday) — not a workaround, an existing documented capability the mobile client simply never uses.
- Mobile could let "Refresh" cycle a meaningful, user-visible context dimension (e.g. slot) rather than silently faking variety — this changes what's being asked for, not the answer to the same question, so it doesn't touch RE-DOC-11 §6 at all.
- Scope: mobile-only, no contract/service change, but only produces variety across the dimensions a user would actually expect to vary (needs product input on whether "refresh" should mean "show me something different for the same ask" vs. "show me a different meal").

## 2. Recommendation

Option A is the correct fix for what "Refresh" is supposed to mean (new options for the *same* ask), but is real cross-service work: contract change + `ghar_re_service` update + Fly.io redeploy + updated `re_integration.test.ts`/`re_core.test.ts` coverage. Recommend scoping it as its own certified work package once prioritized, following WP-8E's precedent (schema change reviewed under `backend-ci.yml`'s `contract-check` job before any code change).

Option B could ship sooner but changes user-facing semantics of "Refresh" and needs a product decision, not just an engineering one.

## 3. Explicitly out of scope for this WP

- No code, schema, or service changes are included in this document.
- No Fly.io redeploy has been performed or scheduled.
- Does not touch `_shared/services/re/variety.ts`'s MMR/variety-window logic — that module is part of the **retired** local TypeScript RE (confirmed off the live path; `recommendations/handler.ts` calls `re-client.ts` → the Fly.io service, not `_shared/services/re/engine.ts`) and is not a precedent to extend here.

## 4. Critical Self-Review

- This WP was written directly from live evidence (`recommendation_events` query, grep of the RE's own source, the contract schema, and the handler's own doc comments) — not from assumption or memory of how recommendation engines "usually" work.
- The determinism claim rests on an absence-of-match grep (`seed`/`random`/`shuffle`) across the relevant Python files; this is a reasonably strong but not exhaustive check — a live A/B call with identical inputs was not performed to double-confirm determinism, since the 9 identical-outcome calls in `recommendation_events` already serve as that empirical confirmation.
- No estimate of engineering effort/timeline is given, since Fly.io deployment mechanics for this project were not verified as part of this WP.

## 5. Versioning & Placement

v1.0 — initial draft. Placement follows the Folder Structure rule (`docs/project-history/work-packages/`, proposed engineering work, DESIGNED until certified). No prior version exists to supersede.

## Founder Sign-off


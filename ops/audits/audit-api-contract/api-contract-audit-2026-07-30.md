# API Contract Audit — 2026-07-30

Report-only run. No fixes applied.

**Repo state:** branch `claude/foofoo-skills-dotfiles-e93096`, commit `e7bb584`

## Contract baseline doc

`docs/architecture/[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md` exists and was read
(Sections 03, 05, 05.1, 06.1–06.5, 07, 18.2, 18.4). Treated as stated intent; compared against
both the backend's actual code and the mobile client's actual code.

## Contract pairs discovered

Backend handlers (`supabase/functions/*/handler.ts`): `consent`, `household`, `recommendations`.
Client call sites: `mobile/src/api/client.ts` (`apiPost` — shared fetch wrapper), invoked from
`mobile/src/api/household.ts` (`postHousehold`) and `mobile/src/api/recommendations.ts`
(`postRecommendations`), which are in turn called from `mobile/app/create-id.tsx`,
`mobile/app/(onboarding)/step-5.tsx`, and `mobile/app/recommendations.tsx`.

| # | Backend handler | Client caller | Paired? |
|---|---|---|---|
| 1 | `consent/handler.ts` (`POST /v1/consent`) | **none found** | **Orphaned** |
| 2 | `household/handler.ts` (`POST /v1/household`) | `postHousehold()` — `create-id.tsx`, `step-5.tsx` | Paired |
| 3 | `recommendations/handler.ts` (`POST /v1/recommendations`) | `postRecommendations()` — `recommendations.tsx` | Paired |

**Contract pairs checked: 2. Orphaned handlers: 1** (`consent`).

`consent` is not called by cron or any other service in this repo either (`grep -rl` for
`/consent`, `postConsent`, or equivalent across `mobile/` and `supabase/functions/` returns
nothing outside the function's own source) — it is a fully-built, fully-tested backend endpoint
with **zero live callers**, mobile or otherwise, in this repository.

## Household field-shape comparison (`household/schema.ts` vs `mobile/src/api/types.ts` + `toHouseholdWrite.ts`)

- `ProfileQuestionKey` (10 values) and `HouseholdAnswerQuestionKey` (9 values) in
  `mobile/src/api/types.ts` match `PROFILE_SCHEMAS`/`HOUSEHOLD_ANSWERS_SCHEMAS` keys in
  `household/schema.ts` **exactly**, field for field.
- `MemberWrite` (client) and `memberEnvelope` (server) match exactly:
  `id, member_name, conditions, allergen_flags, diet_type, is_active`.
- `HouseholdWriteResponse` (client) matches the object `household/handler.ts` actually returns via
  `jsonContract(...)` exactly: `household_id, profile_exists, profile_created, answers_recorded,
  missing_required_fields, members_written` (+ `trace_id`, added additively by `jsonContract`).
- Enum value mappings in `toHouseholdWrite.ts` were cross-checked against the live CHECK-constraint
  vocabularies in `schema.ts` (diet type, who-cooks, objective) — all map to values inside the
  server's accepted enums. No renamed/removed field found on either side. **No drift found in this pair.**

**Finding (LOW, not contract drift but worth flagging) — allergen bitfield coverage gap.**
Backend `compose.ts`'s `ALLERGEN_BITS` defines 7 bits: `nuts(1), dairy(2), gluten(4), shellfish(8),
egg(16), soy(32), sesame(64)`. The client's `toHouseholdWrite.ts` `ALLERGEN_BITS` map only defines
6: `peanuts(1), dairy(2), gluten(4), shellfish(8), soy(32), sesame(64)` — **bit 16 (`egg`) has no
UI option at all**, so a user with an egg allergy has no way to set that flag through the app today.
Both sides agree on what each bit *means* (no renamed/mismatched semantics — this is not a shape
drift), but the client under-uses the backend's own allergen model. Given allergens are
safety-relevant (feeds directly into the RE's hard-constraint filtering), flagging this above LOW
for product/Founder attention even though it isn't a contract-shape bug.

## Recommendations field-shape comparison (`recommendations/contract.ts`, `ghar-re-v1.schema.json` vs `mobile/src/api/types.ts`)

- Client `Plate` interface (`plate_id, form, hero_dish_ids, hero_dish_names, support, is_standalone,
  plate_score, base_total, gain_multiplier, final_score, contributions`) matches the server's
  passthrough response body (`recommendations/handler.ts` forwards the RE's `result.body` as-is,
  contract-validated via `contract.ts`'s Ajv check against `ghar-re-v1.schema.json`) field for
  field. `Contribution { module, value, weight, confidence }` also matches.
- `RecommendationsResponse` client type includes `request_id, api_version, engine_version,
  config_version, plates, warnings, trace_id` — all present in both the real RE-served response
  shape and `fallback.ts`'s `buildFallbackResponse()` shape. **No drift found in this pair.**
- Client sends `{ household_id?, request_id?, context? }` (`RecommendationsRequest`); server accepts
  exactly these three optional fields off the request body (`handler.ts`) before building its own
  `payload` server-side via `compose.ts`. No unrecognized/unused field on either side.

## Error-handling comparison

- Client's `ApiError` construction in `client.ts` reads `json?.error?.message` and `res.status`,
  matching the server's `AppError.toClientJSON()` envelope (`{ error: { code, message, retriable,
  trace_id, context? } }`) exactly in shape.
- **Gap (MEDIUM, "unhandled status code" category):** the client never reads `error.code`. Every
  non-2xx response — 401 `ERR_UNAUTHENTICATED`, 403 `ERR_OWNERSHIP_MISMATCH`, 409
  `ERR_ONBOARDING_ALREADY_COMPLETE`, 422 `ERR_HOUSEHOLD_FIELD_INVALID`/`ERR_HOUSEHOLD_INCOMPLETE`,
  500 `INTERNAL` — is handled identically: thrown as a generic `ApiError` and rendered as a plain
  message string (`step-5.tsx`, `create-id.tsx`, `recommendations.tsx` all just show
  `error.message`). This is not a shape drift (the envelope itself is correctly parsed both sides),
  but it means the app has no differentiated UX for, e.g., a 409 on retrying onboarding (should
  probably route the user forward, not show an error) versus a genuine validation failure. Flagged
  per the skill's own category table ("Unhandled status code" → MEDIUM), since the backend can
  return codes the client's UI logic doesn't distinguish.
- `recommendations/handler.ts` is designed to **always** return 200 (RE failures degrade to a
  fallback plate, per DOC-P3-06 §07/RE-DOC-01 §05) — the client's `recommendations.tsx` comment
  correctly reflects this ("no recommendation-failed case to design for"). Client and backend agree
  here.

## Drift findings table

| Endpoint | Client file | Drift type | Severity | Detail |
|---|---|---|---|---|
| `/v1/consent` | — (none) | Orphaned handler, no client caller in this repo | **flagged, not classified as drift** | Fully built backend endpoint with zero live callers; see note below on downstream consequence |
| `/v1/household` | `toHouseholdWrite.ts` | Incomplete field coverage (not a shape mismatch) | LOW (safety-relevant) | Client has no UI path to set the backend's `egg` allergen bit (16) |
| `/v1/household`, `/v1/recommendations` | `client.ts` | Unhandled status code differentiation | MEDIUM | Client never branches on `error.code`; every error status renders identically |

No CRITICAL or HIGH shape-level drift (renamed/removed/type-mismatched fields) was found between
the backend's actual returned/accepted shapes and the client's actual sent/read fields, for either
of the two paired endpoints.

## Cross-reference to the edge-function audit (same session)

The orphaned `/v1/consent` handler is not an isolated observation — the edge-function audit
(`ops/audits/audit-edge-functions/edge-function-audit.md`, same session) independently found that
the deployed onboarding write path (`household/`) never checks personalization consent, and that
the documented `/v1/onboarding` contract endpoint (which *would* enforce that consent gate via
`OnboardingOrchestrator`) has no deployed Edge Function at all. Combined: consent is documented as
a hard precondition (DOC-09 §03), fully implemented as an endpoint, but currently unreachable from
the client and unchecked by the endpoint that would need it — the DPDP consent gate has no
enforcement point anywhere in the live request path today. Recommend Founder review before this
reaches production, not a silent fix in either audit.

## Completion summary

```
Contract baseline doc found: Yes (DOC-P3-06 v1.2)
Contract pairs checked: 2 (household, recommendations)
Orphaned handlers flagged: 1 (consent)
CRITICAL drift found: 0
HIGH drift found: 0
MEDIUM drift found: 1 (unhandled status-code differentiation)
LOW drift found: 1 (allergen bitfield coverage gap)
Typecheck: not run (report-only; no fixes applied to verify)
Tests: not run (report-only; no fixes applied to verify)
```

No code was changed as part of this audit.

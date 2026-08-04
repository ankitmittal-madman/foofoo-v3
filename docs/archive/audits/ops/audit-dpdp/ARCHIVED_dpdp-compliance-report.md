# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# DPDP Legal Compliance Audit

**REPORT ONLY. No code, data, or configuration was changed. Every finding below is a recommendation for human/legal review — not an instruction that was or should be auto-applied.**

FooFoo ("Ghar" branding) is an India-market household meal-recommendation app collecting health/dietary/household-composition data — DPDP Act 2023 applicability is real, not hypothetical, and the project's own security architecture doc already says so explicitly.

## ⚠️ Findings requiring legal counsel input, not just engineering action
Findings 1 and 2 below are launch-blocking per the project's own documentation (`DOC-09 §01`) and should go to legal/Founder review before any public launch, not be silently patched.

## Step 1 — Sensitive data classification (discovered, not assumed)
The project has **already done this classification itself** — found in `docs/architecture/[ACTIVE]_DOC-P3-07_Security_Architecture_v1.2.md` §13 (Data Classification, "synthesized here for the first time" from DOC-P3-04 + DOC-09):

| Class | Columns/tables | Existing protection |
|---|---|---|
| Personal identifying | `profiles` (name, home_state, city) | RLS owner-only; DPDP export/delete scope |
| **Health/dietary (sensitive — separate consent required)** | `diet_type`, `religious_pref`, `allergen_flags`, `household_members` (which includes `conditions` — e.g. `diabetic_member`, `pregnant_member`, `elderly_member`, `hypertension_heart_member`) | RLS owner-only; separate `personalization` consent gate |
| Behavioral/interaction | `interaction_events`, `suggestion_logs`, `context_log` | RLS owner-only, append-only, 2-year retention ceiling (per doc) |
| Compliance/audit | `consent_records`, `audit_log` | Append-only, retained independent of account deletion |

`household_members.conditions` and `profiles.religious_pref` are DPDP-sensitive categories (health data, religious affiliation) confirmed against the live schema (migration `033_household_members_conditions_vocabulary.sql`, `005_profiles.sql`). This audit adopts the project's own classification rather than re-deriving one, consistent with the skill's own preference for an existing security doc as source of truth.

## Step 2 — Third-party services discovered
**None found.** No `package.json` reference to PostHog/Sentry/Mixpanel/Amplitude/Segment/Firebase Analytics/Datadog, and no `.track(`/`.capture(`/`captureException(`/`.identify(` call sites anywhere in the codebase. This is a genuinely clean result, not an unsearched gap — the codebase does its own structured logging (`_shared/logging/userJourney.ts`, system logger) rather than sending events to a third party.

## RISK 1 — Sensitive data in third-party payloads
**No findings — not applicable.** With zero third-party analytics/error-tracking integrations in the codebase today, there is no current leak vector. **Forward-looking note:** the security doc itself (§section on operational logs, line ~433) already states a rule — "never log a raw request body containing dietary/health fields... in a way that would defeat schema-level lockdown" — so if/when an analytics or crash-reporting SDK is added later, this exact check should be re-run before that integration ships, not assumed still-clean.

## RISK 2 — Consent flow completeness
`consent_records` table exists (migration `013`/schema confirmed live), append-only, one row per consent decision with `consent_type` (`personalization`/`analytics`/`push_notifications`/`data_retention`), `granted`, `granted_at`, `privacy_policy_version`. Recorded via `POST /v1/consent` → `consent-repository.ts` (service-role insert only — by design, per the repository's own doc comment: "the table is append-only... every consent action inserts a new row").

- **Recorded at signup?** Consent capture exists as a first-class endpoint gating onboarding (security doc §07/§19: "no onboarding data collection before personalization consent is recorded"), but this audit found no code path that *forces* the call before other onboarding writes — that enforcement is stated as an architectural requirement, not something this audit could verify is actually wired into the onboarding flow's sequencing (would need `audit-onboarding-funnel` or a full flow trace to confirm, which is out of this skill's scope).
- **Version/timestamp tracked?** Yes — `privacy_policy_version` and `granted_at` are both present and populated (append-only design correctly gives a full history, not just a boolean).
- **Can the user view what consent was given?** Only indirectly: `consent_select_own` RLS policy lets a user `SELECT` their own `consent_records` rows directly from the table, but there is **no dedicated GET/read endpoint** — `consent/handler.ts` only implements `POST` (explicitly rejects all other methods with `METHOD_NOT_ALLOWED`). Functional, but a raw-table-read is a thin way to satisfy "view consent" and isn't documented as the intended UX path.
- **Can the user withdraw consent?** Implicitly yes — re-`POST`ing with `granted: false` records a new row superseding the prior grant (consistent with the append-only design) — but there is no dedicated withdrawal endpoint or confirmation flow either.

**Finding — MEDIUM:** consent view/withdrawal both work only as side-effects of the existing SELECT policy and re-POST semantics, not as first-class, documented capabilities. Recommend confirming with the mobile client team whether this is surfaced in the actual UI, or whether users have no visible way today to see/change past consent.

## RISK 3 — Data subject rights implementation

### A. Data export
`docs/architecture/[ACTIVE]_DOC-P3-07_Security_Architecture_v1.2.md` §19 states: `GET /v1/user/export` — "✅ Fully specified" (architecturally), required within 72h per DPDP.

**CRITICAL FINDING:** No export edge function exists in the codebase. `supabase/functions/` contains exactly three function directories: `consent/`, `household/`, `recommendations/`. There is no `user/`, `export/`, or equivalent. The requirement is fully *designed* but **not implemented** — this is a launch-blocking gap per the project's own stated pre-launch gate (`DOC-09 §01`, cited directly in the security doc).

### B. Account deletion pipeline
Same doc, same section: `POST /v1/user/delete` — "✅ Fully specified," 72h requirement, full erasure.

**CRITICAL FINDING:** No delete/erasure edge function exists either — same three-directory result as above. `profiles.deleted_at` column exists (soft-delete marker, migration `005_profiles.sql`) and is referenced by ownership-check logic ("`deleted_at IS NOT NULL` as an authorization failure state" — security doc §line 210), so the *marker* exists, but there is no discoverable code path that (a) sets it, (b) cascades/anonymizes dependent personal data, or (c) removes the auth.users row. The full erasure pipeline described in the architecture is not present in this repo.

### C. Audit log retention
`audit_log` table exists, RLS-enabled with zero client policies (service-role/internal-only — consistent with its purpose), and the security doc states it should be "retained per DPDP schedule independent of account deletion" (3-year retention per §19's table, vs. 2-year for interaction logs). No `pg_cron`/scheduled purge job was found anywhere in `supabase/functions/` or `database/migrations/` for **either** retention window — so there is currently no enforcement of the 2-year interaction-log ceiling *or* the 3-year audit-log floor. Since no purge job exists at all, the audit log is not at risk of being *incorrectly* swept into a shorter-retention job (there's no job to do that), but the flip side is that the 2-year interaction-log retention ceiling the project itself commits to is also unenforced today.

**Finding — HIGH:** No retention/purge automation exists for either `interaction_events`/`suggestion_logs` (2-year DPDP ceiling) or `audit_log` (3-year floor). Both are currently unbounded.

## Additional finding surfaced directly by the project's own security doc (not newly discovered by this audit, but load-bearing for DPDP and worth restating here)
**`AGR-P3-07-001` — OPEN, launch-blocking:** No minor/under-13 age-gate mechanism exists anywhere in the frozen architecture. The security doc marks this "Unmitigated," a direct DPDP violation, and explicitly requires Founder direction through controlled governance before this can be closed. Flagging again here because it is squarely a DPDP data-subject-rights/consent-capacity issue and should be reviewed alongside Findings 1-3 above, together, by legal counsel — not resolved piecemeal.

## Summary table

| Risk | Finding | Severity | Recommended action | Status |
|---|---|---|---|---|
| RISK 1 | No third-party analytics/error-tracking integrated — no current leak vector | INFO | Re-run this check before adding any analytics/crash-reporting SDK | NEEDS USER REVIEW |
| RISK 2 | Consent view/withdrawal work only as side effects of RLS SELECT + re-POST, not first-class endpoints | MEDIUM | Confirm actual UI coverage with mobile team; consider a dedicated `GET`/`DELETE` consent endpoint | NEEDS USER REVIEW |
| RISK 3A | `GET /v1/user/export` designed but not implemented anywhere in `supabase/functions/` | **CRITICAL** | Implement before public launch — DPDP requires export within 72h | NEEDS LEGAL REVIEW |
| RISK 3B | `POST /v1/user/delete` designed but not implemented; `deleted_at` marker exists with no erasure pipeline behind it | **CRITICAL** | Implement before public launch — DPDP requires deletion/erasure within 72h | NEEDS LEGAL REVIEW |
| RISK 3C | No retention/purge automation for either the 2-year interaction-log ceiling or the 3-year audit-log floor | HIGH | Build a scheduled purge job before launch; both windows are currently unbounded | NEEDS LEGAL REVIEW |
| (restated) | AGR-P3-07-001 — no minor/age-gate mechanism, OPEN per the project's own security doc | **CRITICAL** | Founder + legal decision required; currently zero remediation path | NEEDS LEGAL REVIEW |

## Audit completed 2026-07-30
Sensitive fields confirmed: 4 columns/tables (adopted from project's own DOC-P3-07 classification)
Third-party services checked: 0 found (clean)
RISK 1 findings: 0 (CRITICAL: 0)
RISK 2 findings: 1 (MEDIUM)
RISK 3 findings: 3 (CRITICAL: 2, HIGH: 1)
NOTE: No fixes were applied. All findings require user/legal review, per this skill's hard "report only, never auto-fix" rule — including on explicit request to "just fix it."

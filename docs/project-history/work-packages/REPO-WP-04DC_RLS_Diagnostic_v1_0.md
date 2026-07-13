# REPO-WP-04DC_RLS_Diagnostic_v1.0

**Repository Engineering Work Package #4DC — Row-Level Security Diagnostic (Read-Only, Self-Rolling-Back)**
**Project:** FooFoo (`apverse-labs/foofoo-v3`) · **Supabase:** `slsqtlygeekdppuyiiff`
**Placement:** `docs/project-history/REPO-WP-04DC_RLS_Diagnostic_v1_0.md`
**Date:** 2026-07-10 · **Status:** DESIGNED — awaiting Founder approval to execute
**Prerequisites:** WP-4DB's Phase B halt at `901` Test 5 (this session's evidence gathering, see below)

---

## Pre-Design Independent Evidence Gathering

WP-4DB halted because `901`'s Test 5 (privilege-enforcement proof) did not observe the expected `insufficient_privilege` error when `authenticated` attempted to `UPDATE public.dishes.diet_type`. A principal-engineer review was performed before designing this package, checking every plausible mechanism rather than accepting the first available theory.

### Critical Flaw Found in the Prior Session's Reasoning

The prior session reasoned "Poha's data didn't change, so it's probably fine." **This is invalid as evidence.** Test 5's script structure is:

```
SET ROLE authenticated;
UPDATE dishes SET diet_type='vegan' WHERE name='Poha';
RAISE EXCEPTION 'FAIL: ...';   -- unconditional if the UPDATE itself didn't error
```

The final `RAISE EXCEPTION` fires **regardless of whether the UPDATE touched 0 rows or 1 row**, and rolls back everything in its block either way. This means "Poha's `updated_at` is unchanged" would look identical whether the UPDATE silently matched zero rows (safe) or actually matched and changed one row before being rolled back moments later (unsafe). Both scenarios are indistinguishable from that observation alone — the real answer requires directly measuring the row count, not inferring it from side effects.

### Evidence Tree — Every Plausible Mechanism, Checked Live

| Mechanism | Live evidence gathered | Verdict |
|---|---|---|
| BYPASSRLS on `authenticated`/`anon` | `pg_roles`: both `rolbypassrls = false` | Ruled out — neither role can bypass RLS |
| BYPASSRLS carried over from the connecting role | `postgres`/`service_role` both have `rolbypassrls = true`, but standard Postgres semantics re-evaluate RLS-bypass against the *current* role after `SET ROLE`, not the original login role | Very likely ruled out (standard, documented behavior), not yet directly measured |
| `SET ROLE authenticated` silently failing/no-op | `pg_has_role('postgres','authenticated','MEMBER') = true` — the switch is legitimate; no error was reported at that line | Ruled out as a likely cause |
| Table ownership bypass | `dishes` is owned by `postgres`, not `authenticated` | Ruled out — no ownership relationship |
| FORCE ROW LEVEL SECURITY misconfigured | `relforcerowsecurity = false`, but this flag only affects the table *owner's* own RLS exposure, not a non-owner role like `authenticated` | Ruled out as relevant to this case |
| A hidden trigger on `dishes` intercepting the UPDATE | `pg_trigger` on `public.dishes`: zero non-internal triggers | Ruled out |
| SECURITY DEFINER effects from the derive trigger | The only derive-related trigger is on `dish_ingredients`, not `dishes` — this UPDATE targets `dishes` directly | Ruled out — not applicable |
| Column-level GRANT allowing the UPDATE to proceed syntactically at all | `information_schema.column_privileges` confirms `authenticated`/`anon` hold direct `UPDATE` on `diet_type` (already flagged, previously unresolved) | Confirmed, real, pre-existing gap — this is why no `insufficient_privilege` error was even possible |
| RLS default-deny (no UPDATE policy exists) silently filtering to 0 rows — the "expected, safe" explanation | Confirmed live: exactly one policy on `dishes` (`dishes_public_read`, command=SELECT only). No UPDATE/ALL policy exists. Standard Postgres behavior for this configuration is a silent 0-row match, no error | Plausible and consistent with everything observed — **not yet directly measured; this remains the load-bearing, unproven assumption** |
| RLS genuinely not applying for `authenticated` on this UPDATE — the "real defect" explanation | No mechanism found in this audit that would cause this | No positive evidence found, but absence of a known mechanism is not proof of absence — must still be measured directly |

**Conclusion of the review:** every specific loophole a principal engineer would suspect has been checked and ruled out. What remains is a genuine, still-unresolved two-part chain: a confirmed GRANT-level gap feeding into an RLS default-deny that *should* catch it but has never been directly measured to actually do so.

### Decision Tree

```
Run the UPDATE as 'authenticated', inside an explicitly-rolled-back transaction,
and measure ROW_COUNT directly.

                    ROW_COUNT = ?
                    /           \
                  0               1 (or more)
                  |                 |
        RLS correctly           RLS did NOT block it either
        defaulted to deny        -> REAL security defect confirmed
        -> Data was safe             -> immediate escalation required,
          throughout, despite          this becomes the top-priority
          the confirmed GRANT           repository finding
          gap being a real,
          separate issue to
          still fix later
```

---

## 1. Objective

Determine, with direct measured evidence (not inference), whether the `authenticated` role's UPDATE against `public.dishes.diet_type` affects 0 rows (RLS held) or 1+ rows (RLS did not hold) — reaching exactly one of two classifications with no ambiguity remaining.

## 2. Scope

**In scope:** one diagnostic transaction, explicitly rolled back regardless of outcome, measuring the UPDATE's affected-row-count directly.

**Out of scope:** any fix; any GRANT/REVOKE change; any policy change; any permanent data change; WP-5; re-running `902`/`903`/`904`.

## 3. Method

Execute the UPDATE as `authenticated` inside `BEGIN ... ROLLBACK` — an explicit transaction block with a deliberate, unconditional `ROLLBACK` at the end, not relying on an exception to undo it (that reliance was the flaw in the original test). Immediately after the UPDATE, capture the affected-row-count before doing anything else. Report it directly. Then roll back explicitly, and independently re-verify Poha's row afterward as a second, confirmatory check only — not the primary evidence, as it wrongly was last time.

## 4. Stop Conditions

- The transaction cannot be rolled back cleanly for any reason — halt immediately, do not proceed further
- The row count is anything other than a clean 0 or 1 (e.g., an error occurs) — report exactly what happened, do not guess

## 5. Acceptance Criteria

Exactly one of the two classifications in the Decision Tree is reached, with the measured row count as the direct, primary evidence — not inferred from side effects.

## 6. Exit Criteria

Diagnostic complete, finding classified, Execution Report produced, **STOP — awaiting Founder decision on remediation path**, whichever branch applies.

## 7. Recommended Next Step, Per Outcome

| Outcome | Meaning | Recommended next step |
|---|---|---|
| Row count = 0 | RLS correctly defaulted to deny; data was never at risk | Close Test 5 as a **test-design defect** (it expected the wrong exception type), correct the test's assertion logic in a future validation-script package, and separately still resolve the confirmed GRANT-level gap (defense-in-depth: two locks should both work, only one currently does) |
| Row count ≥ 1 | RLS did not block the write either — genuine security defect | **Immediate priority.** This becomes a new, first-class AGR (not folded into the existing GRANT finding), requiring both a GRANT/REVOKE fix and an explicit UPDATE-denying RLS policy (or a `FORCE ROW LEVEL SECURITY` reconsideration), with Founder sign-off before any further seed/validation work proceeds |

## 8. Founder Decisions Required

None to execute this diagnostic itself (it is read-only in effect). A decision is required **after** the result is known, per Section 7's table — the remediation path differs materially depending on outcome.

## 9. Risks

- Reintroducing the same evidentiary flaw as the original test (relying on an indirect signal instead of a direct measurement) — mitigated by requiring the row count itself, captured immediately after the UPDATE, as the headline finding
- An unclean rollback leaving unexpected state — mitigated by an explicit stop condition requiring immediate escalation if this occurs

## 10. Rollback Strategy

The diagnostic's own transaction is unconditionally rolled back as its final step, regardless of outcome — this is the mechanism under test, not a separate concern requiring a different rollback path.

## 11. Validation Strategy

The row-count measurement **is** the validation — a single, direct, unambiguous fact, with a secondary confirmatory check (Poha's unchanged state) reported alongside it but never substituted for it.

## 12. Critical Self-Review

- **Considered:** treating the "Poha unchanged" observation from the original Test 5 run as sufficient evidence to close this out — rejected; demonstrated above that this observation cannot distinguish between the safe and unsafe outcomes, since both are rolled back by the same unconditional exception regardless of the UPDATE's actual effect.
- **Considered:** assuming BYPASSRLS-carryover from the connecting `postgres`/`service_role` session as the likely explanation without checking role-switch mechanics — rejected; verified live that `postgres` is a legitimate member of `authenticated` (so `SET ROLE` genuinely succeeds) and that `authenticated` itself has `rolbypassrls=false`, which rules this out via direct evidence rather than assumption.
- **Considered:** designing this diagnostic as another DO-block-with-exception-handling test, matching the original's style — rejected; the whole point of this package is to remove the evidentiary flaw that pattern introduced. An explicit `BEGIN ... ROLLBACK` with a direct row-count capture is used instead, deliberately different in structure from the original.

---

## Versioning & Placement

`REPO-WP-04DC_RLS_Diagnostic_v1_0.md` → `docs/project-history/`, committed before execution begins, per established WP-3/WP-4 pattern.

## Sign-off

Founder approval to execute WP-4DC: _______________________ Date: ___________

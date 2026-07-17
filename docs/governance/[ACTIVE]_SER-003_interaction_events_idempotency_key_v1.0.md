# [ACTIVE]_SER-003_interaction_events_idempotency_key_v1.0 — Schema Evolution Request

**Status:** ACTIVE — APPROVED (Founder decision, 2026-07-17, approved as written — including the §5 partition-scoped uniqueness approach, approved as the correct trade-off, not a compromise to revisit).
**Version:** v1.0
**Date:** 2026-07-17
**Placement:** docs/governance/[ACTIVE]_SER-003_interaction_events_idempotency_key_v1.0.md
**Type:** Schema Evolution Request.
**Author:** Claude (Engineering session, Wave 2a).
**Implements in:** `database/migrations/032_interaction_events_dedup_key.sql` (+ rollback).

---

## 1. Problem

`DOC-P3-06` §08 states verbatim: *"No `Idempotency-Key` field exists in `interaction_events` today. A network retry of a `dish_cooked` event, for example, would double-count in LF-J02's `interaction_count++`."* FD-13 in the Decision Register left this as a client-vs-server ownership choice, with Option (a) (client-side only, no schema change) recommended for MVP but not ratified. This SER proposed the Option (b) schema change — a server-side dedup key — for Founder consideration alongside proposed mechanics.

**Everything under "Proposed Mechanics" (§3) was engineering judgment offered for Founder ratification, not a previously-decided fact — the Founder has now approved it as written (§10).**

## 2. Evidence

- `public.interaction_events` (`migration 012_interaction_audit_appendonly.sql`) has no dedup/idempotency column; `PRIMARY KEY (id, occurred_at)` where `id` is server-generated (`gen_random_uuid()` default) — a retried request gets a *new* `id`, so the existing PK cannot catch a duplicate.
- The table is `PARTITION BY RANGE (occurred_at)` (`migration 017_initial_partitions.sql`), monthly partitions. **This matters structurally:** Postgres requires any unique constraint on a partitioned table to include the partition key (`occurred_at`) — a bare `UNIQUE (dedup_key)` is not possible. See §5 for how this SER proposes to handle it.
- `interaction_count` (fed by `LF-J02`) is read by cold-start-exit logic (`J02`, `J05`) and is part of the MVP's Day-0/Day-90 acceptance metric (DOC-01 §07) — a double-counted retry directly corrupts a metric the MVP go/no-go decision depends on.
- No `POST /v1/events` handler exists yet in the codebase (Epic 5, not yet built) — this SER is being proposed ahead of that implementation so the schema is ready when it lands, not as a fix to already-shipped behavior.

## 3. Proposed Mechanics — engineering judgment, marked as such, for Founder ratification

| Aspect | Proposal | Status |
|---|---|---|
| Key generation | Client generates a UUID v4 per logical event (not per HTTP attempt) and sends it as `dedup_key`; retries of the same logical event reuse the same key. | **Approved, 2026-07-17.** |
| Duplicate window | A `dedup_key` seen again within **24 hours** is treated as a duplicate. Chosen because it comfortably covers realistic client retry/backoff windows (seconds to low minutes) with a wide safety margin, without holding an indefinite dedup table. | **Approved, 2026-07-17.** |
| Duplicate handling | On a detected duplicate, the server does **not** insert a second row and does **not** increment `interaction_count` again; it returns the **same response** the original request would have returned (idempotent semantics), rather than an error. | **Approved, 2026-07-17.** |
| Client retry policy | Client retries the same logical event up to **3 times** with backoff on transient failure (e.g., network timeout, 5xx). | **Approved, 2026-07-17.** |

## 4. Architecture Impact

Add `dedup_key uuid` to `public.interaction_events`, nullable (old/never-updated clients that don't send one are unaffected — their events are simply never deduplicated, same as today). `POST /v1/events` (Epic 5, unbuilt) would check for an existing row with the same `dedup_key` within the last 24 hours before inserting; this check is an **application-level query**, not solely a DB constraint — see §5 for why a DB constraint alone can't fully guarantee this on a partitioned table.

## 5. Backward Compatibility & a Partitioning Caveat (disclosed, not hidden)

- `dedup_key` added as **nullable**, no default required — every existing row gets `NULL`, which is not treated as a duplicate of anything (standard NULL-not-equal-NULL semantics).
- **Caveat disclosed and accepted by the Founder (2026-07-17), not a compromise to revisit:** because `interaction_events` is partitioned by `occurred_at`, a single global `UNIQUE (dedup_key)` index is not possible — Postgres requires the partition key in any unique index on a partitioned table. This SER uses a **partial unique index `UNIQUE (dedup_key, occurred_at) WHERE dedup_key IS NOT NULL`**, which catches duplicates reliably *within the same monthly partition* (i.e., essentially always, given a 24-hour window), backed by an **app-level 24h lookback query** as the actual dedup mechanism across a possible partition boundary (e.g., a request at 23:59:59 on the last day of a month and its retry at 00:00:01 the next day). This two-layer approach — partition-scoped DB constraint plus app-level lookback — is approved as the correct trade-off given the partitioning constraint, not a stopgap pending a larger redesign (e.g., a separate non-partitioned `event_dedup_keys` lookup table was considered and is not needed).
- Deterministic and idempotent: `ADD COLUMN IF NOT EXISTS` guard.

## 6. Migration Strategy

`032_interaction_events_dedup_key.sql`: `ALTER TABLE public.interaction_events ADD COLUMN dedup_key uuid;` + `CREATE UNIQUE INDEX ... ON public.interaction_events (dedup_key, occurred_at) WHERE dedup_key IS NOT NULL;` (created directly on the parent, propagating automatically to each existing/future partition, per this repository's partitioned-index convention in `020_indexes.sql`). Structural band, next sequential after `031` (SER-002).

## 7. Rollback Strategy

`032_interaction_events_dedup_key_rollback.sql`: drop the partial unique index, then `DROP COLUMN dedup_key`. Safe at any time before `POST /v1/events` (Epic 5) is built and depends on it.

## 8. Explicitly Out of Scope

- No `POST /v1/events` handler is written or modified under this SER (Epic 5 is unbuilt).
- No retry test (`_tests/events_endpoint.test.ts`, per FD-13's own acceptance criteria) is written here.
- The three mechanics in §3 are proposals only — approving this SER's *column* does not itself ratify those mechanics; the Founder may approve the column while choosing different mechanics.

## 9. Recommendation

**Approve the column + partial index, with the §5 partition caveat explicitly acknowledged**, and separately confirm or amend the §3 mechanics. Splitting "does the schema support this" from "what are the exact retry/dedup semantics" lets the schema-evolution question (narrow, mechanical) be approved independently of the product/engineering-judgment question (the four mechanics), which the Founder may want to discuss further.

## 10. Founder Decision

**APPROVED as written** (Founder, 2026-07-17) — both the column/index shape (§5/§6) and the §3 mechanics, including the partition-scoped uniqueness approach (§5), approved as the correct trade-off, not a compromise to revisit. Migration `032` implements this SER exactly as specified.

## 11. Cross-references

- `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-13 (client-vs-server ownership; this SER proposes Option (b) mechanics for the first time).
- `docs/architecture/[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md` §08 (the `[DCR]` line quoted above).
- `database/migrations/012_interaction_audit_appendonly.sql`, `017_initial_partitions.sql`, `020_indexes.sql` (current table/partition/index shape).
- `[ACTIVE]_SER-001_re_cohorts_city_tier_v1.0.md` (SER format precedent).

Founder Sign-off: Ankit Mittal — Date: 2026-07-17

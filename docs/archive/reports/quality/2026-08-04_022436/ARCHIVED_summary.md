# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Ghar Production Quality Report

_Generated 2026-08-04T02:24:36.921897+00:00 · git `cdf8b20`_

| Quality score | Pass % | Passed | Failed | Skipped | Launch |
|---|---|---|---|---|---|
| **86.8** | 96.8 | 632 | 21 | 26 | ❌ NO |

**Launch readiness:** NOT READY — P0 test failures present

## Steps

| Step | Phase | Status | Priority | Detail |
|---|---|---|---|---|
| inventory | 1-2 | PASS | P3 | 78 components, 18 features |
| ruff-lint | 16 | PASS | P2 | clean |
| unit-core | 4 | PASS | P0 | 84 passed, 0 failed, 0 skipped |
| unit-service | 4 | PASS | P0 | 68 passed, 0 failed, 0 skipped |
| quality-contract | 6 | PASS | P0 | 5 passed, 0 failed, 0 skipped |
| quality-recsys | 8 | FAIL | P0 | 451 passed, 21 failed, 26 skipped |
| quality-security | 13 | PASS | P0 | 12 passed, 0 failed, 0 skipped |
| quality-planning | 5 | PASS | P1 | 12 passed, 0 failed, 0 skipped |
| chaos | 14 | WARN | P1 | chaos probe error: No module named 'ghar_re_service' |
| performance | 12 | PASS | P2 | recommendations p50=130.61ms p99=423.13ms (threshold 1500.0ms, in-process) |
| secrets-scan | 13 | PASS | P1 | no hardcoded secret values detected |
| database | 7 | SKIP | P0 | no live database configured |
| edge-functions | 6 | BLOCKED | P0 | 6 Deno edge-function test file(s) present but not runnable |
| ui-playwright | 9-11 | SKIP | P1 | GHAR_WEB_URL not set. The frontend is an Expo/React-Native app with no committed web build; provide a running web target (e.g. `expo start --web`) to enable browser tests. |

## Unverified P0 surfaces (not certifiable in this environment)

- database: DATABASE_URL / SUPABASE_DB_URL not set — migrations, RLS, constraints, and data-integrity checks require a reachable Postgres with the Supabase auth.* bootstrap; not verifiable in this environment.
- edge-functions: Deno runtime is not installed in this environment; `deno test` cannot execute. Install Deno (or run in Supabase CI) to validate consent/feedback/household/recommendations/user-delete/user-export functions.

## Failing tests

- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[jain_couple_ahmedabad]` — AssertionError: jain_couple_ahmedabad: non-deterministic recommendations across calls
assert [['md5:Sannas...heeyal'], ...] == [['md5:Sannas...heeyal'], ...]
  
  At index 6 diff: ['md5:Neer Dosa', 'md5:Mor Kuzhambu'] != ['md5:Idiyappam', 'md5:Mor Kuzhambu']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[real_p03]` — AssertionError: real_p03: non-deterministic recommendations across calls
assert [['md5:Thoran...Sambar'], ...] == [['md5:Thoran...Sambar'], ...]
  
  At index 6 diff: ['md5:Appam', 'md5:Avial'] != ['md5:Keerai Masiyal', 'md5:Vengaya Sambar']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[real_p13]` — AssertionError: real_p13: non-deterministic recommendations across calls
assert [['md5:Paneer... Bhaji'], ...] == [['md5:Paneer... Bhaji'], ...]
  
  At index 6 diff: ['md5:Baingan Bharta', 'md5:Pakodi Ki Kadhi'] != ['md5:Paneer Tikka', 'md5:Pakodi Ki Kadhi']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[real_p22]` — AssertionError: real_p22: non-deterministic recommendations across calls
assert [['md5:Thoran...:Avial'], ...] == [['md5:Thoran...:Avial'], ...]
  
  At index 6 diff: ['md5:Vendakkai Poriyal', 'md5:Vengaya Sambar'] != ['md5:Idiyappam', 'md5:Avial (Kerala)']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[real_p25]` — AssertionError: real_p25: non-deterministic recommendations across calls
assert [['md5:Paneer...ainsoo'], ...] == [['md5:Paneer...ainsoo'], ...]
  
  At index 6 diff: ['md5:Kachhi Haldi Ki Sabzi', 'md5:Phaanu'] != ['md5:Haak (Kashmiri Greens)', 'md5:Phaanu']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[real_p28]` — AssertionError: real_p28: non-deterministic recommendations across calls
assert [['md5:Thoran... Rasam'], ...] == [['md5:Thoran... Rasam'], ...]
  
  At index 6 diff: ['md5:Idiyappam', 'md5:Kuzhambu (Vathal)'] != ['md5:Appam', 'md5:Kuzhambu (Vathal)']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[real_p29]` — AssertionError: real_p29: non-deterministic recommendations across calls
assert [['md5:Begun ...Shukto'], ...] == [['md5:Begun ...Shukto'], ...]
  
  At index 6 diff: ['md5:Saga Bhaja', 'md5:Dalma'] != ['md5:Bharli Vangi', 'md5:Amti']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[real_p33]` — AssertionError: real_p33: non-deterministic recommendations across calls
assert [['md5:Mutta ...:Saagu'], ...] == [['md5:Mutta ...:Saagu'], ...]
  
  At index 6 diff: ['md5:Appam', 'md5:Parippu Curry'] != ['md5:Poriyal', 'md5:Parippu Curry']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[real_p38]` — AssertionError: real_p38: non-deterministic recommendations across calls
assert [['md5:Bharli...:Avial'], ...] == [['md5:Bharli...:Avial'], ...]
  
  At index 6 diff: ['md5:Poriyal', 'md5:Parippu Curry'] != ['md5:Appam', 'md5:Manga Curry']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[real_p41]` — AssertionError: real_p41: non-deterministic recommendations across calls
assert [['md5:Mochar...:Dalma'], ...] == [['md5:Mochar...:Dalma'], ...]
  
  At index 6 diff: ['md5:Baingan Bharta', 'md5:Dal Tadka'] != ['md5:Bhindi Masala', 'md5:Dal Tadka']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[allergy_sesame_veg]` — AssertionError: allergy_sesame_veg: non-deterministic recommendations across calls
assert [['md5:Rasam ...:Avial'], ...] == [['md5:Rasam ...:Avial'], ...]
  
  At index 6 diff: ['md5:Paneer Bhurji', 'md5:Dal Makhani'] != ['md5:Paneer Tikka', 'md5:Dum Aloo']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[region_odisha]` — AssertionError: region_odisha: non-deterministic recommendations across calls
assert [['md5:Begun ...ok Dal'], ...] == [['md5:Begun ...ok Dal'], ...]
  
  At index 6 diff: ['md5:Fried Bombil', 'md5:Amti'] != ['md5:Bharli Vangi', 'md5:Amti']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[region_jharkhand]` — AssertionError: region_jharkhand: non-deterministic recommendations across calls
assert [['md5:Begun ...ok Dal'], ...] == [['md5:Begun ...ok Dal'], ...]
  
  At index 6 diff: ['md5:Fried Bombil', 'md5:Amti'] != ['md5:Bharli Vangi', 'md5:Amti']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[large_joint_family_non_veg]` — AssertionError: large_joint_family_non_veg: non-deterministic recommendations across calls
assert [['md5:Bhindi... Marag'], ...] == [['md5:Bhindi... Marag'], ...]
  
  At index 6 diff: ['md5:Ker Sangri', 'md5:Dubuk'] != ['md5:Egg Curry', 'md5:Pakodi Ki Kadhi']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[multi_allergy_0]` — AssertionError: multi_allergy_0: non-deterministic recommendations across calls
assert [['md5:Sannas... Bhaji'], ...] == [['md5:Sannas... Bhaji'], ...]
  
  At index 6 diff: ['md5:Idiyappam', 'md5:Manga Curry'] != ['md5:Poriyal', 'md5:Manga Curry']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[multi_allergy_1]` — AssertionError: multi_allergy_1: non-deterministic recommendations across calls
assert [['md5:Bharli...akhani'], ...] == [['md5:Bharli...akhani'], ...]
  
  At index 6 diff: ['md5:Paneer Tikka', 'md5:Dum Aloo'] != ['md5:Rasam Vada', 'md5:Saagu']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[fasting_ramzan_derived]` — AssertionError: fasting_ramzan_derived: non-deterministic recommendations across calls
assert [['md5:Mutta ...:Saagu'], ...] == [['md5:Mutta ...:Saagu'], ...]
  
  At index 6 diff: ['md5:Poriyal', 'md5:Parippu Curry'] != ['md5:Appam', 'md5:Parippu Curry']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[huge_household_derived]` — AssertionError: huge_household_derived: non-deterministic recommendations across calls
assert [['md5:Shukni...Sambar'], ...] == [['md5:Shukni...Sambar'], ...]
  
  At index 6 diff: ['md5:Aloo Pitika', 'md5:Aloo Dum (Bengali)'] != ['md5:Vendakkai Poriyal', 'md5:Manga Curry']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[centenarian_derived]` — AssertionError: centenarian_derived: non-deterministic recommendations across calls
assert [['md5:Bhindi...Pakora'], ...] == [['md5:Bhindi...Pakora'], ...]
  
  At index 6 diff: ['md5:Ker Sangri', 'md5:Mix Veg'] != ['md5:Paneer Bhurji', 'md5:Chainsoo']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[duplicate_allergy_entries_derived]` — AssertionError: duplicate_allergy_entries_derived: non-deterministic recommendations across calls
assert [['md5:Rasam ...heeyal'], ...] == [['md5:Rasam ...heeyal'], ...]
  
  At index 6 diff: ['md5:Appam', 'md5:Avial'] != ['md5:Keerai Masiyal', 'md5:Avial']
  Use -v to get more diff
- `ops.quality.suites.test_recommendation_behavior::test_persona_determinism[objective_protein_calculator_derived]` — AssertionError: objective_protein_calculator_derived: non-deterministic recommendations across calls
assert [['md5:Rasam ...Sambar'], ...] == [['md5:Rasam ...Sambar'], ...]
  
  At index 6 diff: ['md5:Appam', 'md5:Avial'] != ['md5:Paneer Bhurji', 'md5:Dal Makhani']
  Use -v to get more diff
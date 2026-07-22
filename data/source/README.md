# Ghar RE — Configuration (extracted from FROZEN specs)

Every tunable the engine reads lives here — NOT hard-coded. Tuning = edit config, re-run. This is the spec<->code traceability layer.

## Files & source-of-truth
| Config file | Source spec |
|---|---|
| base_weights.yaml | Core Spine FROZEN - S2 PART B |
| distance_weights.yaml | Core Spine FROZEN - S1 3.6 (beta, tau, IDF, cuisine/diet distance) |
| q15_weights.yaml | Core Spine FROZEN - S3 (gamma, kappa, bounds) |
| pairing_rules.yaml | Core Spine FROZEN - S4 (lambda_pair, gates, soft terms) |
| weather_rules.yaml | Core Spine S2 m_weather + KB v0.2 Z2 |
| filters.yaml | Core Spine FROZEN - S2 PART A + S1 normalization |
| derivation_params.yaml | D1-D7 FROZEN - S4-5 (all D1-D7 params) |
| community_priors.csv | KB v0.2 - C1 (soft, decays v2) |
| ../sig_scores_v1.csv | KB v0.2 - S1/S2 (signature scores; 58 curated / 744 draft) |

## Rules
1. No parameter appears in code that isn't here.
2. Changing a frozen value = an RFC (record in the spec's Future/RFC register), then edit here.
3. IDF weights recompute whenever the catalogue changes (N, df_i).
4. v1 pins: all conf_k = 1.0, kappa = 1.0, rho_disc near floor, S_pref = 0, S_cohort = 0.
5. Conformance review (Phase 6) diffs code against these files + the specs.

## Philosophy
These files are **implementation artifacts derived from the frozen specifications.** If a frozen specification changes, regenerate or update the corresponding configuration rather than editing business logic directly.

## Runtime contract
Load → validate → **freeze in memory** → run. Config is **immutable at runtime**; no live edits. Every recommendation can be stamped with `Spine v1.0 · KB v0.2 · Config v1.0` for audit.

## Versioning
Every config carries `config_version`, `generated_from`, `generated_on`. `community_priors.csv` and `sig_scores_v1.csv` carry `version` columns.

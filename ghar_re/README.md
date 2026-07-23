# ghar_re — Ghar RE v1.0 reference pipeline (rebuild)

Standalone, self-contained **reference implementation** of the FROZEN Ghar RE v1.0 spine + the
D1–D7 household intelligence layer. It is **not wired to the live app** (Deno edge functions) — per
the task STOP condition — and reads its parameters from the frozen-spec config, never hard-coded.

> **Placement note:** this package sits at repo top-level because the frozen repository architecture
> has no code home for a Python engine. Relocate on Founder direction (nothing is committed).

## Sources of truth (nothing invented silently)
| Layer | Source |
|---|---|
| Logic / architecture | the 4 FROZEN docs (Core Spine, D1–D7, Derivation-reconciled, Final_RE) |
| Parameter VALUES | `data/source/*.yaml` (loaded by `config.py`) + KB v0.2 (`knowledge.py`) |
| Golden sample | `fixtures.py` (invented, all `ai_generated`) |

## Modules
- `config.py` — loads `data/source/*.yaml`; raises rather than inventing a missing parameter.
- `knowledge.py` — KB v0.2 transcription (zone map, comfort heroes ✓/⚑, sig bands, negative priors,
  §R2 priors, §E1 normalization, §C1 lean cross-check). `data_source`: ✓→real, ⚑→stub.
- `fixtures.py` — golden sample: 39 dishes + 7 households (all `ai_generated`).
- `catalogue.py` — in-memory catalogue (zone resolved cuisine→group→zone_map, KB §R1).
- `derivation.py` — D1–D7 → θ (each field a `(value,confidence,source,kind,stability,version,ts)` record).
- `scoring.py` — hard filters A1–A6 (§S2A) + BASE modules (§S2B) + Q15 gain (§S3).
- `pairing.py` — guardrails + plate_score + assemble-7 + carb attach (§S4 + KB §R2a).
- `pipeline.py` — end-to-end orchestration. `python3 -m ghar_re.pipeline` prints 7 plates/household.
- `seedgen.py` — emits `database/seeds/120_ghar_re_kb_reference.sql` + `121_ghar_re_golden_sample.sql`.

## Run
```bash
python3 -m ghar_re.pipeline        # demo: 7 plates per golden household
python3 -m ghar_re.seedgen         # regenerate the SQL seeds from fixtures/knowledge
python3 -m pytest ghar_re/tests -q # end-to-end tests
```

## v1 pins (per spec + config README)
`conf_k = 1.0` everywhere · `kappa = 1.0` · `rho_disc` near floor (familiarity-first) ·
`S_pref = 0` · `S_cohort = 0` · D7 latent `= {}`. Weather API is **mocked** (injected context).

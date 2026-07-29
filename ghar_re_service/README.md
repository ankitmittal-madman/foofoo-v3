# ghar_re_service — Ghar RE v1 HTTP service (thin hosting shell)

The production RE service (RE-DOC-10 Phase B). It **hosts** the `ghar_re_core` domain package over
HTTP — it contains **no recommendation math of its own** (RE-DOC-11 §3). All scoring/derivation/
pairing lives in `ghar_re_core`, the single tested implementation.

## Layers
| Module | Responsibility |
|---|---|
| `providers.py` | `CatalogueProvider` / `ConfigProvider` Protocols + one adapter each (`LocalSnapshotCatalogueProvider`, `YamlFileConfigProvider`). The seams for future data sources (RE-DOC-11 §1/§2). |
| `modules.py` | `ScoringModule` protocol + ordered registry wrapping each `ghar_re_core.scoring` BASE component; composes BASE and emits the open `contributions[]` (RE-DOC-11 §6/§7). |
| `schemas.py` | Validates requests/responses against `contracts/ghar-re-v1.schema.json` directly (zero FastAPI imports, no hand-duplicated rules). |
| `engine.py` | Composition/translation: request → `ghar_re_core.pipeline.recommend` → contract response. |
| `lifecycle.py` | Startup: load config → catalogue → indices → registry → ready. Structured JSON logs. |
| `main.py` | FastAPI routes — translation-only. `POST /v1/recommendations`, `GET /healthz`, `/readyz`, `/v1/meta`. |

## Run
```bash
pip install -e .            # installs ghar-re-core (from repo root) first, then this
pip install -e ghar_re_service
uvicorn ghar_re_service.main:app --reload      # serves on :8000
python3 -m pytest ghar_re_service/tests -q     # contract + e2e tests
```

## Contract
`contracts/ghar-re-v1.schema.json` is the single source of truth. The service validates its own
responses before returning them (fail-closed). Compatibility is additive/open — unknown fields are
ignored, new fields are optional, breaking changes bump to `/v2/` (RE-DOC-11 §5).

## Scope
Phases A–F. Weather is mocked (injected via the request). Catalogue = golden sample; the real
810-dish cutover is Phase G.

---

# Deployment (Phase F)

> **Status: PREPARED, NOT DEPLOYED.** Every artefact below is ready to run, but no real deploy has
> been executed and no cloud infrastructure has been provisioned. The "Could not be verified"
> section at the end lists exactly what remains unproven until someone runs these commands against
> a real Fly.io account.

## The immutable bundle (RE-DOC-10 §8)

The engine reads its catalogue and config from an **immutable bundle baked into the image** — never
from a database at runtime, and never from the repo working tree.

This is not ceremony. Three separate code paths resolve files relative to the *installed package*,
and all three break in a container, where the package lives in `site-packages`:

| Path | Reads | Breaks because |
|---|---|---|
| `ghar_re_core/config.py` | the 7 YAML config files + `community_priors.csv` | `<site-packages>/../data/source` does not exist |
| `ghar_re_core/catalogue.py` | `ingredients_v5.csv` (allergen/Jain master), **at import time** | same, and it crashes before any provider runs |
| `ghar_re_service/schemas.py` | `contracts/ghar-re-v1.schema.json`, **at import time** | `<site-packages>/../../contracts` does not exist |

Each now honours an env var (`GHAR_RE_CONFIG_DIR`, `GHAR_RE_CONTRACT_PATH`), which the Dockerfile
sets. Unset, behaviour is byte-for-byte unchanged — the golden-master test pins that.

The contract is deliberately **not** copied into the bundle: Phase E's `contract-check` CI job
asserts the repo holds exactly **one** `ghar-re-v1.schema.json`, so both services provably read the
same file. A second committed copy would defeat the check. Hence a path override instead.

### Rebuilding the bundle

```bash
# From the repo root. Rewrites ghar_re_service/data/bundle/ and prints the manifest.
python -m ghar_re_service.scripts.export_bundle

# CI gate: fails if the committed bundle is stale vs data/source (no writes).
python -m ghar_re_service.scripts.export_bundle --check
```

`bundle_version` is a **content hash**, not a timestamp — identical inputs always produce the
identical version, so comparing two images' `/v1/meta` output is a real answer to "is this the same
catalogue?". It is surfaced at `/v1/meta` alongside `config_version`, and logged at startup
(`startup.source_resolved`).

**Source:** the golden-sample fixtures (`ghar_re_core.fixtures.DISHES`, 39 dishes) plus the YAML
config layer. RE-DOC-10 §8 describes the eventual export as pulling from Postgres; that swap is
Phase G and deliberately out of scope. The bundle *format* is identical either way — swapping the
source later changes `export_bundle.py` only, and nothing in the service or the engine.

## Step-by-step deploy

Run these yourself — none of them have been executed here.

### 0. Prerequisites
```bash
curl -L https://fly.io/install.sh | sh     # if flyctl is not installed
fly auth login
fly version
```

### 1. Make sure the bundle is current
```bash
cd /path/to/foofoo-v3
python -m ghar_re_service.scripts.export_bundle --check   # must print "OK: bundle is current"
```
If it reports stale, re-run without `--check`, then **commit the regenerated bundle** — it is
tracked in git on purpose, so a catalogue change is reviewable as a diff (RE-DOC-10 §8).

### 2. Create the app (first time only)
```bash
# --no-deploy so the app exists (and can hold secrets) before any image is pushed.
fly apps create ghar-re --org <your-org>
```
`fly launch` is deliberately **not** used: it would overwrite the hand-written `fly.toml`.

### 3. Set secrets — BEFORE the first deploy (Task 4)

The shared HMAC secret must never be committed or placed in `fly.toml`'s `[env]`. Generate a strong
one and store it in Fly's encrypted secret store:

```bash
# Generate a 32-byte random secret and set it in one step. Note the leading space: in bash/zsh with
# HISTCONTROL=ignorespace this keeps the value out of your shell history.
 fly secrets set GHAR_RE_SERVICE_SECRET="$(openssl rand -hex 32)" --app ghar-re

# Confirm it exists (prints the NAME and a digest — never the value):
fly secrets list --app ghar-re
```

**Save the same value for the Edge Function** — both sides must hold the identical secret or every
call fails with `401 invalid_signature`. If you generated it inline as above, read it back out of
your Supabase config after step 6 rather than trying to recover it from Fly; Fly will not show it
to you again. If you prefer, generate it to a variable first:

```bash
 SECRET="$(openssl rand -hex 32)"
 fly secrets set GHAR_RE_SERVICE_SECRET="$SECRET" --app ghar-re
 npx supabase secrets set GHAR_RE_SERVICE_SECRET="$SECRET"    # step 6, same value
 unset SECRET
```

This is the **only** secret the RE needs. Per RE-DOC-10 §13 it holds no database credentials of any
kind — if you ever find yourself adding one here, something has gone wrong with the architecture.

`FOOFOO_ENV=production` is already set in `fly.toml`, which arms the fail-closed guard: with it set
and the secret missing, the service **refuses to start** rather than falling back to the dev secret
published in this repo. (Verified locally — see below.)

### 4. Deploy
```bash
# Build context is the REPO ROOT (the image needs ghar_re_core/, pyproject.toml and contracts/).
fly deploy --config ghar_re_service/fly.toml --dockerfile ghar_re_service/Dockerfile .

# Tag the image with engine_version for independent rollback (RE-DOC-10 §13):
fly deploy --config ghar_re_service/fly.toml --dockerfile ghar_re_service/Dockerfile \
           --image-label v1.0.0 .
```

### 5. Verify the deploy (from inside the private network)

The app has **no public ingress** (see Network isolation below), so these run through Fly:

```bash
fly status --app ghar-re                 # expect 1 machine, state "started", health checks passing
fly logs --app ghar-re                   # expect startup.ready + source_resolved with bundle_version

# Reach the private address from a throwaway machine in the same org:
fly ssh console --app ghar-re -C "wget -qO- http://localhost:8080/healthz"
fly ssh console --app ghar-re -C "wget -qO- http://localhost:8080/readyz"
fly ssh console --app ghar-re -C "wget -qO- http://localhost:8080/v1/meta"
```

Confirm `/v1/meta`'s `bundle_version` matches what `export_bundle` printed locally. If it does not,
the running image is not built from the bundle you think it is.

### 6. Point the Edge Function at it (Task 6)

`GHAR_RE_SERVICE_URL` should become the Fly **private** address:

```
http://ghar-re.internal:8080
```

Set it as a Supabase Edge Function secret (it is not sensitive, but it lives with the other config):

```bash
npx supabase secrets set GHAR_RE_SERVICE_URL="http://ghar-re.internal:8080"
npx supabase secrets set GHAR_RE_SERVICE_SECRET="<the same value from step 3>"
npx supabase secrets list
```

Note `http://`, not `https://` — traffic over Fly's 6PN mesh is already encrypted at the network
layer, and the RE serves plain HTTP inside it (no TLS terminator is configured, by design).

⚠️ **This URL only resolves from inside Fly's private network.** Supabase Edge Functions run on
Supabase's infrastructure, **not** on Fly — so `*.internal` will **not** resolve from them. See the
next section; this is the one open question that needs a decision before the two halves can talk.

**Does the Phase C guard still make sense here?** Yes, and more so. `config.ts` requires both
`GHAR_RE_SERVICE_URL` and `GHAR_RE_SERVICE_SECRET` in production and hard-fails without them, while
local/staging fall back to `http://localhost:8000` + the dev secret. Against a deployed target that
is exactly right: the dev fallback keeps local work friction-free, and production cannot start
pointed at localhost or signing with a secret that is public in this repo. One tightening worth
considering (not changed here — it is your call): `config.ts` still lets **staging** use the dev
fallback, flagged `[TODO Phase F]` in that file. If staging ever gets its own deployed RE, staging
should be held to the same requirement as production.

## Network isolation — now defense-in-depth, not the only boundary (Task 5)

**This changed materially in Phase C.5.** The RE now verifies an HMAC signature on every
`/v1/recommendations` call and rejects unsigned, tampered, wrong-secret, or replayed (>5 min)
requests with a `401` *before parsing the body or doing any computation*. Network isolation is
therefore the **second** layer.

Before Phase C.5, this config was the only thing standing between the engine and an open endpoint —
a misconfigured network meant a completely unauthenticated service. That is no longer true. If the
two ever conflict, **the signature check is the one that must not be weakened**: it is the boundary
that still holds when the network boundary is misconfigured.

How it is configured: `fly.toml` declares no public service, so Fly assigns no public IP. The app is
reachable only over 6PN (Fly's private WireGuard mesh) at `ghar-re.internal` from other apps in the
same organisation.

```bash
fly ips list --app ghar-re      # expect NO public v4/v6 address
```

### If the Edge Function must reach it from outside Fly's network

This is the likely case, since Supabase Edge Functions do not run on Fly. Options, roughly in order
of preference:

1. **Fly private-network egress from Supabase** — not currently possible; Supabase Edge Functions
   cannot join a Fly 6PN mesh. Listed only to rule it out explicitly.
2. **Public ingress + signature + IP allowlist.** Add an `[http_service]` public port to `fly.toml`,
   set `force_https = true`, put `GHAR_RE_SERVICE_URL=https://ghar-re.fly.dev`, and restrict source
   IPs to Supabase's egress ranges with a Fly proxy rule or an in-app allowlist. The HMAC check is
   what actually protects the endpoint here; the allowlist narrows exposure. **Do not do this
   without also confirming the signature check is live** — verify with an unsigned `curl` that
   returns `401`.
3. **A WireGuard tunnel** from a small relay you control into the Fly mesh, with the Edge Function
   calling the relay. More moving parts; only worth it if (2) is unacceptable.

Whichever is chosen, `GHAR_RE_SERVICE_URL` changes accordingly and the secret does not.

## Rollback

```bash
fly releases --app ghar-re                  # list releases
fly deploy --image <previous-image-ref> --config ghar_re_service/fly.toml
```
RE-DOC-10 §13 requires the RE to roll back **independently** of the Edge Function — they are
separate deploys and neither blocks the other. If a rolled-back RE serves an older `bundle_version`,
that is visible at `/v1/meta`.

## What was verified here, and how

Verified locally, without cloud access:

| Check | Result |
|---|---|
| Bundle export is deterministic (same inputs → same `bundle_version`) | ✅ |
| `bundle_version` changes when any config file changes | ✅ |
| Incomplete bundle fails at build time, not at runtime | ✅ |
| Bundled catalogue reconstructs the same dish set as the fixtures | ✅ |
| Engine serves 7 plates with the repo config path pointed at `/nonexistent` | ✅ |
| Service starts with **only** the bundle reachable (packages installed to `site-packages`, run from outside the repo — the container's exact conditions) | ✅ |
| `/healthz` → 200, `/readyz` → 200 after load, `/v1/meta` reports `bundle_version` | ✅ |
| Signed `POST /v1/recommendations` → 200 with 7 plates | ✅ |
| Unsigned → 401 `missing_signature`; wrong secret → 401 `invalid_signature`; stale → 401 `stale_signature` | ✅ |
| `FOOFOO_ENV=production` with no secret → refuses to start | ✅ |
| Full Python suite (56 tests incl. golden master) | ✅ |

## Could NOT be verified without real platform access

Stated plainly rather than assumed:

1. **The Docker image has never been built.** The sandbox's proxy denies
   `production.cloudfront.docker.com` (403 on CONNECT), so no base image can be pulled and
   `docker build` cannot run. The Dockerfile is therefore **unbuilt and unrun**. The container's
   *runtime conditions* were reproduced faithfully (non-editable install into `site-packages`, run
   from outside the repo, only the bundle and contract reachable) and everything passed — which is
   what caught the `ingredients_v5.csv` import-time break — but that is a simulation of the
   container, not the container. **Run `docker build` first, before `fly deploy`.**
2. **`fly.toml` has never been parsed by flyctl.** Key names, nesting, and especially the
   `[checks]` vs `[[http_service.checks]]` split are written from the documented schema, not
   validated. Run `fly config validate --config ghar_re_service/fly.toml` before deploying.
3. **No Fly.io account, org, app, region, or secret exists.** Nothing was provisioned.
4. **`primary_region = "bom"` is a judgement call**, not a measurement — chosen as the closest
   region to the Indian user base. Confirm it against `fly platform regions`.
5. **The 512MB VM size is an estimate** for the 39-dish golden sample. Re-measure before Phase G's
   810-dish catalogue.
6. **Whether Supabase Edge Functions can reach `*.internal` at all** — they almost certainly cannot
   (they do not run on Fly). This is the single biggest open item; see the section above.

## Deferred / TODO

- [ ] **G6 protein-balance pairing gap** (`ghar_re_core/pairing.py`, `compat()`): `protein_cat`
      declares `{dal_lentil, kebab, egg_dish, curry}` but the check only tests `dal_lentil`, so
      curry/kebab plates miss a bonus they were designed to earn. Fixing it **changes
      recommendation output**, so it needs the golden files regenerated in the same PR for the diff
      to be reviewable. Deliberately deferred by the Founder — not part of Phase F.
- [ ] Decide the Supabase → Fly reachability approach (section above).
- [ ] Consider holding staging to the same secret requirement as production (`config.ts` TODO).
- [ ] Pin the base image by digest once a real build has produced one.

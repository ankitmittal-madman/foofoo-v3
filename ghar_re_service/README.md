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

### 5. Verify the deploy

The app has **public ingress** by design (see the section below), so these run directly:

```bash
fly status --app ghar-re                 # expect 1 machine, state "started", health checks passing
fly logs --app ghar-re                   # expect startup.ready + source_resolved with bundle_version

curl https://ghar-re.fly.dev/healthz
curl https://ghar-re.fly.dev/readyz
curl https://ghar-re.fly.dev/v1/meta

fly ips list --app ghar-re               # a public v4/v6 address IS expected here — see below
```

Confirm `/v1/meta`'s `bundle_version` matches what `export_bundle` printed locally. If it does not,
the running image is not built from the bundle you think it is.

**Then confirm the trust boundary is actually live** — this is the single most important check in
this runbook, because public ingress means the signature check is the only thing protecting the
engine:

```bash
# MUST return 401 {"error":"unauthorized","detail":"missing_signature"}.
# If this returns anything else, take the app down (`fly scale count 0 --app ghar-re`) and fix it
# before doing anything else.
curl -i -X POST https://ghar-re.fly.dev/v1/recommendations \
     -H 'content-type: application/json' -d '{}'
```

### 6. Point the Edge Function at it (Task 6)

`GHAR_RE_SERVICE_URL` is the app's **public HTTPS** address:

```
https://ghar-re.fly.dev
```

Set it as a Supabase Edge Function secret (it is not sensitive, but it lives with the other config):

```bash
npx supabase secrets set GHAR_RE_SERVICE_URL="https://ghar-re.fly.dev"
npx supabase secrets set GHAR_RE_SERVICE_SECRET="<the same value from step 3>"
npx supabase secrets list
```

Note `https://`, not `http://`: the request crosses the public internet, and `force_https = true`
in `fly.toml` redirects plain HTTP. The signature protects against tampering, but TLS is what keeps
the request body — household composition, i.e. personal data — private in transit.

**Does the Phase C guard still make sense here?** Yes, and more so. `config.ts` requires both
`GHAR_RE_SERVICE_URL` and `GHAR_RE_SERVICE_SECRET` in production and hard-fails without them, while
local/staging fall back to `http://localhost:8000` + the dev secret. Against a deployed target that
is exactly right: the dev fallback keeps local work friction-free, and production cannot start
pointed at localhost or signing with a secret that is public in this repo. One tightening worth
considering (not changed here — it is your call): `config.ts` still lets **staging** use the dev
fallback, flagged `[TODO Phase F]` in that file. If staging ever gets its own deployed RE, staging
should be held to the same requirement as production.

## Public ingress and the trust boundary (Task 5 — settled)

**This is a deliberate, confirmed design decision, not an unresolved gap.**

Supabase Edge Functions run on Supabase's infrastructure, cannot join Fly's 6PN private mesh, and
**cannot present a fixed egress IP range**. Private-only networking and IP allowlisting are both
therefore unavailable to us. The RE accepts **public ingress**, and:

> **HMAC signature verification is the trust boundary.** Not a second layer behind the network —
> the actual and only one.

Earlier revisions of this document treated network isolation as the primary boundary with the
signature as defence-in-depth. That is now inverted, and the practical consequences are worth being
blunt about: any misbehaviour in `auth.py` is directly internet-exposed. There is no network layer
left to catch it.

### What the boundary actually enforces

Every `POST /v1/recommendations` must carry `X-Ghar-Signature: t=<unix>,v1=<hex>` — an HMAC-SHA256
over the **raw request bytes**, keyed on a secret held only in Fly's and Supabase's encrypted secret
stores. Rejected with `401`, *before the body is parsed or the engine is touched*:

| Case | `detail` |
|---|---|
| No signature header | `missing_signature` |
| Header present but unparseable | `malformed_signature` |
| Timestamp more than 5 minutes from server clock (replay) | `stale_signature` |
| Body tampered with, or signed with the wrong secret | `invalid_signature` |

The comparison is constant-time (`hmac.compare_digest`), so the secret cannot be recovered byte by
byte through timing. Someone who can reach the port still cannot get a recommendation out of it.

`fly ips list` **will** show a public IPv4/IPv6. That is expected and correct.

### Rate limiting (Task 2)

Because the HMAC check is now the sole boundary and is internet-reachable, anything that can send
bytes can make the service compute an HMAC. A limiter therefore runs **ahead of** signature
verification, so a flood is shed before any HMAC is computed.

| Property | Behaviour |
|---|---|
| Algorithm | Sliding window, per client IP (`Fly-Client-IP`, set by Fly's proxy) |
| Default | **300 requests / minute / IP** — `GHAR_RE_RATE_LIMIT_PER_MINUTE` in `fly.toml` `[env]` |
| Over limit | `429` + `Retry-After` header; counted at `/v1/meta` as `rate_limited_total` |
| Paths guarded | `/v1/recommendations`, `/v1/meta` |
| Paths exempt | `/healthz`, `/readyz` — shedding a platform probe would get the machine restarted |
| Disable | Set `GHAR_RE_RATE_LIMIT_PER_MINUTE = "0"` |

Four things about it are deliberate and worth knowing before you tune it:

1. **The default is generous on purpose.** Supabase's egress is NAT'd, so one source address can
   legitimately carry many end users. A tight per-IP cap throttles real traffic, not attackers.
   If you see `rate_limited_total` climbing while users complain, **raise it** — it is an `[env]`
   value, so a `fly deploy` picks it up with no rebuild.
2. **It is per machine.** The window lives in process memory (`--workers 1`, `min_machines_running
   = 1`, so today one machine = one window). Scale to N machines and the effective ceiling becomes
   N × the limit. Shared enforcement would need Redis; not worth it at this size.
3. **It fails open.** If the limiter has not loaded, requests pass through to the signature check.
   The asymmetry with auth — which fails *closed*, returning `503` — is intentional: a missing
   damper should not become a self-inflicted outage, whereas a missing secret must never let
   unauthenticated traffic through.
4. **It is a volume damper, not a WAF.** It stops one noisy source from burning CPU on signature
   verification. Distributed floods are out of scope — see the Cloudflare note below.

`[http_service.concurrency]` in `fly.toml` (soft 200 / hard 250) is a separate, complementary
backstop: it bounds how many requests are *in flight at once*, where the limiter bounds *rate*.
Fly's proxy has no per-IP rate limiting of its own, which is why the limiter is in-process.

### Later, if needed: Cloudflare in front (Task 4 — note only, not implemented)

If distributed/bot traffic ever becomes a real problem, the standard approach needs no application
change: point a Cloudflare-managed hostname at the Fly app, add the hostname with
`fly certs add re.<your-domain>`, enable Cloudflare's proxy (orange cloud) with Bot Fight Mode and a
rate-limiting rule, then change `GHAR_RE_SERVICE_URL` to the Cloudflare hostname. One caveat that
matters for the in-process limiter: traffic would then arrive from Cloudflare's IPs, so
`Fly-Client-IP` becomes Cloudflare's edge rather than the true client, and per-IP limiting would
need to read `CF-Connecting-IP` instead — **only** trustworthy once direct Fly access is restricted
to Cloudflare's ranges, otherwise the header is forgeable. Deliberately not built now: it is real
configuration work and unnecessary at current traffic.

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
| Rate limiter sheds over-limit traffic with 429 + `Retry-After` | ✅ |
| Limiter runs **before** signature verification (unsigned over-limit request → 429, not 401 — proves no HMAC was computed) | ✅ |
| `/healthz` + `/readyz` never rate limited (25 probes at a 2/min limit → all 200) | ✅ |
| Limiter is per-IP; one noisy source does not shed another caller's traffic | ✅ |
| Tracking table stays bounded under 500 rotating source IPs (no memory-exhaustion vector) | ✅ |
| 429s counted as `rate_limited_total`, not folded into `errors_total` | ✅ |
| `fly.toml` parses as valid TOML; `force_https=true`, `min_machines_running=1`, distinct `/healthz` + `/readyz` checks, no secret in `[env]` | ✅ |
| Full Python suite (77 tests incl. golden master) | ✅ |

## Could NOT be verified without real platform access

Stated plainly rather than assumed:

1. **The Docker image has never been built.** The sandbox's proxy denies
   `production.cloudfront.docker.com` (403 on CONNECT), so no base image can be pulled and
   `docker build` cannot run. The Dockerfile is therefore **unbuilt and unrun**. The container's
   *runtime conditions* were reproduced faithfully (non-editable install into `site-packages`, run
   from outside the repo, only the bundle and contract reachable) and everything passed — which is
   what caught the `ingredients_v5.csv` import-time break — but that is a simulation of the
   container, not the container. **Run `docker build` first, before `fly deploy`.**
2. **`fly.toml` has never been parsed by flyctl.** It is valid TOML and the invariants above were
   asserted programmatically, but key *names* and nesting — especially the `[checks]` vs
   `[[http_service.checks]]` split and `[http_service.concurrency]` — are written from the
   documented schema, not validated by the tool that consumes them. Run
   `fly config validate --config ghar_re_service/fly.toml` before deploying.
3. **No Fly.io account, org, app, region, or secret exists.** Nothing was provisioned.
4. **`primary_region = "bom"` is a judgement call**, not a measurement — chosen as the closest
   region to the Indian user base. Confirm it against `fly platform regions`.
5. **The 512MB VM size is an estimate** for the 39-dish golden sample. Re-measure before Phase G's
   810-dish catalogue.
6. **The rate limit has never seen real traffic.** 300/min/IP is a starting point chosen against
   NAT'd Supabase egress, not a measurement. Watch `rate_limited_total` at `/v1/meta` after the
   first real load and tune `GHAR_RE_RATE_LIMIT_PER_MINUTE` accordingly.
7. **`Fly-Client-IP` is trusted on the documented behaviour of fly-proxy**, not on an observed
   request. If Fly does not populate it as documented, the limiter falls back to the socket peer —
   which behind the proxy is the proxy itself, collapsing all callers into one bucket and
   over-limiting. Confirm with one real request's logs after deploying.

## Deferred / TODO

- [ ] **G6 protein-balance pairing gap** (`ghar_re_core/pairing.py`, `compat()`): `protein_cat`
      declares `{dal_lentil, kebab, egg_dish, curry}` but the check only tests `dal_lentil`, so
      curry/kebab plates miss a bonus they were designed to earn. Fixing it **changes
      recommendation output**, so it needs the golden files regenerated in the same PR for the diff
      to be reviewable. Deliberately deferred by the Founder — not part of Phase F.
- [x] ~~Decide the Supabase → Fly reachability approach.~~ **Settled:** public ingress + HMAC (no
      fixed Supabase egress range exists, so private networking and IP allowlisting are both off the
      table). See "Public ingress and the trust boundary" above.
- [ ] Tune `GHAR_RE_RATE_LIMIT_PER_MINUTE` once real traffic volume is known.
- [ ] Consider holding staging to the same secret requirement as production (`config.ts` TODO).
- [ ] Pin the base image by digest once a real build has produced one.
- [ ] Optional, only if bot/DDoS traffic appears: put Cloudflare in front (note in the section
      above — deliberately not built).

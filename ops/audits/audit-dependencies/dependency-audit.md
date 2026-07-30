# Dependency & Security Audit — FooFoo v3

**Skill:** `audit-dependencies` (`.claude/skills/audit-dependencies/SKILL.md`)
**Mode:** REPORT ONLY — this run applies no fixes. Any remediation below
requires explicit human confirmation in a later turn before anything is
installed, removed, or upgraded.
**Date:** 2026-07-30
**Branch:** `claude/foofoo-skills-dotfiles-e93096` @ `e7bb584`

---

## Step 1 — Stack detected

Three independent, unrelated dependency trees were found (no monorepo tooling
ties them together):

| Project root | Manager | Manifest | Lockfile |
|---|---|---|---|
| `mobile/` | npm | `mobile/package.json` | `mobile/package-lock.json` (present) |
| `/` (repo root) | pip (setuptools/PEP 621) | `pyproject.toml` — `ghar-re-core` domain package | none (no `requirements.txt`/`poetry.lock`/`uv.lock`) |
| `ghar_re_service/` | pip (setuptools/PEP 621) | `ghar_re_service/pyproject.toml` — FastAPI hosting shell | none |

Detected: npm, single package at `mobile/`, **Expo SDK 52** (`"expo": "~52.0.0"`)
React Native 0.76.3 app using Expo Router. Two Python packages declare only
floor versions (`>=`) with no lockfile — the audit below reflects the newest
versions resolvable today, not necessarily whatever is actually deployed;
see the caveat in Step 2b.

---

## Step 2 — Security vulnerabilities

### 2a. `mobile/` — `npm audit --json` (ran successfully, registry reachable)

```
CRITICAL: 1  — tar
HIGH:     39 — @expo/cli, @expo/config, @expo/config-plugins, @expo/fingerprint,
               @expo/metro-config, @expo/plist, @expo/prebuild-config,
               @jest/transform, @react-native/babel-plugin-codegen,
               @react-native/babel-preset, @react-native/codegen,
               @react-native/community-cli-plugin, @react-native/dev-middleware,
               @react-native/metro-babel-transformer, @xmldom/xmldom,
               babel-jest, babel-plugin-istanbul, babel-preset-expo,
               brace-expansion, cacache, chromium-edge-launcher, del, expo,
               expo-asset, expo-constants, expo-linking, expo-router,
               expo-splash-screen, glob, jscodeshift, minimatch, node-dir,
               postcss, react-native, rimraf, sucrase, temp, tempy,
               test-exclude
MODERATE: 4  — @expo/bunyan, @expo/rudder-sdk-node, uuid, xcode
LOW:      0
```

Total: 44 advisories across 958 resolved packages (910 prod / 1 dev / 12
optional / 36 peer).

**Every single one of these 44 advisories is transitive**, coming from the
Expo/React Native tooling dependency graph (Metro, `@expo/cli`, Jest/Babel
transform chain, xcode/xmldom used by prebuild), not from application code.
`npm audit` reports exactly **one fix path for all 44**: upgrading the direct
`expo` dependency to `57.0.9`.

```
fixAvailable: { name: "expo", version: "57.0.9", isSemVerMajor: true }
```

This is a **major SDK bump** (Expo 52 → 57 spans 5 SDK majors), not a patch —
it will require its own migration pass (React Native version bump, New
Architecture behavior changes across 5 releases, Expo Router major versions,
re-testing on both platforms) rather than a mechanical `npm audit fix`. This
is flagged for CRITICAL/HIGH per the skill's Step 2 instruction but the "exact
fix command" is not a safe one-liner — recommend scoping it as its own tracked
work package rather than an automatic dependency bump.

Exact command if/when the Founder authorizes the major bump:
```
cd mobile && npx expo install expo@^57.0.9 --fix
```
(then run `npx expo-doctor` and the full typecheck/build before merging.)

### 2b. Python projects — no lockfile, so no fixed install to audit against

Neither `pyproject.toml` pins exact versions (both use floor constraints:
`pyyaml>=6`, `fastapi>=0.110`, `uvicorn>=0.29`, `jsonschema>=4.20`,
`openpyxl>=3.1`, plus `pytest>=8`, `httpx>=0.27`, `ruff>=0.6`, `mypy>=1.11`
in optional extras). There is no `requirements.txt`, `poetry.lock`, or
`uv.lock` in the repo, so **the versions actually running in
production/staging cannot be verified from repository contents alone** —
this is itself a finding (see Step 5).

To still produce a real result rather than fabricating one: resolved the
full declared dependency set (both projects' base + optional-test/lint
extras) into a scratch virtualenv at today's latest compatible versions and
ran `pip-audit` (PyPI reachable — network access confirmed, 200 from
`pypi.org`) against that resolution:

```
Found 8 known vulnerabilities in 2 packages
pip         24.0    → fix 26.1.2 / 25.3 / 26.0 / 26.1  (4 advisories)
setuptools  79.0.1  → fix 83.0.0                         (1 advisory, listed twice)
```

**Zero vulnerabilities found in any of the project's own declared
dependencies** (fastapi, uvicorn, jsonschema, openpyxl, pyyaml, pytest,
httpx, ruff, mypy all resolved clean). The only flagged packages are `pip`
and `setuptools` themselves — bootstrap tooling from the scratch venv, not
project dependencies — included here for transparency, not as real findings.

**Caveat, stated explicitly per the "no fabrication" rule:** this reflects
the newest resolvable versions as of 2026-07-30, not whatever is actually
pinned/deployed today, because no lockfile exists to check against. If the
live Supabase/production service is running older resolved versions than
what `pip` would install today, this audit cannot see that — only a
lockfile (or a `pip freeze` from the actual deployment) would confirm it.

---

## Step 3 — Unused packages (`mobile/`)

Cross-referenced every import in `mobile/src/**` and `mobile/app/**` against
`package.json` dependencies/devDependencies, then checked `app.json`,
`babel.config.js`, and `tsconfig.json` for config-only usage before marking
anything REMOVE.

| Package | Version | Where used (or "nowhere found") | Safe to remove | Command |
|---|---|---|---|---|
| `@opentelemetry/api` | ^1.9.1 | Nowhere — not imported in `src/`/`app/`, not referenced in `app.json`/`babel.config.js`. The project's actual client logger (`src/lib/logger.ts`) is console + AsyncStorage based and has no OTel integration. | **REMOVE** (pending confirmation) | `npm uninstall @opentelemetry/api` |
| `expo-constants` | ~17.0.3 | Not imported directly, but is a standard Expo peer dep other Expo packages read `Constants.expoConfig` through internally; commonly required transitively by `expo-router`/`expo`. | KEEP | — |
| `expo-asset` | ~11.0.1 | Not imported directly; used internally by `expo-font`/`expo-splash-screen` asset loading. | KEEP | — |
| `react-dom` | ^18.3.1 | Not imported directly; required by `react-native-web` for the `web` bundler target declared in `app.json` (`"web": {"bundler": "metro"}`). | KEEP | — |
| `react-native-web` | ^0.19.13 | Not imported directly; required by the same web target. | KEEP | — |
| `react-native-screens` | ~4.1.0 | Not imported directly in app code; required internally by `expo-router`'s native-stack navigator. | KEEP | — |

**Net finding: 1 confirmed unused package** (`@opentelemetry/api`) out of 21
direct dependencies. Everything else that isn't directly imported has a
config- or transitive-dependency justification.

Python projects: every declared dependency (`pyyaml`/`yaml`, `fastapi`,
`jsonschema`, `openpyxl`) has a matching `import` in `ghar_re_core/` or
`ghar_re_service/`. `uvicorn` has no direct `import` (expected — it's invoked
as the ASGI server process, not imported by application code). **No unused
Python packages found.**

---

## Step 4 — Duplicate functionality

Checked the common patterns (date libs, HTTP clients, state management,
animation, icons, forms) against the actual installed set.

**None found.** The dependency surface is small and each concern has exactly
one library: `@tanstack/react-query` (data fetching/cache — no competing
state library), `@supabase/supabase-js` (single API client, no axios/fetch
wrapper alongside it), no date library present at all, no icon library
duplication, no form library. Same for both Python projects — one web
framework (FastAPI), one YAML lib, one spreadsheet lib.

---

## Step 5 — Framework/SDK compatibility

**Expo project** (`mobile/`): SDK version is `~52.0.0`. Cross-checked the
version-sensitive companion packages the skill calls out by name:

| Package | Installed | Expected for SDK 52 | Status |
|---|---|---|---|
| `react-native` | 0.76.3 | 0.76.x | OK |
| `react-native-safe-area-context` | 4.12.0 | 4.12.x | OK |
| `react-native-screens` | ~4.1.0 | ~4.1.x–4.4.x | OK |
| `expo-router` | ~4.0.0 | ~4.0.x | OK |
| Supabase client (`@supabase/supabase-js`) | ^2.45.0 | not SDK-coupled | OK |

Internally consistent for SDK 52 — no cross-version mismatches. The real
finding is currency, not internal mismatch: **Expo SDK 52 is 5 majors behind
the current SDK line (57)**, which is also the entire reason all 44
`npm audit` findings exist (they're all in tooling that ships newer,
non-vulnerable versions starting at SDK 57). This is a currency/EOL risk as
much as a security one — SDK branches fall out of Expo's own support window
over time.

**Python (`ghar_re_service` / `ghar_re_core`)**: both declare
`requires-python = ">=3.11"` consistently. No Node engine field applies
(pure Python service). No version-sensitive companion package issues found.

---

## Findings ranked by severity (top 5)

1. **HIGH — Expo SDK 52 is 5 majors out of date**, and is the single root
   cause of all 44 `npm audit` advisories (1 critical, 39 high, 4 moderate).
   Fix requires a scoped major-upgrade work package (`expo@57.0.9`), not a
   one-line patch — recommend tracking as its own effort with full
   regression testing, not folded into a routine dependency bump.
2. **HIGH (indirectly, via #1) — 1 critical + 39 high transitive
   vulnerabilities**, all resolved by the same SDK bump. No standalone
   critical/high vulnerability exists outside that one upgrade path.
3. **MEDIUM — No lockfile for either Python project** (`pyproject.toml` only,
   floor-version constraints). This means the actual deployed dependency
   versions cannot be verified from the repo, and a future `pip install`
   could silently resolve to different versions than whatever is running
   today. Recommend adding `uv.lock` or pinned `requirements*.txt` for both
   `ghar_re_core`/root and `ghar_re_service/`.
4. **LOW — 1 confirmed unused npm package**, `@opentelemetry/api`, with no
   import or config reference anywhere in `mobile/`.
5. **LOW — 4 moderate npm advisories** (`@expo/bunyan`, `@expo/rudder-sdk-node`,
   `uuid`, `xcode`) — same single fix path (`expo@57.0.9`) as the high/critical
   findings; no separate action needed once #1 is addressed.
6. **INFO — no duplicate-functionality packages found** in either the mobile
   app or either Python project; dependency surface is lean and each concern
   has a single library.

No fixes have been applied. Everything above is presented for the Founder's
review and explicit confirmation before any `npm install`/`uninstall`,
`pip`/`uv` pin, or version bump is executed.

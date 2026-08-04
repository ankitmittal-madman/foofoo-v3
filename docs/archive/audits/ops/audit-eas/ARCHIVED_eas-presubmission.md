# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# Expo & EAS Pre-Submission Audit — FooFoo v3 Mobile

**Skill:** `audit-eas` (`.claude/skills/audit-eas/SKILL.md`, registered as
`audit-eas-presubmission`)
**Mode:** REPORT ONLY — no config was written or changed. Any proposed
change below (e.g. an `eas.json`) requires explicit human confirmation
before being created.
**Date:** 2026-07-30
**Scope:** `mobile/`

---

## Step 1 — Confirmed this is an Expo project

`mobile/app.json` exists with an `"expo"` root key, and `mobile/package.json`
declares `"expo": "~52.0.0"` as a direct dependency. Expo-specific checks
apply.

---

## Step 2 — `app.json` audit

| Item | Status | Notes |
|---|---|---|
| Bundle identifier | **WARNING** | `ios.bundleIdentifier`: `app.foofoo.mobile`, `android.package`: `app.foofoo.mobile` — present, reverse-DNS format, and **consistent** between platforms. Marked WARNING only because it could not be cross-checked against an actual App Store Connect / Play Console record (none accessible from repo) — confirm it matches the registered store listing before submission. |
| App name | PASS | `"FooFoo"` — not a placeholder. |
| Version | PASS | `"0.1.0"` — valid semver. Note: this is a pre-1.0 version string; confirm this is intentional for a first store submission rather than an oversight. |
| Build number | **BLOCKER** | Neither `ios.buildNumber` nor `android.versionCode` is present anywhere in `app.json`. Both are **required by their respective stores** — a submission will be rejected (iOS) or fail upload validation (Android) without them. No prior EAS build history is accessible from this repo to infer the last submitted value, so a starting value cannot be inferred — must be set explicitly (typically `1` if this is the first submission, otherwise higher than whatever was last submitted). |
| iOS deployment target | INFO / not applicable to flag | `ios.deploymentTarget` is not set in `app.json` — Expo SDK 52 / React Native 0.76 default their native project's minimum iOS version (this is generated at prebuild time, not read from `app.json`, for Expo's managed workflow with no `ios/` native folder present). No native `ios/` directory exists in this repo, confirming a fully managed (CNG) workflow — nothing to flag here since there's no custom native override to check. |
| Android `targetSdkVersion` | INFO / not applicable to flag | Same reasoning — no native `android/` directory exists (managed workflow); `targetSdkVersion` is set by the Expo SDK's prebuild templates, not a repo-level config value for SDK 52. **Could not reach a live source to confirm the current Play Store minimum required targetSdkVersion** (no network fetch of Play Console policy pages was attempted for this report — flagging as a manual check item rather than fabricating a number). Separately, SDK 52 is 5 majors behind the current Expo SDK line (see `docs/archive/audits/ops/audit-dependencies/ARCHIVED_dependency-audit.md` Step 5) — worth confirming SDK 52's bundled `targetSdkVersion` still clears the current Play Store minimum before submission. |
| Permissions / usage descriptions | PASS | See Step 3 — no permission-requiring modules are actually installed or used. |

---

## Step 3 — Permissions discovered from actual project usage

```
grep -rE "expo-camera|expo-location|expo-notifications|expo-image-picker|expo-contacts|expo-calendar|expo-media-library" mobile/package.json
```
→ no matches. None of these modules are declared dependencies at all.

```
grep -rlnE "expo-camera|expo-location|expo-notifications|expo-image-picker|expo-contacts|expo-calendar" mobile/src mobile/app
```
→ one match, in `app/(onboarding)/step-2.tsx` — but it is a **code comment**,
not an import or call:

> `"Share my location" GPS card (expo-location, reverse geocoding) was
> DROPPED per the agreed scope — foofoo-v3 has no GPS integration..."`

**Finding: no permission-requiring module is installed or used anywhere in
the app.** Correspondingly, `app.json` declares no
`NSCameraUsageDescription`/`NSLocationWhenInUseUsageDescription`/etc., which
is correct given nothing needs them — **PASS**, not a gap. Nothing to flag
as BLOCKER here, and no stale usage-description cleanup needed either since
none exist.

---

## Step 4 — EAS build profiles

`eas.json` **does not exist** in `mobile/` (or anywhere in the repo).

Checked for a staging/env signal to determine what profiles the project
actually needs: only `mobile/.env.example` exists, with a comment noting
*"no live project ref exists in this repo yet... fill in from the actual
Supabase project when one is provisioned"* — i.e. there is no confirmed
staging vs. production environment split yet at the mobile-app level.

**Finding: BLOCKER for EAS builds specifically** (not for the app generally)
— `eas build`/`eas submit` cannot run at all without an `eas.json` defining
at least one build profile. This blocks any EAS-based build or store
submission today, independent of the other findings above.

Per the skill's own instruction, a proposal is shown here, not written:
a minimal starting profile set, to be created only on explicit confirmation:

```jsonc
// PROPOSED — not written to disk. For Founder review only.
{
  "cli": { "appVersionSource": "remote" },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal"
    },
    "production": {
      "distribution": "store",
      "autoIncrement": true
    }
  },
  "submit": {
    "production": {}
  }
}
```
This is a starting-point proposal only, based on Expo's own default
three-profile convention (no repo-internal staging/production doc was found
to confirm a different, project-specific profile shape is needed) — it
should be reviewed against actual store credentials and Supabase
project/environment plans before being written.

---

## Step 5 — Expo Updates (OTA) configuration

Checked `app.json` for `updates.*` and `runtimeVersion` keys: **none are
present.**

| Item | Status | Impact |
|---|---|---|
| `updates.url` | **WARNING** (not BLOCKER — OTA is opt-in) | Not set. This means the app has **no OTA update channel configured at all** — not a broken OTA setup, but OTA is simply not wired up yet. Not a store-rejection blocker, but worth flagging since `expo-updates` isn't even a declared dependency in `package.json` (checked — absent), so there is currently no way to ship JS-only fixes post-submission without a full store resubmission. |
| `updates.fallbackToCacheTimeout` | N/A | Not applicable while `expo-updates` itself isn't installed — no hang risk exists because there's no update check happening at all. Revisit once/if OTA is added. |
| `runtimeVersion` | N/A | Same — not applicable until `expo-updates` is actually adopted. |

**Finding: OTA is not configured, but this reads as "not yet built" rather
than "broken."** Not a submission blocker. Flagging so it's a deliberate
decision (ship without OTA for v1) rather than an oversight — worth a
one-line confirmation from the Founder either way.

---

## Step 6 — EAS build inspect

```
eas build:inspect --platform ios --profile production
eas build:inspect --platform android --profile production
```

**Could not run** — the `eas` CLI is not installed in this environment
(`which eas` → not found), and no `eas.json` exists to supply a `production`
profile even if it were installed. Stating this explicitly per the skill's
own instruction rather than fabricating output. This step should be re-run
once (a) the EAS CLI is available and (b) `eas.json` exists.

---

## Step 7 — Checklist

| Item | Status | Severity if FAIL | Notes |
|---|---|---|---|
| Bundle identifier present & consistent | PASS | — | `app.foofoo.mobile` both platforms |
| App name not a placeholder | PASS | — | "FooFoo" |
| Version is valid semver | PASS | — | `0.1.0` |
| Build number (`ios.buildNumber`/`android.versionCode`) | **FAIL** | **BLOCKER** | Absent entirely — required by both stores |
| iOS deployment target | N/A | — | Managed workflow, no native override to check |
| Android targetSdkVersion | MANUAL | — | Could not verify against live Play Store policy from this environment; also revisit given SDK 52 is 5 majors behind current |
| Permission usage descriptions match actual usage | PASS | — | No permission-requiring modules installed or used |
| `eas.json` exists with needed build profiles | **FAIL** | **BLOCKER** | File does not exist at all — blocks any EAS build/submit |
| `expo-updates` / OTA configured | WARNING | WARNING | Not configured; reads as intentionally not-yet-built, not broken |
| `eas build:inspect` (ios/android, production) | NOT RUN | — | `eas` CLI unavailable in this environment; no profile to inspect against anyway |

---

## Step 8 — Completion summary

```
Items checked: 10
BLOCKERS: 2  (missing build number, missing eas.json)
WARNINGS: 2  (bundle ID / store-listing cross-check unverifiable here,
              OTA/expo-updates not configured)
MANUAL:   2  (Android targetSdkVersion vs. current Play Store policy,
              eas build:inspect — needs EAS CLI + eas.json first)
```

## Bottom line

**Not ready to submit today.** Two hard blockers: no `ios.buildNumber`/
`android.versionCode` in `app.json`, and no `eas.json` at all (so an EAS
build/submit cannot even be attempted). Both are quick, low-risk fixes once
confirmed by the Founder — this is a configuration gap, not an architectural
one. Permissions are clean (nothing is declared that isn't used, and nothing
is used that isn't declared). OTA is absent but that reads as scope-not-yet-
built rather than a defect. No fixes were applied in this pass — this report
is for review before anything is created or edited.

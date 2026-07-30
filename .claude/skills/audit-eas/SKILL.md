---
name: audit-eas-presubmission
description: >
  Pre-submission audit for Expo + EAS apps before submitting to the App Store
  or Play Store — checks app.json/app.config configuration, EAS build profiles,
  required permissions, and OTA update configuration. Generic — only activates
  its Expo-specific checks if the project is actually an Expo project, and
  discovers required permissions from the project's own feature set rather
  than a fixed list.

  Trigger: slash command /audit-eas only. Does not trigger automatically.
---

# Expo & EAS Pre-Submission Audit Skill

Catches configuration mistakes before "Submit to App Store" — the kind that
get an app bounced in review or silently break OTA updates after launch.

## Skill Authority

This skill provides reusable engineering practices.

It must never override:

- Project Documentation
- Architecture
- Governance
- Founder Decisions
- Project Workflow (APDF)

If the project already defines an approach, the project takes precedence.
## Trigger

This skill activates ONLY when the developer runs:
```
/audit-eas
```
## Activation
- Activation Type: Manual
- Recommended Phase: Repository, Implementation, QA or/and Production

## Step 0 — Self-install check (run once per repo)

```bash
ls .claude/skills/audit-eas-presubmission/SKILL.md 2>/dev/null && echo "INSTALLED" || echo "MISSING"
```

**If MISSING:** fetch from `ankitmittal-madman/dotfiles` →
`.claude/skills/audit-eas-presubmission/SKILL.md` via GitHub MCP, write to the
same path in this repo, commit and push.

**If INSTALLED:** continue below directly.

---

## Step 1 — Confirm this is an Expo project

```bash
cat app.json app.config.js app.config.ts 2>/dev/null
grep '"expo"' package.json 2>/dev/null
```

If none of these exist, tell the user this skill is Expo-specific and doesn't
apply to this project, then stop.

---

## Step 2 — app.json / app.config audit

Check, and report PASS/FAIL/WARNING for each:

- **Bundle identifier** (`ios.bundleIdentifier` / `android.package`) — must be
  present, in reverse-DNS format, and consistent between iOS and Android
- **App name** — present; flag if it looks like a placeholder
  (e.g. contains "test", "untitled", "my app") so the user can confirm it's
  final before submission
- **Version** — `version` field follows semantic versioning (X.Y.Z)
- **Build number** — `ios.buildNumber` and `android.versionCode` are present
  and incremented from the last known submitted build (check git history /
  EAS build history if accessible for the previous value)
- **iOS deployment target** — check `ios.deploymentTarget` if set; flag if
  unusually low (most current apps target iOS 15+, but confirm against what
  the project's own dependencies actually require rather than asserting a
  fixed number)
- **Android targetSdkVersion** — check against current Play Store
  requirements; **search the web for the current minimum required
  targetSdkVersion** rather than relying on a hardcoded number, since this
  changes yearly
- **Permissions and usage descriptions** — see Step 3

---

## Step 3 — Discover required permissions from the project itself (do not assume a fixed list)

Don't assume which permissions are needed. Discover them from what the app
actually uses:

```bash
# Look for Expo modules that require permissions
grep -rE "expo-camera|expo-location|expo-notifications|expo-image-picker|expo-contacts|expo-calendar|expo-media-library" package.json

# Look for actual usage in code (a dependency being installed doesn't 
# guarantee it's used — and usage confirms the permission description 
# needs to be accurate to what it's used FOR)
grep -rln "expo-camera\|expo-location\|expo-notifications\|expo-image-picker" --include=*.{ts,tsx,js,jsx} . | grep -vE "node_modules"
```

For every permission-requiring module found in actual use, verify the
corresponding usage description string exists in `app.json`/`app.config`:
- Camera → `NSCameraUsageDescription` (iOS) / camera permission (Android)
- Location → `NSLocationWhenInUseUsageDescription` (iOS) / location permission (Android)
- Notifications → notification permission setup
- Photo library → `NSPhotoLibraryUsageDescription`
- Contacts, calendar, microphone, etc. — same pattern

Flag any permission-requiring module in use **without** a corresponding usage
description as **BLOCKER** — this causes App Store rejection.

Also flag the reverse: a usage description present for a permission the app
no longer actually uses (stale config) — lower severity, just a cleanup note.

---

## Step 4 — EAS build profiles

```bash
cat eas.json 2>/dev/null
```

Check for the presence of build profiles appropriate to the project's actual
deployment setup (discover this from `.env*` files and any staging/production
documentation found in the repo, rather than assuming exactly three profiles
named development/staging/production):

- Does each profile point to the right distribution type
  (`internal` for dev/staging, `store` for production)?
- Does each profile's environment configuration match an actual `.env` file
  or secrets source found in the project?

If `eas.json` is missing entirely, or missing a profile that the project
clearly needs (e.g. there's a `.env.staging` but no `staging` profile), flag
it and propose the missing profile — but show the proposal before writing it.

---

## Step 5 — Expo Updates (OTA) configuration

Check `app.config` for `expo-updates` configuration:
- `updates.url` is set and points to a real EAS update endpoint
- `updates.fallbackToCacheTimeout` is set (flag if missing — without it,
  the app can hang on a slow network waiting for an update check)
- `runtimeVersion` is configured (flag if missing — without it, OTA updates
  can silently fail to apply or apply incorrectly across native version changes)

---

## Step 6 — Run EAS build inspect

```bash
eas build:inspect --platform ios --profile production 2>&1
eas build:inspect --platform android --profile production 2>&1
```

(Run only for platforms the project actually targets — check `app.json` for
which platforms are configured.)

Report all warnings and errors verbatim.

---

## Step 7 — Write the checklist output

`eas-presubmission.md`:

| Item | Status | Severity if FAIL | Notes |
|---|---|---|---|

Every FAIL must be marked **BLOCKER** (will likely cause rejection or break
OTA) or **WARNING** (should fix, won't necessarily block submission).

---

## Step 8 — Completion summary

```
## Audit completed [date]
Items checked: N
BLOCKERS: N
WARNINGS: N
```

Commit:
```bash
git add eas-presubmission.md app.json app.config.js eas.json 2>/dev/null
git commit -m "chore: EAS pre-submission audit — [one-line summary]"
git push
```

Tell the user clearly: is this app ready to submit, or are there blockers?
Lead with that, then the detail.

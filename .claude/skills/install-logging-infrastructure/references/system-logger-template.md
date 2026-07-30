# System Logger — Reference Template

Adapt this pattern to the target project's stack. Do not copy variable names
like "FooFoo" or fixed table names — replace with the actual project name and
discovered schema.

## Purpose

A single structured logger that all application code uses instead of raw
`console.log`. In development: human-readable console output. In production:
errors forward to the error tracker (Sentry or equivalent, if present),
warnings become breadcrumbs, info/debug are suppressed remotely but persisted
locally for an in-app debug view.

## Design requirements

1. **Single dispatcher function** taking `(level, module, message, meta?)`
2. **Four levels**: DEBUG (dev only), INFO, WARN, ERROR
3. **Module tag** — caller identifies which part of the app logged this
   (e.g. `'PLANS-REPO'`, `'AUTH'`) so logs are filterable
4. **Structured meta object** — never string-concatenate data into the
   message; pass it as a separate object so it can be parsed later
5. **Local persistence** (circular buffer, ~500 entries) for an in-app debug
   view — implementation depends on platform:
   - React Native → AsyncStorage
   - Web-only → localStorage or IndexedDB
   - Pure backend service → skip local persistence, rely on the platform's
     own log aggregation (stdout capture, etc.)
6. **Error tracker forwarding** — only if the project actually has Sentry/
   Bugsnag/Rollbar etc. installed (checked in Step 2 of the parent skill).
   If none present, implement the dispatcher to no-op gracefully on this
   path and flag to the user that remote error visibility is currently
   absent.
7. **Timezone-aware timestamps if relevant** — if the project has a primary
   user timezone/market (discover from existing code, e.g. IST-shifting
   logic already present elsewhere), match that convention. Otherwise use
   UTC or local system time.
8. **Privacy rule, always included as a comment block at the top of the
   file**: never log values from fields the project's own data model treats
   as sensitive (discover the actual sensitive field names from the project's
   schema/docs — do not hardcode a fixed list from an unrelated project).
   Log only IDs, counts, durations, and non-sensitive status/category values.

## Public API shape

```
Logger.debug(module, message, meta?)
Logger.info(module, message, meta?)
Logger.warn(module, message, meta?)
Logger.error(module, message, meta?)
Logger.getLogs() → Promise<string>   // formatted text, for an in-app debug view
Logger.clearLogs() → Promise<void>
```

## Output line format

```
[HH:MM:SS] [LEVEL] [MODULE] message {meta}
```

Generate the actual TypeScript/JavaScript file following this design,
adapted to the detected project's runtime and conventions discovered during
Step 2 of the parent skill (platform, error tracker presence, persistence
layer, timezone convention).

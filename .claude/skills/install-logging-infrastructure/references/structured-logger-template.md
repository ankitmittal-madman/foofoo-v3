# Structured (Lightweight) Logger — Reference Template

A second, lighter logger for hot-path code where full local persistence
(e.g. AsyncStorage I/O on every call) is too expensive — typically
client-side code in performance-sensitive paths.

## Design requirements

- Same four levels as the System Logger (debug/info/warn/error)
- Forwards directly to the error tracker (if present) without local
  persistence
- Dev-mode console output with a light visual marker (emoji or prefix) so
  it's visually distinguishable from System Logger output
- Header comment must clearly state: this is for hot paths; the full
  System Logger is the default choice elsewhere
- Same privacy rule as the System Logger — discover the project's actual
  sensitive fields, never hardcode an unrelated project's field names
- Must be safe to import only in the runtime it's meant for — if the
  project has both client and serverless/edge function code, state clearly
  in the header which runtime this file is for and that it must not be
  imported in the other (e.g. a browser-oriented logger must not be
  imported into a Deno/Node edge function, and vice versa)

## Public API shape

```
logger.debug(event, context?, duration_ms?)
logger.info(event, context?, duration_ms?)
logger.warn(event, context?)
logger.error(event, context?)
```

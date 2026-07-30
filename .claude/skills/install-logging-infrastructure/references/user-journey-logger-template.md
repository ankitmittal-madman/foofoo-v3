# User Journey Logger — Reference Template

Adapt this pattern to the target project. This logger exists for ONE
audience: a non-technical PM or stakeholder who wants to read, in plain
English, what a specific user did and why the app responded the way it did
— without reading code or raw database tables.

## Purpose

Per-user, human-readable narrative log of significant actions and (if
applicable) engine/algorithm decisions made on their behalf. Development and
QA aid — exists to make debugging and product review possible without a
database client.

## Design requirements

1. **Per-user circular log** (e.g. max 200 entries), keyed by a truncated
   user ID so logs are identifiable without exposing full UUIDs in casual
   viewing
2. **Plain English, not technical** — every entry should read like a
   sentence a PM would say out loud, not a log line. Compare:
   - Bad: `action=swipe slot=breakfast pos=0`
   - Good: `User swiped on Breakfast (Idli Sambar at position 1) → Browsing carousel`
3. **Categories** — discover the project's actual user-action categories
   rather than assuming a fixed set. Common categories worth considering:
   onboarding/setup steps, core engine decisions (if applicable), discrete
   user actions (gestures, taps, submissions), system/account events.
4. **Timestamp formatting** matching the project's primary market timezone
   convention if one exists (discover from other code), otherwise local/UTC.
5. **Decision-logging method** (only if the project has a computation/
   decision engine — see the parent skill's Step 5): a dedicated method that
   logs the engine's choice, the alternatives it considered with their
   scores, and a plain-English reasoning string. This is the single most
   valuable entry type for a non-technical PM, since it answers "why did the
   app do that" without any code reading required.

   Structural shape (adapt field names to the actual engine's real output):
   ```
   logEngineDecision(userId, decisionContext, winner, alternatives, reasoningText)
   ```
   Output should read like:
   ```
   App chose: WINNER NAME (Score: X.XX)

   [reasoning sentence explaining the key factors]

   Top alternatives the app considered:
     2. Alternative A — Score: X.XX (why it lost)
     3. Alternative B — Score: X.XX (why it lost)
   ```

6. **Action-logging method** for discrete user actions — adapt the actual
   vocabulary to what the project's UI actually supports (discover from
   gesture handlers / event handlers in the codebase). Each action should
   map to a short narrative template, not a raw event name.

## Public API shape (adapt method names to the project's actual concepts)

```
Logger.logSetupStep(userId, stepNumber, stepName, choices)
Logger.logEngineDecision(userId, context, winner, alternatives, reasoning)  // if applicable
Logger.logUserAction(userId, action, target, context)
Logger.getFullLog(userId) → Promise<string>
Logger.clearLog(userId) → Promise<void>
```

Generate the actual file adapted to this project's real action vocabulary,
real decision-engine shape (if any), and real timezone convention.

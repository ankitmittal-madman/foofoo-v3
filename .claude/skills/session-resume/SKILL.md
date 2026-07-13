---
name: session-resume
description: Controls HOW Claude Code reconstructs a project's execution state at the start of a session — before any design, prompt, migration, or implementation work. Prevents shallow resumption by requiring the repository and docs/project-history/ to be actually read (not searched or inferred), disclosing exactly what was fully read vs. partially read vs. only indexed, and producing a Session Resume Report that the Founder must approve before any new work begins. Trigger on /session-resume, "resume this session", "reconstruct project state", "where did we leave off", or automatically at the start of any Claude Code session on a repo with docs/project-history/ present. Never silently substitutes search snippets or conversation memory for actually reading repository files.
---

# Session Resumption Protocol (Claude Code)

Repo-side counterpart to the `session-resume` claude.ai personal skill. This skill governs
Claude Code sessions specifically — where the repository and its committed documentation are
the only authority, not chat memory, not prior-session assumptions.

## Core rule

**Conversation memory is not authoritative. The repository is.** Every session starts fresh.
Nothing from a previous chat — including a summary a person pastes in — should be trusted over
what the repo actually contains right now. If a person's message asserts a state ("we finished
WP-3B"), treat it as a claim to verify, not a fact to record.

## Authority hierarchy

When sources disagree, this order wins — never reversed:

## STEP 5 — Wait

Stop. Do not generate work packages, Claude Code prompts, migrations, or implementation plans
until the Founder/user explicitly approves proceeding from the report.

## Permanent rules

- Never use search-tool snippets as a substitute for reading a file in full.
- Never assume repository state, database state, or migration state — always discover via
  actual tool calls.
- Always disclose confidence and always distinguish fully read / partially read / indexed only.
- Never say "reviewed" unless actually reviewed.
- If reading requires multiple sessions to do properly, stop, produce a Reading Plan, and wait
  — don't silently optimize for speed by skimming instead.
- The repository and its committed documentation are the only architectural authority. The
  database is built *from* documentation — never reverse-engineer documentation from the
  database's current shape.
- `docs/project-history/` (or wherever the knowledge-book hierarchy lives per
  repo-structure-setup) is the execution authority for what happened across sessions.

## Handoff from claude.ai

If a session opens with a message referencing a claude.ai `session-resume` report (e.g. "Last
known focus from claude.ai: ..."), treat that line as a lead to verify in Step 2–3, not as
confirmed state. It's useful for knowing where to look first, not as a substitute for looking.

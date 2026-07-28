#!/usr/bin/env bash
# check-knowledge-book.sh
#
# Runs at the end of a Claude Code session (Stop hook). Mechanically checks
# whether this session touched code/DB/config/docs without also touching
# KNOWLEDGE.html, and prints a warning if so. This replaces relying on
# Claude remembering a markdown instruction every session — the check
# happens whether or not the model chose to think about it.
#
# Exit code 0 always (never blocks the session) — this is advisory, not
# enforcement-by-refusal, per CLAUDE.md's "report the gap, don't invent or
# force" philosophy. It just makes the gap impossible to miss.
#
# FIX (2026-07-28): the original version only inspected UNCOMMITTED changes
# (git diff HEAD + --cached). The actual workflow commits every change before
# the turn ends, so at Stop time the tree was always clean and this hook never
# fired — session-knowledge-doc silently never ran. It now inspects the
# session's COMMITTED work too (this branch vs its base on origin/main), which
# is where the real changes live, plus any uncommitted remainder.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# --- Determine the branch base (what this branch added on top of main) --------
# Prefer the merge-base with origin/main; fall back to origin/main, then to the
# previous commit. Any failure degrades gracefully to "no committed diff".
BASE=""
if git rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
  BASE="$(git merge-base HEAD origin/main 2>/dev/null || git rev-parse origin/main 2>/dev/null || true)"
fi
if [ -z "$BASE" ]; then
  BASE="$(git rev-parse --verify --quiet HEAD~1 2>/dev/null || true)"
fi

# Committed changes on this branch beyond its base (the session's real work).
COMMITTED_FILES=""
if [ -n "$BASE" ]; then
  COMMITTED_FILES="$(git diff --name-only "$BASE" HEAD 2>/dev/null || true)"
fi

# Uncommitted changes (working tree + staged) — catches work not yet committed.
UNCOMMITTED_FILES="$(git diff --name-only HEAD 2>/dev/null || true)
$(git diff --name-only --cached HEAD 2>/dev/null || true)"

CHANGED_FILES="$(printf '%s\n%s\n' "$COMMITTED_FILES" "$UNCOMMITTED_FILES" | sort -u)"

if [ -z "$(echo "$CHANGED_FILES" | tr -d '[:space:]')" ]; then
  # Nothing changed at all (committed or uncommitted) — nothing to check.
  exit 0
fi

# Did anything substantive (code, SQL, docs, config) change?
SUBSTANTIVE_CHANGED="$(echo "$CHANGED_FILES" \
  | grep -E '\.(ts|tsx|js|jsx|py|sql|md|docx|yaml|yml|json|toml)$' \
  | grep -v 'KNOWLEDGE.html' \
  | grep -v -E '(^|/)(deno\.lock|package-lock\.json)$' || true)"

# Did KNOWLEDGE.html change (in the branch work or uncommitted)?
KNOWLEDGE_CHANGED="$(echo "$CHANGED_FILES" | grep -c 'KNOWLEDGE.html' || true)"

if [ -n "$SUBSTANTIVE_CHANGED" ] && [ "$KNOWLEDGE_CHANGED" -eq 0 ]; then
  WARNING="$(cat <<EOF

⚠️  KNOWLEDGE BOOK CHECK (session-knowledge-doc skill)
   This session changed the files below (committed and/or uncommitted) but did
   NOT update KNOWLEDGE.html:
$(echo "$SUBSTANTIVE_CHANGED" | sed 's/^/     - /')
   Per CLAUDE.md Session End: update KNOWLEDGE.html now (per
   .claude/skills/session-knowledge-doc/SKILL.md), or state explicitly why
   this session's changes don't warrant a new entry.
EOF
)"
  # Print to stdout (Stop-hook feedback surfaces in the transcript in this
  # environment — confirmed this session via the global git-check hook) AND
  # persist to a file as a durable backup.
  echo "$WARNING"
  echo "$WARNING" >> .claude/hooks/knowledge-book-warnings.log
fi

exit 0

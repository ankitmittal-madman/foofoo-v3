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

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Files changed in the working tree since the last commit on this branch,
# plus anything already staged — covers a session's actual edits regardless
# of whether they were committed yet.
CHANGED_FILES="$(git diff --name-only HEAD 2>/dev/null || true)"
CHANGED_FILES="${CHANGED_FILES}
$(git diff --name-only --cached HEAD 2>/dev/null || true)"

if [ -z "$(echo "$CHANGED_FILES" | tr -d '[:space:]')" ]; then
  # Nothing changed at all this session — nothing to check.
  exit 0
fi

# Did anything substantive (code, SQL, docs) change?
SUBSTANTIVE_CHANGED="$(echo "$CHANGED_FILES" | grep -E '\.(ts|tsx|js|jsx|sql|md|docx)$' | grep -v 'KNOWLEDGE.html' || true)"

# Did KNOWLEDGE.html change?
KNOWLEDGE_CHANGED="$(echo "$CHANGED_FILES" | grep -c 'KNOWLEDGE.html' || true)"

if [ -n "$SUBSTANTIVE_CHANGED" ] && [ "$KNOWLEDGE_CHANGED" -eq 0 ]; then
  WARNING="$(cat <<EOF

⚠️  KNOWLEDGE BOOK CHECK (session-knowledge-doc skill)
   This session changed files below but did NOT update KNOWLEDGE.html:
$(echo "$SUBSTANTIVE_CHANGED" | sed 's/^/     - /')
   Per CLAUDE.md Session End: update KNOWLEDGE.html now, or state
   explicitly why this session's changes don't warrant a new entry.
EOF
)"
  # Print to stdout (in case a real terminal session sees it) AND persist
  # to a file. Confirmed by direct testing (2026-07-19): hook stdout from
  # Claude Code does not reliably surface in the chat transcript in this
  # environment — the canary test only became visible because it wrote to
  # a file that could be read back in a later message. This mirrors that.
  echo "$WARNING"
  echo "$WARNING" >> .claude/hooks/knowledge-book-warnings.log
fi

exit 0

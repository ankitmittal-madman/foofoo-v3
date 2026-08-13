#!/usr/bin/env bash
# scripts/install-git-hooks.sh
#
# Points this clone's git hooks at the versioned .githooks/ directory.
#
# WHY AN INSTALLER IS NEEDED AT ALL
# Git never versions .git/hooks — it is local to a clone and is not part of the
# repository's contents. In a normal setup that just means "run this once after
# cloning." Here it matters more: the working environments are Codespaces and
# Claude Code web containers, which are rebuilt from a fresh clone regularly, so
# an uninstalled hook is the default state rather than a rare one. Keeping the
# hook itself in .githooks/ (which IS versioned) and flipping git's hooksPath at
# it means the hook travels with the repo and this script only has to set one
# config value.
#
# Safe to re-run: setting the same config value twice is a no-op.
# Idempotent by design, because the Claude Code SessionStart hook runs it at the
# start of every session (see .claude/settings.json) so a fresh container arms
# itself with no human step.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

if [ ! -d .githooks ]; then
  echo "install-git-hooks: no .githooks/ directory found — nothing to install."
  exit 0
fi

# Make sure every hook is executable. A hook without the executable bit is
# silently ignored by git, which looks exactly like "the hook did not fire."
chmod +x .githooks/* 2>/dev/null || true

CURRENT="$(git config --get core.hooksPath 2>/dev/null || true)"

if [ "$CURRENT" = ".githooks" ]; then
  # Already armed. Stay quiet — this runs at every session start and should not
  # add noise to a session that has nothing to do with hooks.
  exit 0
fi

git config core.hooksPath .githooks

echo "✅ Git hooks installed (core.hooksPath → .githooks)."
echo "   The pre-commit hook now keeps Python style in sync with re-ci.yml."
echo "   To disable:  git config --unset core.hooksPath"

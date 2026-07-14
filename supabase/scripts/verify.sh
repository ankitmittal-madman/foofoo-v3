#!/usr/bin/env bash
# WP-8B — backend scaffold verification. Runs formatter check, linter, type-check, and tests.
# Usage: (from repo root) bash supabase/scripts/verify.sh
set -euo pipefail
cd "$(dirname "$0")/.."   # -> supabase/
echo "== deno fmt --check =="; deno fmt --check
echo "== deno lint =="; deno lint
echo "== deno check =="; deno check functions/_shared/mod.ts
echo "== deno test =="; deno test --allow-env functions/_tests/
echo "ALL CHECKS PASSED"

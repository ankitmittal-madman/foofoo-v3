#!/usr/bin/env bash
# WP-8B — generate TypeScript types from the live schema (read-only).
# Writes functions/_shared/types/database.types.ts. Run whenever the schema changes so the type
# layer catches drift at build time (DOC-P4-00 §21). Requires the Supabase CLI + a linked project
# or SUPABASE_PROJECT_REF. This script is NOT run automatically and makes NO schema changes.
set -euo pipefail
cd "$(dirname "$0")/.."   # -> supabase/
: "${SUPABASE_PROJECT_REF:?set SUPABASE_PROJECT_REF (staging/canonical project) first}"
supabase gen types typescript --project-id "$SUPABASE_PROJECT_REF" --schema public --schema re_engine \
  > functions/_shared/types/database.types.ts
echo "wrote functions/_shared/types/database.types.ts"

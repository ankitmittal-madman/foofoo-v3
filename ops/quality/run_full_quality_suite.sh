#!/usr/bin/env bash
#
# Phase 19 — single-command quality gate for Ghar.
#
# Runs the entire production-quality program (inventory, static analysis, unit + service tests,
# contract, recommendation behaviour, API/security, planning surfaces, chaos, performance,
# secrets scan, database probe, edge-function probe, headless UI), collects all artifacts into a
# single timestamped folder under ops/quality/reports/<timestamp>/, and prints the launch verdict.
#
# Usage:
#   ops/quality/run_full_quality_suite.sh            # full run
#   ops/quality/run_full_quality_suite.sh --quick    # skip the perf benchmark
#
# Optional environment to unlock the gated suites:
#   DATABASE_URL / SUPABASE_DB_URL   -> enables the live database checks (Phase 7)
#   GHAR_WEB_URL                     -> enables the headless browser + a11y checks (Phase 9-11)
#   (install Deno)                   -> enables the edge-function tests (Phase 6)
#
# Exit code: 0 if launchable for the surfaces verifiable here, non-zero if a P0 test failed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

export PYTHONPATH="${REPO_ROOT}:${REPO_ROOT}/ghar_re_service${PYTHONPATH:+:${PYTHONPATH}}"

echo "Ghar Quality Suite — repo ${REPO_ROOT}"
echo "git HEAD: $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo

python3 "${SCRIPT_DIR}/runner/orchestrator.py" "$@"
rc=$?

echo
echo "Triage (latest report):"
python3 "${SCRIPT_DIR}/runner/report_reader.py" || true

exit ${rc}

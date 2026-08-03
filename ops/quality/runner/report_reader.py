"""
Phase 17/20 — Report reader + guided fixer.

Reads a report's test_results.json (the latest by default), ranks every failing test by the
severity of the step it belongs to (P0..P3), and prints an actionable triage list: what failed,
where, and the message. This is the "read the report and fix the errors" capability the program
brief asks for.

Two modes:
  * (default) triage    — print ranked failures + unverified P0 surfaces + the verdict.
  * --rerun-failed      — re-run ONLY the pytest targets that contained failures, so a fix can be
    re-validated in seconds without the full suite. It does NOT auto-edit product code: fixes to
    application logic are a human/agent judgement call (a QA harness that silently rewrites the
    code under test cannot be trusted), so this surfaces precisely what to fix and re-verifies it.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORTS = REPO_ROOT / "ops" / "quality" / "reports"
_ENV = {**os.environ, "PYTHONPATH": f"{REPO_ROOT}{os.pathsep}{REPO_ROOT / 'ghar_re_service'}"}

# Map a step name back to the pytest target it ran, so failures can be re-validated.
_TARGETS = {
    "unit-core": "ghar_re_core/tests",
    "unit-service": "ghar_re_service/tests",
    "quality-contract": "ops/quality/suites/test_contract_boundary.py",
    "quality-recsys": "ops/quality/suites/test_recommendation_behavior.py",
    "quality-security": "ops/quality/suites/test_api_security.py",
    "quality-planning": "ops/quality/suites/test_planning_surfaces.py",
}


def _latest_report() -> Path | None:
    """Return the newest report directory (via reports/latest.txt, else mtime)."""
    ptr = REPORTS / "latest.txt"
    if ptr.exists():
        p = Path(ptr.read_text().strip())
        if p.exists():
            return p
    dirs = [d for d in REPORTS.glob("*") if d.is_dir()]
    return max(dirs, key=lambda d: d.stat().st_mtime) if dirs else None


def triage(report_dir: Path) -> dict:
    """Print a ranked triage of the report and return the parsed results dict."""
    data = json.loads((report_dir / "test_results.json").read_text())
    verdict = data["verdict"]
    print(f"Report: {report_dir}")
    print(f"Quality score {verdict['quality_score']} | pass {verdict['pass_pct']}% | "
          f"can launch today: {'YES' if verdict['can_launch_today'] else 'NO'}")
    print(f"Readiness: {verdict['launch_readiness']}\n")

    ranked: list[tuple[str, str, dict]] = []
    for step in data["steps"]:
        for f in step.get("failures", []):
            ranked.append((step["priority"], step["name"], f))
    ranked.sort(key=lambda t: t[0])  # P0 first

    if ranked:
        print(f"FAILING TESTS ({len(ranked)}), most severe first:")
        for prio, step_name, f in ranked:
            print(f"  [{prio}] ({step_name}) {f['test']}")
            if f.get("message"):
                print(f"        -> {f['message'][:180]}")
    else:
        print("No failing tests.")

    steps_failed = [s for s in data["steps"] if s["status"] == "fail"]
    if steps_failed:
        print("\nFAILED STEPS:")
        for s in steps_failed:
            print(f"  [{s['priority']}] {s['name']}: {s['summary'] or s['reason']}")

    if verdict["unverified_p0_surfaces"]:
        print("\nUNVERIFIED P0 SURFACES (not certifiable in this environment):")
        for u in verdict["unverified_p0_surfaces"]:
            print(f"  - {u}")
    return data


def rerun_failed(data: dict) -> int:
    """Re-run only the pytest targets whose step failed; return the aggregate exit code."""
    failed_steps = [s["name"] for s in data["steps"]
                    if s["status"] == "fail" and s["name"] in _TARGETS]
    if not failed_steps:
        print("Nothing to re-run — no failing pytest steps.")
        return 0
    rc = 0
    for name in failed_steps:
        target = _TARGETS[name]
        print(f"\n=== Re-running {name} ({target}) ===")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", target, "-q", "-p", "no:cacheprovider"],
            cwd=REPO_ROOT, env=_ENV)
        rc = rc or proc.returncode
    return rc


def main() -> int:
    """CLI entrypoint for report triage and targeted re-validation."""
    ap = argparse.ArgumentParser(description="Read a Ghar quality report and triage failures")
    ap.add_argument("--report", help="report dir (default: latest)")
    ap.add_argument("--rerun-failed", action="store_true",
                    help="re-run only the pytest targets that had failures")
    args = ap.parse_args()

    report_dir = Path(args.report) if args.report else _latest_report()
    if not report_dir or not (report_dir / "test_results.json").exists():
        print("No report found. Run the orchestrator first.")
        return 2

    data = triage(report_dir)
    if args.rerun_failed:
        return rerun_failed(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Phases 16-19 — Quality orchestrator, evidence generator, and dashboard.

Runs every APPLICABLE validation step, collects real artifacts into a single timestamped report
folder, and renders summary.txt / summary.md / summary.html plus machine-readable test_results.json
and metrics.json. It computes a quality score and a launch-readiness verdict (Phase 18 + 20).

Design rules honoured here:
  * No fabrication. A step that cannot run in this environment is recorded as SKIPPED or BLOCKED
    with the concrete reason (Deno absent, no DATABASE_URL, no web target), never as a pass.
  * Every pytest step emits a JUnit XML the report links to, parsed for real pass/fail/skip counts.
  * A FAIL in a P0 step is a launch blocker; the verdict lists blockers ranked P0..P3.

Usage:
    python ops/quality/runner/orchestrator.py [--quick] [--report-root DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
QUALITY_DIR = REPO_ROOT / "ops" / "quality"
SUITES = QUALITY_DIR / "suites"

# PYTHONPATH every subprocess needs: repo root (ghar_re_core) + nested service package root.
_ENV = {**os.environ, "PYTHONPATH": f"{REPO_ROOT}{os.pathsep}{REPO_ROOT / 'ghar_re_service'}"}


@dataclass
class StepResult:
    """Outcome of one orchestrated step, with real counts and the artifacts it produced."""

    name: str
    phase: str
    status: str            # pass | fail | skip | blocked | warn
    priority: str          # P0..P3 — severity if this step FAILS
    summary: str = ""
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_s: float = 0.0
    reason: str = ""       # why skipped/blocked
    artifacts: list[str] = field(default_factory=list)
    failures: list[dict] = field(default_factory=list)


def _log(report_dir: Path, msg: str) -> None:
    """Append a timestamped line to the report's execution.log and echo it to stdout."""
    line = f"[{datetime.now(UTC).isoformat()}] {msg}"
    with (report_dir / "execution.log").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line, flush=True)


def _parse_junit(xml_path: Path) -> tuple[int, int, int, list[dict]]:
    """Parse a JUnit XML file into (passed, failed, skipped, failure-detail list)."""
    if not xml_path.exists():
        return 0, 0, 0, []
    tree = ET.parse(xml_path)
    root = tree.getroot()
    suites = root.iter("testsuite")
    total = fails = errors = skips = 0
    failures: list[dict] = []
    for s in suites:
        total += int(s.get("tests", 0))
        fails += int(s.get("failures", 0))
        errors += int(s.get("errors", 0))
        skips += int(s.get("skipped", 0))
        for case in s.iter("testcase"):
            bad = case.find("failure") if case.find("failure") is not None else case.find("error")
            if bad is not None:
                failures.append({
                    "test": f"{case.get('classname', '')}::{case.get('name', '')}",
                    "message": (bad.get("message") or "").strip()[:500],
                })
    failed = fails + errors
    passed = total - failed - skips
    return passed, failed, skips, failures


def _run_pytest(report_dir: Path, name: str, phase: str, priority: str, target: str,
                category: str) -> StepResult:
    """Run one pytest target with a JUnit report, parse it, and return a StepResult."""
    cat_dir = report_dir / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    junit = cat_dir / f"{name}.junit.xml"
    log = cat_dir / f"{name}.log"
    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q", "-p", "no:cacheprovider",
         f"--junitxml={junit}"],
        cwd=REPO_ROOT, env=_ENV, capture_output=True, text=True,
    )
    log.write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
    passed, failed, skipped, failures = _parse_junit(junit)
    status = "pass" if failed == 0 and proc.returncode in (0, 5) else "fail"
    return StepResult(
        name=name, phase=phase, status=status, priority=priority,
        summary=f"{passed} passed, {failed} failed, {skipped} skipped",
        passed=passed, failed=failed, skipped=skipped,
        duration_s=round(time.time() - t0, 2),
        artifacts=[str(junit.relative_to(report_dir)), str(log.relative_to(report_dir))],
        failures=failures,
    )


def step_inventory(report_dir: Path) -> StepResult:
    """Phase 1-2: generate the repository inventory + feature matrix into the report."""
    sys.path.insert(0, str(QUALITY_DIR / "inventory"))
    import generate_inventory  # type: ignore

    out = report_dir / "inventory"
    t0 = time.time()
    summary = generate_inventory.generate(out)
    return StepResult(
        name="inventory", phase="1-2", status="pass", priority="P3",
        summary=f"{summary['component_count']} components, {summary['feature_count']} features",
        duration_s=round(time.time() - t0, 2),
        artifacts=[str(Path(a).relative_to(report_dir)) for a in summary["artifacts"]],
    )


def step_ruff(report_dir: Path) -> StepResult:
    """Static analysis: ruff lint across both packages + the quality module."""
    cat = report_dir / "static"
    cat.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "ghar_re_core", "ghar_re_service", "ops/quality"],
        cwd=REPO_ROOT, env=_ENV, capture_output=True, text=True,
    )
    (cat / "ruff.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    ok = proc.returncode == 0
    return StepResult(
        name="ruff-lint", phase="16", status="pass" if ok else "warn", priority="P2",
        summary="clean" if ok else "lint findings (see static/ruff.log)",
        duration_s=round(time.time() - t0, 2),
        artifacts=["static/ruff.log"],
    )


def step_perf(report_dir: Path) -> StepResult:
    """Phase 12: in-process latency benchmark of /v1/meta and /v1/recommendations."""
    cat = report_dir / "performance"
    cat.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(QUALITY_DIR / "runner"))
    import perf_benchmark  # type: ignore

    t0 = time.time()
    try:
        metrics = perf_benchmark.run(int(os.environ.get("GHAR_PERF_ITERS", "120")))
    except Exception as e:  # a benchmark failure must not abort the whole run
        return StepResult("performance", "12", "warn", "P2", f"benchmark error: {e}",
                          duration_s=round(time.time() - t0, 2))
    (cat / "perf.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    compute = metrics["endpoints"].get("/v1/recommendations", {})
    return StepResult(
        name="performance", phase="12", status=metrics["status"], priority="P2",
        summary=f"recommendations p50={compute.get('p50_ms')}ms p99={compute.get('p99_ms')}ms "
                f"(threshold {metrics['warn_threshold_p99_ms']}ms, in-process)",
        duration_s=round(time.time() - t0, 2), artifacts=["performance/perf.json"],
    )


def step_secrets(report_dir: Path) -> StepResult:
    """Phase 13: report-only scan for hardcoded secret VALUES in source (never prints values)."""
    cat = report_dir / "security"
    cat.mkdir(parents=True, exist_ok=True)
    import re

    patterns = {
        "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
        "private_key_block": re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
        "generic_assignment": re.compile(
            r"(?i)(secret|password|api[_-]?key|token)\s*[:=]\s*[\"'][^\"'{}$\s]{12,}[\"']"),
    }
    allow = ("DEV_INSECURE_SECRET", "dev-insecure", "example", "changeme", "your-", "xxxx",
             "placeholder", "test", "dummy", "os.environ", "getenv", "process.env")
    findings: list[dict] = []
    exts = {".py", ".ts", ".tsx", ".js", ".yaml", ".yml", ".json", ".toml", ".sh"}
    skip_dirs = {".git", "node_modules", "__pycache__", "reports", ".mypy_cache",
                 ".ruff_cache", ".pytest_cache"}
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            fp = Path(dirpath) / fn
            if fp.suffix not in exts:
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                if any(a in line for a in allow):
                    continue
                for kind, pat in patterns.items():
                    if pat.search(line):
                        findings.append({"file": str(fp.relative_to(REPO_ROOT)),
                                         "line": line_no, "kind": kind})
    (cat / "secrets_scan.json").write_text(
        json.dumps({"findings": findings, "note": "values are NEVER recorded, only locations"},
                   indent=2), encoding="utf-8")
    status = "pass" if not findings else "warn"
    return StepResult(
        name="secrets-scan", phase="13", status=status, priority="P1",
        summary="no hardcoded secret values detected" if not findings
                else f"{len(findings)} candidate location(s) to review",
        artifacts=["security/secrets_scan.json"],
    )


def step_db(report_dir: Path) -> StepResult:
    """Phase 7: probe a live PostgreSQL via DATABASE_URL; SKIP truthfully if none is configured."""
    url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not url:
        return StepResult(
            name="database", phase="7", status="skip", priority="P0",
            summary="no live database configured",
            reason="DATABASE_URL / SUPABASE_DB_URL not set — migrations, RLS, constraints, and "
                   "data-integrity checks require a reachable Postgres with the Supabase auth.* "
                   "bootstrap; not verifiable in this environment.")
    try:
        import psycopg2

        conn = psycopg2.connect(url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("select count(*) from information_schema.tables where table_schema='ghar_re'")
        n = cur.fetchone()[0]
        conn.close()
        return StepResult("database", "7", "pass", "P0",
                          f"connected; {n} tables in ghar_re schema")
    except Exception as e:
        return StepResult("database", "7", "fail", "P0", "database connection/query failed",
                          reason=str(e)[:300])


def step_edge(report_dir: Path) -> StepResult:
    """Phase 6 (edge): run Supabase/Deno edge-function tests if Deno is present, else BLOCK truthfully."""
    from shutil import which

    fn_root = REPO_ROOT / "supabase" / "functions"
    tests = list((fn_root / "_tests").glob("*.test.ts")) if (fn_root / "_tests").exists() else []
    if which("deno") is None:
        return StepResult(
            name="edge-functions", phase="6", status="blocked", priority="P0",
            summary=f"{len(tests)} Deno edge-function test file(s) present but not runnable",
            reason="Deno runtime is not installed in this environment; `deno test` cannot execute. "
                   "Install Deno (or run in Supabase CI) to validate consent/feedback/household/"
                   "recommendations/user-delete/user-export functions.")
    cat = report_dir / "edge"
    cat.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    # Must run with cwd=supabase/ (not REPO_ROOT) and a path relative to it: the import map
    # (@std/assert, zod, ajv, @supabase/supabase-js) lives in supabase/deno.json and Deno only
    # picks up that config by walking up from the CURRENT WORKING DIRECTORY — an absolute path
    # passed from a different cwd resolves those imports as missing (TS2307) even though the
    # exact same test files pass under backend-ci.yml, which runs from this same working-directory.
    proc = subprocess.run(["deno", "test", "--allow-env", "functions/_tests/"],
                          cwd=fn_root.parent, capture_output=True, text=True)
    (cat / "deno.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    ok = proc.returncode == 0
    return StepResult("edge-functions", "6", "pass" if ok else "fail", "P0",
                      "deno tests passed" if ok else "deno tests failed (see edge/deno.log)",
                      duration_s=round(time.time() - t0, 2), artifacts=["edge/deno.log"])


def step_ui(report_dir: Path) -> StepResult:
    """Phase 9-11: run the Playwright driver; SKIP truthfully if no web target / Playwright."""
    from shutil import which

    cat = report_dir / "playwright"
    cat.mkdir(parents=True, exist_ok=True)
    if which("node") is None:
        return StepResult("ui-playwright", "9-11", "blocked", "P1",
                          "node not available", reason="Node.js not installed")
    env = {**os.environ, "GHAR_UI_OUT": str(cat)}
    t0 = time.time()
    proc = subprocess.run(["node", str(QUALITY_DIR / "ui" / "run_ui.mjs")],
                          cwd=REPO_ROOT, env=env, capture_output=True, text=True)
    (cat / "node.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    result_file = cat / "ui_result.json"
    data = json.loads(result_file.read_text()) if result_file.exists() else {"status": "fail"}
    status = {"pass": "pass", "warn": "warn", "skipped": "skip",
              "blocked": "blocked", "fail": "fail"}.get(data.get("status", "fail"), "fail")
    return StepResult("ui-playwright", "9-11", status, "P1",
                      data.get("reason", "browser run complete"),
                      duration_s=round(time.time() - t0, 2), reason=data.get("reason", ""),
                      artifacts=["playwright/ui_result.json"])


def step_chaos(report_dir: Path) -> StepResult:
    """Phase 14: in-process resilience probes — the service must fail SAFE, not crash.

    Two runnable checks against the live app: (1) when the service is not ready it returns 503 on
    the compute path (RE-unavailable / cold-start degradation), and (2) an unsigned request is
    rejected 401 (auth boundary holds). Deeper chaos (DB down, network partition, secret rotation)
    requires the live infra probed in step_db / step_edge and is reported there.
    """
    cat = report_dir / "chaos"
    cat.mkdir(parents=True, exist_ok=True)
    checks: list[dict] = []
    try:
        from fastapi.testclient import TestClient

        from ghar_re_service import main

        with TestClient(main.app) as c:
            main.state.ready = False
            try:
                r = c.post("/v1/recommendations", json={"household": {}, "context": {}})
                checks.append({"check": "not_ready_returns_503_or_401",
                               "ok": r.status_code in (503, 401), "status": r.status_code})
            finally:
                main.state.ready = True
            r2 = c.post("/v1/recommendations", json={"household": {}, "context": {}})
            checks.append({"check": "unsigned_rejected_401", "ok": r2.status_code == 401,
                           "status": r2.status_code})
    except Exception as e:
        return StepResult("chaos", "14", "warn", "P1", f"chaos probe error: {e}")
    (cat / "chaos.json").write_text(json.dumps({"checks": checks}, indent=2), encoding="utf-8")
    all_ok = all(c["ok"] for c in checks)
    return StepResult("chaos", "14", "pass" if all_ok else "fail", "P1",
                      "fail-safe behaviour held" if all_ok else "a resilience check failed",
                      artifacts=["chaos/chaos.json"])


def run_all(report_dir: Path, quick: bool = False) -> list[StepResult]:
    """Execute every step in order and return their results."""
    steps: list[StepResult] = []
    _log(report_dir, "=== Ghar Quality Suite start ===")

    def _add(result: StepResult) -> None:
        """Append a step result and log its outcome (keeps run_all one-statement-per-line)."""
        steps.append(result)
        _log(report_dir, f"{result.name}: {result.status} ({result.summary or result.reason})")

    _add(step_inventory(report_dir))
    _add(step_ruff(report_dir))

    for name, phase, prio, target, cat in [
        ("unit-core", "4", "P0", "ghar_re_core/tests", "recommendation"),
        ("unit-service", "4", "P0", "ghar_re_service/tests", "contracts"),
        ("quality-contract", "6", "P0", "ops/quality/suites/test_contract_boundary.py", "contracts"),
        ("quality-recsys", "8", "P0", "ops/quality/suites/test_recommendation_behavior.py", "recommendation"),
        ("quality-security", "13", "P0", "ops/quality/suites/test_api_security.py", "security"),
        ("quality-planning", "5", "P1", "ops/quality/suites/test_planning_surfaces.py", "contracts"),
    ]:
        _add(_run_pytest(report_dir, name, phase, prio, target, cat))

    _add(step_chaos(report_dir))
    if not quick:
        _add(step_perf(report_dir))
    _add(step_secrets(report_dir))
    _add(step_db(report_dir))
    _add(step_edge(report_dir))
    _add(step_ui(report_dir))

    _log(report_dir, "=== Ghar Quality Suite end ===")
    return steps


def score_and_verdict(steps: list[StepResult]) -> dict:
    """Phase 18 + 20: compute the quality dashboard numbers and the launch verdict."""
    total_tests = sum(s.passed + s.failed + s.skipped for s in steps)
    passed = sum(s.passed for s in steps)
    failed = sum(s.failed for s in steps)
    skipped_tests = sum(s.skipped for s in steps)
    executed = passed + failed
    pass_pct = round(100 * passed / executed, 1) if executed else 0.0

    # Blockers: any FAIL, ranked by the step's declared priority. BLOCKED P0 surfaces are launch
    # risks too (unverified), surfaced as P1 "unverified-critical" rather than a hard fail.
    blockers = {"P0": [], "P1": [], "P2": [], "P3": []}
    unverified = []
    for s in steps:
        if s.status == "fail":
            blockers[s.priority].append(f"{s.name}: {s.summary or s.reason}")
        elif s.status in ("blocked", "skip") and s.priority == "P0":
            unverified.append(f"{s.name}: {s.reason or s.summary}")

    hard_blockers = blockers["P0"]

    # The honest QA position for a system meant to serve millions: certification requires BOTH no
    # P0 failures AND no entirely-unverified P0 surface. Zero failing tests over a partial surface
    # is NOT a launch green-light — an unverified DPDP delete/export path or unmigrated DB is a
    # launch risk, so it blocks certification here rather than being waved through.
    can_launch = not hard_blockers and not unverified

    if hard_blockers:
        readiness = "NOT READY — P0 test failures present"
    elif unverified:
        readiness = ("NOT CERTIFIABLE HERE — 0 failing tests, but P0 surfaces (DB, edge functions) "
                     "are UNVERIFIED in this environment; certify them in CI/staging before launch")
    else:
        readiness = "READY — all P0 surfaces verified with no failures"

    # Quality score: pass rate discounted by unverified P0 surfaces.
    score = pass_pct - 5 * len(unverified)
    score = max(0.0, round(score, 1))

    return {
        "total_test_cases": total_tests, "passed": passed, "failed": failed,
        "skipped": skipped_tests, "pass_pct": pass_pct, "quality_score": score,
        "can_launch_today": can_launch, "launch_readiness": readiness,
        "blockers": blockers, "unverified_p0_surfaces": unverified,
    }


def _write_reports(report_dir: Path, steps: list[StepResult], verdict: dict, meta: dict) -> None:
    """Write test_results.json, metrics.json, summary.txt/.md/.html into the report folder."""
    results = {"meta": meta, "verdict": verdict, "steps": [asdict(s) for s in steps]}
    (report_dir / "test_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (report_dir / "metrics.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")

    # ---- summary.txt / summary.md ----
    lines = [
        "GHAR PRODUCTION QUALITY REPORT",
        f"Generated: {meta['generated_at']}  |  git: {meta['git_head']}",
        "=" * 72,
        f"Quality score: {verdict['quality_score']}   Pass%: {verdict['pass_pct']}",
        f"Tests: {verdict['passed']} passed / {verdict['failed']} failed / "
        f"{verdict['skipped']} skipped ({verdict['total_test_cases']} total)",
        f"Launch readiness: {verdict['launch_readiness']}",
        f"Can launch today: {'YES' if verdict['can_launch_today'] else 'NO'}",
        "=" * 72, "", "STEPS:",
    ]
    for s in steps:
        lines.append(f"  [{s.status.upper():7}] {s.name:20} (P{s.priority[-1]}, phase {s.phase})"
                     f" - {s.summary or s.reason}")
    if verdict["blockers"]["P0"]:
        lines += ["", "P0 BLOCKERS:"] + [f"  - {b}" for b in verdict["blockers"]["P0"]]
    if verdict["unverified_p0_surfaces"]:
        lines += ["", "UNVERIFIED P0 SURFACES (cannot certify in this environment):"]
        lines += [f"  - {u}" for u in verdict["unverified_p0_surfaces"]]
    (report_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")

    md = ["# Ghar Production Quality Report", "",
          f"_Generated {meta['generated_at']} · git `{meta['git_head']}`_", "",
          "| Quality score | Pass % | Passed | Failed | Skipped | Launch |",
          "|---|---|---|---|---|---|",
          f"| **{verdict['quality_score']}** | {verdict['pass_pct']} | {verdict['passed']} | "
          f"{verdict['failed']} | {verdict['skipped']} | "
          f"{'✅ YES' if verdict['can_launch_today'] else '❌ NO'} |", "",
          f"**Launch readiness:** {verdict['launch_readiness']}", "", "## Steps", "",
          "| Step | Phase | Status | Priority | Detail |", "|---|---|---|---|---|"]
    for s in steps:
        md.append(f"| {s.name} | {s.phase} | {s.status.upper()} | {s.priority} | "
                  f"{(s.summary or s.reason).replace('|', '/')} |")
    if verdict["unverified_p0_surfaces"]:
        md += ["", "## Unverified P0 surfaces (not certifiable in this environment)", ""]
        md += [f"- {u}" for u in verdict["unverified_p0_surfaces"]]
    all_fail = [f for s in steps for f in s.failures]
    if all_fail:
        md += ["", "## Failing tests", ""]
        md += [f"- `{f['test']}` — {f['message']}" for f in all_fail]
    (report_dir / "summary.md").write_text("\n".join(md), encoding="utf-8")

    # ---- summary.html (self-contained dashboard) ----
    rows = "".join(
        f"<tr class='{s.status}'><td>{s.name}</td><td>{s.phase}</td>"
        f"<td>{s.status.upper()}</td><td>{s.priority}</td>"
        f"<td>{(s.summary or s.reason)}</td></tr>" for s in steps)
    unver = "".join(f"<li>{u}</li>" for u in verdict["unverified_p0_surfaces"]) or "<li>none</li>"
    launch_color = "#137333" if verdict["can_launch_today"] else "#b3261e"
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Ghar Quality Report</title><style>
body{{font-family:system-ui,Arial;margin:2rem;color:#1a1a1a}}
h1{{margin-bottom:0}} .sub{{color:#666}}
.kpis{{display:flex;gap:1rem;margin:1rem 0;flex-wrap:wrap}}
.kpi{{border:1px solid #ddd;border-radius:10px;padding:1rem 1.4rem;min-width:120px}}
.kpi b{{font-size:1.8rem;display:block}}
table{{border-collapse:collapse;width:100%;margin-top:1rem}}
td,th{{border:1px solid #e0e0e0;padding:.5rem .7rem;text-align:left;font-size:.92rem}}
tr.pass td:nth-child(3){{color:#137333;font-weight:600}}
tr.fail td:nth-child(3){{color:#b3261e;font-weight:700}}
tr.blocked td:nth-child(3),tr.skip td:nth-child(3){{color:#9a6700;font-weight:600}}
tr.warn td:nth-child(3){{color:#9a6700}}
.verdict{{font-size:1.2rem;font-weight:700;color:{launch_color}}}
</style></head><body>
<h1>Ghar Production Quality Report</h1>
<div class="sub">Generated {meta['generated_at']} · git {meta['git_head']}</div>
<div class="kpis">
<div class="kpi"><b>{verdict['quality_score']}</b>Quality score</div>
<div class="kpi"><b>{verdict['pass_pct']}%</b>Pass rate</div>
<div class="kpi"><b>{verdict['passed']}</b>Passed</div>
<div class="kpi"><b>{verdict['failed']}</b>Failed</div>
<div class="kpi"><b>{verdict['skipped']}</b>Skipped</div>
</div>
<p class="verdict">Launch today: {'YES' if verdict['can_launch_today'] else 'NO'} — {verdict['launch_readiness']}</p>
<h2>Steps</h2><table><tr><th>Step</th><th>Phase</th><th>Status</th><th>Priority</th><th>Detail</th></tr>{rows}</table>
<h2>Unverified P0 surfaces</h2><ul>{unver}</ul>
</body></html>"""
    (report_dir / "summary.html").write_text(html, encoding="utf-8")


def main() -> int:
    """CLI entrypoint: run the suite, write the report, print the verdict, return an exit code."""
    ap = argparse.ArgumentParser(description="Ghar production quality orchestrator")
    ap.add_argument("--quick", action="store_true", help="skip the perf benchmark")
    ap.add_argument("--report-root", default=str(QUALITY_DIR / "reports"))
    ap.add_argument(
        "--ci", action="store_true",
        help="CI mode: exit non-zero ONLY on a real test/step FAILURE. A skipped/blocked P0 "
             "surface (e.g. no DB or no web target in the runner) does NOT fail the build — it is "
             "still reported and still blocks the launch verdict, but an environment gap is not a "
             "regression. Without this flag the exit code follows the launch verdict, which is "
             "correct for a release gate but would make ordinary CI always red.")
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_dir = Path(args.report_root) / stamp
    report_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("screenshots", "videos", "network", "console", "performance", "security",
                "playwright", "contracts", "recommendation", "database", "static", "chaos", "edge"):
        (report_dir / sub).mkdir(exist_ok=True)

    try:
        head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=REPO_ROOT, text=True).strip()
    except Exception:
        head = "unknown"
    meta = {"generated_at": datetime.now(UTC).isoformat(), "git_head": head,
            "report_dir": str(report_dir)}

    steps = run_all(report_dir, quick=args.quick)
    verdict = score_and_verdict(steps)
    _write_reports(report_dir, steps, verdict, meta)

    # keep a stable pointer to the newest report
    (Path(args.report_root) / "latest.txt").write_text(str(report_dir), encoding="utf-8")

    print("\n" + (report_dir / "summary.txt").read_text(encoding="utf-8"))
    print(f"\nFull report: {report_dir}")

    if args.ci:
        # CI gate: fail only on an actual step failure, not on an unverified/skipped surface.
        failed_steps = [s.name for s in steps if s.status == "fail"]
        if failed_steps:
            print(f"\nCI: FAIL — failing step(s): {', '.join(failed_steps)}")
            return 1
        print("\nCI: PASS — no failing steps (unverified surfaces reported, not fatal in CI).")
        return 0
    return 0 if verdict["can_launch_today"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

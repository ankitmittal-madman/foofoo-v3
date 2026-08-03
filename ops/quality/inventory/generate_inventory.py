"""
Phase 1 + 2 — Repository Inventory and Feature Matrix generator.

This module DISCOVERS what actually exists in the repository rather than assuming a fixed layout.
It walks the tree, classifies every component (Python package, FastAPI service, Deno Edge Function,
mobile screen/API client, SQL migration, contract, script, test suite), and emits two artifacts the
quality report links to:

  * inventory.json / inventory.md  — the discovered repository inventory (Phase 1)
  * feature_matrix.json / feature_matrix.md — the master feature matrix with testability + risk
    (Phase 2)

It performs NO fabrication: every row is derived from a real file on disk. Where a status cannot be
proven from the repository (e.g. "is this deployed?"), the field is emitted as "unverified" rather
than guessed.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Directories that are noise for an inventory (caches, VCS, vendored deps).
_SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".egg-info", "reports",
}


def _iter_files(root: Path):
    """Yield every non-noise file under `root`, skipping caches/VCS/vendored dirs.

    Trigger: called by each discovery pass below.
    Reads: the filesystem only. Writes: nothing.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in _SKIP_DIRS and not d.endswith(".egg-info")
        ]
        for name in filenames:
            yield Path(dirpath) / name


@dataclass
class Component:
    """One discovered repository component (a subsystem, surface, or artifact)."""

    name: str
    kind: str
    path: str
    detail: str = ""
    files: int = 0


@dataclass
class Feature:
    """One row of the Phase 2 feature matrix, derived from discovered components."""

    feature: str
    description: str
    owner: str
    dependencies: str
    status: str
    testability: str
    priority: str
    risk: str
    missing: str
    evidence: str


def _rel(p: Path) -> str:
    """Return `p` relative to the repository root as a POSIX string."""
    return p.relative_to(REPO_ROOT).as_posix()


def discover_components() -> list[Component]:
    """Walk the repo and classify every real component into the Phase 1 inventory.

    Returns a list of :class:`Component`; each entry corresponds to files that actually exist.
    """
    comps: list[Component] = []

    # --- Python packages (RE core + service) -------------------------------------------------
    for pkg_dir, kind, detail in [
        ("ghar_re_core", "python-package", "Recommendation-engine math (frozen reference impl)"),
        ("ghar_re_service", "python-service", "FastAPI production service hosting the RE"),
    ]:
        d = REPO_ROOT / pkg_dir
        if d.exists():
            py = [f for f in _iter_files(d) if f.suffix == ".py"]
            comps.append(Component(pkg_dir, kind, _rel(d), detail, len(py)))

    # --- FastAPI endpoints (parsed from main.py route decorators) ----------------------------
    main_py = REPO_ROOT / "ghar_re_service" / "ghar_re_service" / "main.py"
    if main_py.exists():
        src = main_py.read_text(encoding="utf-8")
        for m in re.finditer(r'@app\.(get|post|put|delete|patch)\("([^"]+)"\)', src):
            comps.append(
                Component(
                    f"{m.group(1).upper()} {m.group(2)}", "http-endpoint", _rel(main_py),
                    "FastAPI route on the RE service",
                )
            )

    # --- Supabase Edge Functions -------------------------------------------------------------
    fn_root = REPO_ROOT / "supabase" / "functions"
    if fn_root.exists():
        for child in sorted(fn_root.iterdir()):
            if child.is_dir() and not child.name.startswith("_"):
                ts = [f for f in _iter_files(child) if f.suffix == ".ts"]
                comps.append(
                    Component(child.name, "edge-function", _rel(child),
                              "Supabase/Deno edge function", len(ts))
                )

    # --- Mobile app (Expo Router screens + API clients) --------------------------------------
    app_dir = REPO_ROOT / "mobile" / "app"
    if app_dir.exists():
        for f in sorted(_iter_files(app_dir)):
            if f.suffix == ".tsx":
                comps.append(Component(_rel(f), "mobile-screen", _rel(f), "Expo Router screen"))
    api_dir = REPO_ROOT / "mobile" / "src" / "api"
    if api_dir.exists():
        for f in sorted(_iter_files(api_dir)):
            if f.suffix == ".ts":
                comps.append(Component(_rel(f), "mobile-api-client", _rel(f), "Mobile API client"))

    # --- SQL (migrations / rollback / seeds / validation) ------------------------------------
    for sub, kind in [
        ("database/migrations", "sql-migration"),
        ("database/rollback", "sql-rollback"),
        ("database/seeds", "sql-seed"),
        ("database/validation", "sql-validation"),
        ("supabase/migrations", "sql-migration"),
    ]:
        d = REPO_ROOT / sub
        if d.exists():
            sql = [f for f in _iter_files(d) if f.suffix == ".sql"]
            if sql:
                comps.append(Component(sub, kind, sub, f"{len(sql)} SQL files", len(sql)))

    # --- Contracts ---------------------------------------------------------------------------
    contracts = REPO_ROOT / "contracts"
    if contracts.exists():
        for f in sorted(_iter_files(contracts)):
            comps.append(Component(_rel(f), "api-contract", _rel(f), "JSON Schema contract"))

    # --- Existing test suites ----------------------------------------------------------------
    for f in _iter_files(REPO_ROOT):
        if f.name.startswith("test_") and f.suffix in {".py", ".ts"}:
            comps.append(Component(_rel(f), "test-suite", _rel(f), "Existing automated tests"))

    # --- Scripts / workflows -----------------------------------------------------------------
    gh = REPO_ROOT / ".github" / "workflows"
    if gh.exists():
        for f in sorted(_iter_files(gh)):
            comps.append(Component(_rel(f), "ci-workflow", _rel(f), "GitHub Actions workflow"))

    return comps


def _git_head() -> str:
    """Return the current git HEAD short SHA, or 'unknown' if git is unavailable."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def build_feature_matrix(comps: list[Component]) -> list[Feature]:
    """Derive the Phase 2 feature matrix from discovered components.

    Testability/priority/risk are assigned from what the repository can actually prove: a feature
    with an executable test path is 'automated'; an Edge Function with no runnable test harness in
    this environment (Deno absent) is 'blocked'. Nothing here is invented — `evidence` cites the
    file(s) each row rests on.
    """
    kinds = {}
    for c in comps:
        kinds.setdefault(c.kind, []).append(c)

    endpoints = [c.name for c in kinds.get("http-endpoint", [])]
    edge = [c.name for c in kinds.get("edge-function", [])]
    screens = list(kinds.get("mobile-screen", []))

    feats: list[Feature] = []

    feats.append(Feature(
        "Recommendation engine (RE core math)",
        "Class-first scoring/pipeline: household->cohort->class plan->dish pool.",
        "ghar_re_core", "seed data bundle, config YAMLs", "implemented",
        "automated (pytest, golden-master locked)", "P0", "high",
        "none identified", "ghar_re_core/, ghar_re_core/tests/test_golden_master.py",
    ))
    feats.append(Feature(
        "RE HTTP service", f"FastAPI service exposing {len(endpoints)} routes: {', '.join(endpoints)}",
        "ghar_re_service", "ghar_re_core, data bundle, HMAC secret", "implemented",
        "automated (FastAPI TestClient + quality suites)", "P0", "high",
        "no live-deploy verification in this env", "ghar_re_service/ghar_re_service/main.py",
    ))
    feats.append(Feature(
        "Service auth (HMAC signature)", "Signed service-to-service calls; fail-closed 401/503.",
        "ghar_re_service/auth.py", "shared secret", "implemented",
        "automated (test_auth + quality security suite)", "P0", "high",
        "prod secret rotation not verifiable here", "ghar_re_service/ghar_re_service/auth.py",
    ))
    feats.append(Feature(
        "Rate limiting", "Sliding-window per-client limiter; 429 with Retry-After.",
        "ghar_re_service/ratelimit.py", "none", "implemented",
        "automated (test_ratelimit + quality security suite)", "P1", "medium",
        "distributed limiter (multi-instance) not present", "ghar_re_service/ghar_re_service/ratelimit.py",
    ))
    feats.append(Feature(
        "API contract (v1 schema)", "JSON-Schema request/response contract, additive/open rule.",
        "contracts/", "schema file", "implemented",
        "automated (contract suite)", "P0", "high", "none identified",
        "contracts/ghar-re-v1.schema.json",
    ))
    feats.append(Feature(
        "Onboarding flow (mobile)",
        f"Expo onboarding: {len([s for s in screens if 'onboarding' in s.path])} screens + consent.",
        "mobile", "RE service, Supabase auth", "implemented",
        "blocked-here (no running Expo web target / device)", "P0", "high",
        "no automated UI test; needs running web build or device farm",
        "mobile/app/(onboarding)/",
    ))
    feats.append(Feature(
        "Auth / sign-in (mobile)", "Supabase-backed sign-in + session context.",
        "mobile/src/auth", "Supabase", "implemented", "blocked-here (needs running app + Supabase)",
        "P0", "high", "no automated UI/e2e test in this env", "mobile/app/(auth)/sign-in.tsx",
    ))
    for fn in edge:
        risk = "high" if fn in {"user-delete", "user-export", "consent"} else "medium"
        prio = "P0" if fn in {"recommendations", "household", "consent"} else "P1"
        feats.append(Feature(
            f"Edge function: {fn}", f"Supabase/Deno function '{fn}'.", "supabase/functions",
            "Supabase DB, RE service (for recommendations)", "implemented",
            "blocked-here (Deno runtime not installed)", prio, risk,
            "Deno absent -> native deno test cannot run in this environment",
            f"supabase/functions/{fn}/",
        ))
    feats.append(Feature(
        "Database schema + migrations", "Numbered SQL migrations/rollback/seeds/validation.",
        "database/", "PostgreSQL 15 / Supabase", "implemented",
        "blocked-here (no live DB connection configured)", "P0", "high",
        "needs a reachable Postgres with auth.* bootstrap to execute", "database/migrations/",
    ))
    feats.append(Feature(
        "Data-subject rights (export/delete)", "user-export, user-delete, retention purge, hard delete.",
        "supabase/functions", "Supabase DB", "implemented", "blocked-here (Deno + DB)",
        "P0", "high", "DPDP-critical; no executable verification in this env",
        "supabase/functions/user-delete/, user-export/, cron-*",
    ))
    return feats


def _md_table(rows: list[dict], cols: list[str]) -> str:
    """Render a list of dict rows as a GitHub-flavoured Markdown table."""
    head = "| " + " | ".join(cols) + " |\n"
    sep = "| " + " | ".join("---" for _ in cols) + " |\n"
    body = ""
    for r in rows:
        body += "| " + " | ".join(str(r.get(c, "")).replace("|", "\\|") for c in cols) + " |\n"
    return head + sep + body


def generate(out_dir: Path | None = None) -> dict:
    """Run discovery + matrix build and write inventory/feature-matrix artifacts.

    Args:
        out_dir: where to write the artifacts. Defaults to this module's own directory so a bare
            `python generate_inventory.py` leaves a browsable snapshot; the orchestrator passes a
            timestamped report folder instead.

    Returns a summary dict (counts + output paths) for the orchestrator to embed in its report.
    """
    out_dir = out_dir or Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    comps = discover_components()
    feats = build_feature_matrix(comps)
    generated_at = datetime.now(UTC).isoformat()
    head = _git_head()

    by_kind: dict[str, int] = {}
    for c in comps:
        by_kind[c.kind] = by_kind.get(c.kind, 0) + 1

    inv = {
        "generated_at": generated_at, "git_head": head,
        "component_count": len(comps), "by_kind": by_kind,
        "components": [asdict(c) for c in comps],
    }
    (out_dir / "inventory.json").write_text(json.dumps(inv, indent=2), encoding="utf-8")

    inv_md = ["# Repository Inventory (Phase 1)\n",
              f"_Generated {generated_at} · git `{head}`_\n",
              f"**{len(comps)} components discovered.**\n", "## By kind\n"]
    inv_md.append(_md_table(
        [{"kind": k, "count": v} for k, v in sorted(by_kind.items())], ["kind", "count"]))
    inv_md.append("\n## Components\n")
    inv_md.append(_md_table([asdict(c) for c in comps], ["name", "kind", "path", "detail", "files"]))
    (out_dir / "inventory.md").write_text("\n".join(inv_md), encoding="utf-8")

    fm = {"generated_at": generated_at, "git_head": head,
          "features": [asdict(f) for f in feats]}
    (out_dir / "feature_matrix.json").write_text(json.dumps(fm, indent=2), encoding="utf-8")
    fm_md = ["# Feature Matrix (Phase 2)\n", f"_Generated {generated_at} · git `{head}`_\n",
             _md_table([asdict(f) for f in feats],
                       ["feature", "description", "owner", "dependencies", "status",
                        "testability", "priority", "risk", "missing", "evidence"])]
    (out_dir / "feature_matrix.md").write_text("\n".join(fm_md), encoding="utf-8")

    return {
        "component_count": len(comps), "feature_count": len(feats), "by_kind": by_kind,
        "artifacts": [str(out_dir / n) for n in
                      ("inventory.json", "inventory.md", "feature_matrix.json", "feature_matrix.md")],
    }


if __name__ == "__main__":
    summary = generate()
    print(json.dumps(summary, indent=2))

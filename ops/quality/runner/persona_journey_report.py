"""
WP-22 — persona_journey_report.py. Turns run_persona_journeys.mjs's per-persona output
(GHAR_UI_OUT/personas/<key>/{summary.json, recommendations.json, *.png}) into one HTML page per
persona (screenshots in order, with each step's caption) plus an index.html grouping personas by
outcome (200 / 422 / warned / driver-error), matching this quality program's existing report
style (ops/quality/runner/report_reader.py's plain-HTML/no-build-step convention — no bundler, no
external assets, just files a browser can open directly).

Usage:
    python3 ops/quality/runner/persona_journey_report.py <GHAR_UI_OUT-dir>

Writes <dir>/report/index.html and <dir>/report/<persona-key>.html. Purely a reader/renderer of
whatever run_persona_journeys.mjs already wrote — if that directory doesn't exist (because the
driver was skipped for lack of GHAR_WEB_URL), this script says so explicitly and exits nonzero
rather than fabricating a report from nothing.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


def _load_persona(persona_dir: Path) -> dict | None:
    """Read one persona's summary.json + recommendations.json, or None if summary.json is missing."""
    summary_path = persona_dir / "summary.json"
    if not summary_path.exists():
        return None
    summary = json.loads(summary_path.read_text())
    recs_path = persona_dir / "recommendations.json"
    recommendations = json.loads(recs_path.read_text()) if recs_path.exists() else None
    return {"dir": persona_dir, "summary": summary, "recommendations": recommendations}


def _outcome_bucket(entry: dict) -> str:
    """Classify a persona's run into the index page's grouping: 200 / 422 / warned / error."""
    summary = entry["summary"]
    if not summary.get("ok"):
        return "driver-error"
    status = summary.get("recommendations_status")
    body = (entry.get("recommendations") or {}).get("body") or {}
    if status == 200 and isinstance(body, dict) and body.get("warnings"):
        return "warned"
    if status == 200:
        return "200"
    if status == 422:
        return "422"
    return "other"


def _persona_page(entry: dict) -> str:
    """Render one persona's HTML report: its steps in order (screenshot + caption) plus the raw
    recommendations capture, so a reviewer can see exactly what the UI showed and what the API
    returned for this persona without re-running anything."""
    summary = entry["summary"]
    key = html.escape(str(summary.get("key", "")))
    label = html.escape(str(summary.get("label", "")))
    ok = summary.get("ok")
    error = summary.get("error")
    steps_html = []
    for step in summary.get("steps", []):
        shot = step.get("screenshot")
        caption = html.escape(str(step.get("label", "")))
        img_tag = f'<img src="../personas/{key}/{html.escape(shot)}" alt="{caption}">' if shot else "<em>no screenshot</em>"
        steps_html.append(f'<figure><figcaption>{caption}</figcaption>{img_tag}</figure>')

    recs_json = html.escape(json.dumps(entry.get("recommendations"), indent=2))
    status_line = "OK" if ok else f"FAILED — {html.escape(str(error))}"

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Persona journey — {key}</title>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 24px; background: #0b0c10; color: #e8e8e8; }}
h1 {{ font-size: 20px; }} h2 {{ font-size: 15px; color: #9aa; margin-top: 28px; }}
.meta {{ color: #9aa; margin-bottom: 16px; }}
figure {{ margin: 0 0 24px 0; border: 1px solid #333; border-radius: 8px; padding: 10px; background: #14161a; }}
figcaption {{ font-size: 13px; color: #9ab; margin-bottom: 8px; font-weight: 600; }}
img {{ max-width: 900px; width: 100%; border-radius: 4px; border: 1px solid #222; }}
pre {{ background: #14161a; border: 1px solid #333; border-radius: 8px; padding: 12px; overflow: auto; font-size: 12px; }}
a {{ color: #7cf; }}
.status-ok {{ color: #6d6; }} .status-fail {{ color: #e66; }}
</style></head>
<body>
<p><a href="index.html">&larr; back to index</a></p>
<h1>{label} <span class="meta">({key})</span></h1>
<p class="{'status-ok' if ok else 'status-fail'}">{status_line}</p>
<h2>Steps</h2>
{''.join(steps_html) or '<p><em>no steps recorded</em></p>'}
<h2>Recommendations capture</h2>
<pre>{recs_json}</pre>
</body></html>"""


def _index_page(entries: list[dict]) -> str:
    """Render index.html: personas grouped by outcome bucket, each linking to its own report page."""
    buckets: dict[str, list[dict]] = {"200": [], "422": [], "warned": [], "driver-error": [], "other": []}
    for entry in entries:
        buckets[_outcome_bucket(entry)].append(entry)

    titles = {
        "200": "200 — accepted",
        "422": "422 — contract-rejected",
        "warned": "200 with warnings[]",
        "driver-error": "Driver/UI failure (never reached a recommendations result)",
        "other": "Other / unknown",
    }
    sections = []
    for bucket, label in titles.items():
        items = buckets[bucket]
        if not items:
            continue
        rows = "".join(
            f'<li><a href="{html.escape(e["summary"]["key"])}.html">{html.escape(e["summary"]["key"])}</a> '
            f'— {html.escape(str(e["summary"].get("label", "")))}</li>'
            for e in items
        )
        sections.append(f"<h2>{html.escape(label)} ({len(items)})</h2><ul>{rows}</ul>")

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>WP-22 Persona UI Journeys</title>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 24px; background: #0b0c10; color: #e8e8e8; }}
h1 {{ font-size: 20px; }} h2 {{ font-size: 15px; color: #9ab; margin-top: 24px; }}
ul {{ line-height: 1.6; }} a {{ color: #7cf; }}
</style></head>
<body>
<h1>WP-22 — Synthetic Persona UI Journey Reports</h1>
<p>{len(entries)} personas.</p>
{''.join(sections)}
</body></html>"""


def main() -> int:
    """CLI entry point: read <GHAR_UI_OUT>/personas/*, write <GHAR_UI_OUT>/report/*.html."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ui_out_dir", help="the GHAR_UI_OUT directory run_persona_journeys.mjs wrote into")
    args = parser.parse_args()

    ui_out = Path(args.ui_out_dir)
    personas_root = ui_out / "personas"
    if not personas_root.exists():
        print(
            f"No personas/ directory found under {ui_out} — run_persona_journeys.mjs was either "
            "skipped (no GHAR_WEB_URL) or hasn't run yet. Nothing to report; not fabricating one.",
            file=sys.stderr,
        )
        return 1

    entries = []
    for persona_dir in sorted(personas_root.iterdir()):
        if not persona_dir.is_dir():
            continue
        entry = _load_persona(persona_dir)
        if entry is not None:
            entries.append(entry)

    if not entries:
        print(f"personas/ directory under {ui_out} exists but contains no summary.json files.", file=sys.stderr)
        return 1

    report_dir = ui_out / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        key = entry["summary"]["key"]
        (report_dir / f"{key}.html").write_text(_persona_page(entry))
    (report_dir / "index.html").write_text(_index_page(entries))

    print(f"Wrote {len(entries)} persona report(s) + index.html to {report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

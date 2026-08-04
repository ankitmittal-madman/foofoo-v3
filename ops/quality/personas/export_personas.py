"""
WP-22 — export_personas.py. Dumps all_personas() (personas.py; 7 golden + 8 derived +
41 real_persona_derived + 44 adversarial = 100) to a flat JSON array so the Node/Playwright
journey driver (ops/quality/ui/run_persona_journeys.mjs) — which cannot import Python — has a
static, versioned snapshot of every persona's household/context/expectation fields to drive the
real onboarding UI against.

Usage (documented here, matching run_ui.mjs's own header-comment convention rather than having
the Node driver shell out to python3 itself):

    python3 ops/quality/personas/export_personas.py > /tmp/personas.json
    GHAR_WEB_URL=http://localhost:8081 GHAR_UI_OUT=/path/to/report \
        GHAR_PERSONAS_JSON=/tmp/personas.json \
        node ops/quality/ui/run_persona_journeys.mjs

If GHAR_PERSONAS_JSON is not set, run_persona_journeys.mjs falls back to invoking this script
itself via child_process (see that file's loadPersonas()), so the one-liner above is a documented
convenience, not a hard requirement.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ops.quality.personas.personas import all_personas  # noqa: E402


def main() -> None:
    """Write every persona's key/label/household/context/expectations to stdout as a JSON array."""
    out = []
    for p in all_personas():
        out.append({
            "key": p.key,
            "label": p.label,
            "household": p.household,
            "context": p.context,
            "expect_status": p.expect_status,
            "expect_plates": p.expect_plates,
            "forbid_diet": list(p.forbid_diet),
            "forbid_ingredients": list(p.forbid_ingredients),
            "expect_warnings": p.expect_warnings,
            "note": p.note,
        })
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

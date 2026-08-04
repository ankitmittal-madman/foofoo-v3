"""
ghar_re_core.substitution — ingredient/dish substitution graph (Core Spine SP-F14).

Was schema-only, near-empty in the old dropped `ghar_re.dish_variants` table (2 rows, golden
sample only, real 810-catalogue variant seed never built — see
docs/archive/audits/re_audit_archive/ARCHIVED_04_food_ontology_audit.md §2). Founder-directed
backlog closeout (2026-08-04, item 5): a real, working substitution
graph, built at the layer the live engine actually reads (a bundled CSV, same placement convention
as sig_scores_v1.csv/dish_macro_v1.csv), not a revived Postgres table the engine never queried.

Scope, deliberately conservative: 13 curated (dish_name -> dish_name, variant_type) pairs, each
verified present in the real 810-dish catalogue before being added (see data/dish_substitutions_v1.csv's
own `method` column for provenance — AI-researched from established substitution convention, not
live-cited, spot-check recommended). This is NOT a general multi-hop ingredient-level graph (SP-F14's
original ambition); it is a real, working dish-level substitution lookup, honestly scoped to what
was actually curated rather than claiming more than 13 pairs cover.
"""
import csv
import os

from ghar_re_core import config as _cfg

SUBSTITUTIONS_CSV = "dish_substitutions_v1.csv"

# list of (from_name, to_name, variant_type, note) — loaded once at import time, same pattern as
# catalogue.py's _ING dict, so it follows GHAR_RE_CONFIG_DIR into a baked bundle too.
_SUBSTITUTIONS = []
_path = os.path.join(os.path.dirname(_cfg.SRC), SUBSTITUTIONS_CSV)
with open(_path, newline="", encoding="utf-8") as _f:
    for _row in csv.DictReader(_f):
        _SUBSTITUTIONS.append(
            (_row["from_dish"], _row["to_dish"], _row["variant_type"], _row["note"])
        )


def find_substitutes(dish_name, variant_type=None):
    """All curated substitutes for `dish_name`, optionally filtered to one `variant_type`
    ('veg_swap', 'protein_swap', ...). Returns a list of (to_dish_name, variant_type, note)
    tuples — callers resolve the name against their own Catalogue (this module has no Catalogue
    dependency, so it works identically for the golden sample or the real 810-dish catalogue).
    Returns [] if no curated substitute exists for this dish — never guesses one."""
    out = []
    for frm, to, vtype, note in _SUBSTITUTIONS:
        if frm != dish_name:
            continue
        if variant_type is not None and vtype != variant_type:
            continue
        out.append((to, vtype, note))
    return out


def has_substitute(dish_name, variant_type=None):
    """True if find_substitutes(dish_name, variant_type) would return at least one match —
    convenience for callers that only need a yes/no (e.g. an onboarding UI hint)."""
    return bool(find_substitutes(dish_name, variant_type))

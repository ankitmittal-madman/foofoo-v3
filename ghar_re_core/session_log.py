"""
ghar_re.session_log — per-user recommendation trace as a Markdown file (ops/logs/session-log/).

Renders the FULL decision path for one household+context, the same walk-through used to debug
test_10/13/14 by hand: raw answers -> theta -> cohort feature vector -> sub-cohort membership ->
migration/region blend -> learned class affinity -> per-dish scoring -> eligibility funnel ->
Assemble-7 plates. Every number is live from the engine, nothing hand-authored.

Usage (dev/ops tool — the Fly service is stateless and does not write to the repo at runtime):
    from ghar_re_core.session_log import write_session_log
    write_session_log(household, ctx)                       # -> ops/logs/session-log/<label>.md
Or via the pipeline:  recommend(hh, ctx, session_log_dir="ops/logs/session-log")
"""
import os
from datetime import datetime, timezone

from ghar_re_core import cohort_intel as CI
from ghar_re_core import pairing
from ghar_re_core import scoring as S
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.config import CONFIG
from ghar_re_core.derivation import derive_theta

DEFAULT_LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ops", "logs", "session-log"
)


def _safe(label):
    """Filesystem-safe slug for a household label / id."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(label)) or "user"


def render(household, ctx, catalogue=None):
    """Return the Markdown session-log string for one (household, ctx). Runs the live pipeline."""
    cat = catalogue or Catalogue()
    th = derive_theta(household)
    obj = household.get("q15_objective") or CONFIG.default_objective
    feats = CI.theta_features(th)
    n = ctx.get("interaction_count", 0)
    L = []
    L.append(f"# Session log — {household.get('label', household.get('id_key', 'user'))}")
    L.append(f"_generated {datetime.now(timezone.utc).isoformat()} · slot={ctx.get('slot')} "
             f"weekday={ctx.get('weekday')} · engine {CONFIG.versions['spine']}_\n")

    L.append("## 1. Onboarding inputs (raw)")
    for k in ("q1_household_type", "q3_home_state", "q4_current_city", "q5_diet", "q13_who_cooks",
              "q14_eat_out_per_week", "q15_objective", "q11_conditions"):
        if k in household:
            L.append(f"- `{k}` = {household[k]}")
    L.append("")

    L.append("## 2. θ — derived household profile")
    for k in ("home_state", "region", "city_tier", "is_migrant", "local_state", "blend", "diet",
              "spice_ceiling", "lifecycle_stage", "time_pressure", "time_route", "objective"):
        rec = th.get(k)
        if rec is not None:
            L.append(f"- **{k}** = {rec['value']}")
    L.append(f"- **objective** = {obj}\n")

    L.append("## 3. Cohort feature vector (what the model keys on)")
    L.append("```")
    for k, v in feats.items():
        L.append(f"{k:18s}= {v}")
    L.append("```\n")

    L.append("## 4. Resolved persona + sub-cohort membership")
    from ghar_re_core import cohort_plan as CP
    L.append("**Compositional persona resolution (WP-17 — the plan core):**")
    for p, frac in CP.resolve_persona(th, k=3):
        L.append(f"- **{p['persona_id']}** · {p.get('sub_cohort_label')} · match {frac}")
    L.append("\n_nearest anchors (learned-model explainability):_")
    for m in CI.cohort_membership(th, k=3):
        L.append(f"- {m['persona_id']} · {m['label']} · match {m['match']}")
    L.append("")

    L.append("## 5. Migration / region blend")
    grp = CI.destination_group(th)
    row = CI._migration().get((th["home_state"]["value"], grp))
    L.append(f"- destination_group = **{grp}** · migrant = {th['is_migrant']['value']}")
    if row:
        L.append(f"- weights → home {row['home_state_signature_weight']} / "
                 f"city {row['current_city_lifestyle_weight']} / national {row['national_modern_weight']}"
                 + ("  _(overlay applied — migrant)_" if th["is_migrant"]["value"]
                    else "  _(overlay NOT applied — home-state resident)_"))
    L.append("")

    daytype = "weekend" if ctx.get("weekday") in ("Saturday", "Sunday") else "weekday"
    L.append(f"## 6. Class plan — compositional + learned ({ctx.get('slot')}/{daytype})")
    comp = CP.class_plan(th, ctx)
    L.append("**Compositional plan (WP-17: persona core ∩ state pool + migration, spine-filtered):**")
    for c, v in sorted(comp.items(), key=lambda x: -x[1])[:8]:
        if v > 0.02:
            L.append(f"- {v:.2f}  `{c}`")
    w_comp, w_learn = CONFIG.class_plan_weights
    L.append(f"\n**Fused affinity (compositional×{w_comp} + learned×{w_learn}, what scoring uses):**")
    aff = CI.class_affinity(th, ctx)
    for c, v in sorted(aff.items(), key=lambda x: -x[1])[:8]:
        if v > 0.02:
            L.append(f"- {v:.2f}  `{c}`")
    L.append(f"\n- cohort weight w_cohort(n={n}) = **{CONFIG.w_cohort_effective(n):.2f}** · "
             f"foreign_demote(n={n}) = **{CONFIG.foreign_demote_effective(n):.2f}**\n")

    L.append("## 7. Eligibility funnel")
    L.append("```")
    for f in S.eligibility_funnel(cat, th, ctx, shared_hero=False):
        L.append(f"{f['stage']:24s}: {f['count']}")
    L.append("```\n")

    L.append("## 8. Final plates (Assemble-7)")
    plates = pairing.assemble_7(cat, th, ctx, obj, n=7)
    for i, p in enumerate(plates, 1):
        L.append(f"{i}. **[{p['score']:.2f}]** {pairing.plate_label(p)}")
    L.append("")

    L.append("## 9. Per-dish scoring (dishes in the served plates)")
    L.append("| dish | zone | m_palette | sig | BASE | GAIN | s_cohort | s_foreign | score |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    seen = set()
    for p in plates[:5]:
        for name in p.get("heroes", []):
            if name in seen:
                continue
            seen.add(name)
            d = cat.get(name)
            if not d:
                continue
            L.append(f"| {name} | {d.zone} | {S.m_palette(d, th):.2f} | {d.sig_score:.2f} | "
                     f"{S.base(d, th, ctx):.2f} | {S.gain_q15(d, obj):.2f} | "
                     f"{S.s_cohort(d, th, ctx):.2f} | {S.s_foreign(d):.0f} | {S.score(d, th, ctx, obj):.2f} |")
    L.append("")
    return "\n".join(L)


def write_session_log(household, ctx, catalogue=None, out_dir=None):
    """Render and write the session log to <out_dir>/<label>.md. Returns the file path."""
    out_dir = out_dir or DEFAULT_LOG_DIR
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, _safe(household.get("label") or household.get("id_key")) + ".md")
    with open(path, "w") as f:
        f.write(render(household, ctx, catalogue))
    return path

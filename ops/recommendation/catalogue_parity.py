"""Deterministic parity comparison between the static bundle catalogue and a DB publication.

WHAT THIS SOLVES (WP-24 step A.1)
Ghar RE scores dishes from a spreadsheet-derived bundle (``ghar_re_service/data/bundle/
catalogue.json``); Aux RE retrieves from Qdrant, loaded from a Postgres-derived publication
(``re_engine.catalogue_publication_rows()``). Nothing compares the two, so they can drift without
anyone noticing. Migration 097 defers the cutover "until shadow parity is proven", but the Aux
shadow process holds the catalogue constant and compares *engines* — it never compares catalogue
*sources*. This module is that missing comparison.

WHAT IT DELIBERATELY DOES NOT DO
No database access, no file I/O, no network. Callers load both sides and pass dish dicts already in
Ghar's catalogue-constructor shape (for the publication side, that means passing rows through
``published_catalogue.to_ghar_dish()`` first). Keeping this module pure is what makes the parity
rule itself unit-testable without a production connection, matching ``catalogue_eligibility.py``.

It also never decides whether a delta is acceptable. It reports what differs and how severely;
the accept/reject call is a Founder decision recorded in WP-24 §B.2, not a threshold hidden here.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

# Field groups, ordered by how much a mismatch matters. Safety deltas can change what a user is
# told is safe to eat; scoring deltas silently change recommendation order; display deltas are
# cosmetic. The report keeps them separate so a reviewer never has to weigh a missing calorie
# count against a wrong Jain flag.
SAFETY_FIELDS: tuple[str, ...] = (
    "diet",
    "jain_compatible",
    "farali_compatible",
    "vegan_compatible",
)
SCORING_FIELDS: tuple[str, ...] = (
    "sig_band",
    "spice_level",
    "sweetness",
    "heaviness",
    "hero_role",
    "cuisine",
    "state_origin",
    "meal_type",
    "cooking_method",
    "texture",
    "richness",
    "weather_affinity",
    "scope_tier",
)
EFFORT_FIELDS: tuple[str, ...] = (
    "prep_mins",
    "cook_mins",
    "total_mins",
    "difficulty",
)
DISPLAY_FIELDS: tuple[str, ...] = (
    "calories",
    "serving_size",
    "primary_taste",
    "mouthfeel",
    "aroma_profile",
    "fermentation",
    "serving_temp",
)

FIELD_SEVERITY: dict[str, str] = {
    **dict.fromkeys(SAFETY_FIELDS, "safety"),
    **dict.fromkeys(SCORING_FIELDS, "scoring"),
    **dict.fromkeys(EFFORT_FIELDS, "effort"),
    **dict.fromkeys(DISPLAY_FIELDS, "display"),
}

COMPARED_FIELDS: tuple[str, ...] = SAFETY_FIELDS + SCORING_FIELDS + EFFORT_FIELDS + DISPLAY_FIELDS

# Which side lost information, not merely that the two differ. "bundle_richer" is the regression
# direction a cutover would introduce; "publication_richer" is what a cutover would gain. Reporting
# both is required by WP-24 §9 — the bundle is not automatically the better baseline.
DIRECTION_BUNDLE_RICHER = "bundle_richer"
DIRECTION_PUBLICATION_RICHER = "publication_richer"
DIRECTION_CONFLICT = "conflict"


def normalize_name(value: object) -> str:
    """Normalize a dish name for cross-source matching.

    Uses the exact convention already established by
    ``published_catalogue.canonical_identities_by_name()`` (casefold + whitespace collapse) so this
    module matches dishes the same way the running service does, rather than inventing a second,
    subtly different identity rule.
    """
    return " ".join(str(value).casefold().split())


def _is_empty(value: object) -> bool:
    """Treat None, empty string/list/dict as 'no value present'.

    Deliberately does NOT treat 0 or False as empty: a spice_level of 0 and a missing spice_level
    are different facts, and collapsing them would hide exactly the kind of default-substitution
    this tool exists to surface.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _comparable(value: object) -> object:
    """Reduce a field to a stable, order-insensitive form for equality testing.

    List-valued taxonomy fields (meal_type, cooking_method, ...) carry no meaningful order in
    either source, so comparing them as ordered sequences would report false differences.
    """
    if isinstance(value, (list, tuple)):
        return tuple(sorted(str(item) for item in value))
    if isinstance(value, str):
        return value.casefold().strip()
    return value


@dataclass(frozen=True)
class FieldDelta:
    """One field that does not agree between the two sources for one dish."""

    dish_name: str
    field_name: str
    severity: str
    direction: str
    bundle_value: object
    publication_value: object


@dataclass
class ParityReport:
    """Full comparison outcome. Counts are derived, never supplied by a caller."""

    bundle_count: int = 0
    publication_count: int = 0
    matched_count: int = 0
    bundle_only_names: list[str] = field(default_factory=list)
    publication_only_names: list[str] = field(default_factory=list)
    deltas: list[FieldDelta] = field(default_factory=list)

    def deltas_by_severity(self) -> dict[str, int]:
        """Count deltas grouped by severity, highest-stakes group first in the returned order."""
        counts: dict[str, int] = {"safety": 0, "scoring": 0, "effort": 0, "display": 0}
        for delta in self.deltas:
            counts[delta.severity] = counts.get(delta.severity, 0) + 1
        return counts

    def deltas_by_field(self) -> dict[str, int]:
        """Count deltas per field, so a systemic default-substitution stands out from noise."""
        counts: dict[str, int] = {}
        for delta in self.deltas:
            counts[delta.field_name] = counts.get(delta.field_name, 0) + 1
        return counts

    def systemic_fields(self, threshold: float = 0.9) -> list[str]:
        """Fields differing on at least ``threshold`` of matched dishes.

        A field that differs on essentially every dish is a hardcoded default or a mapping bug, not
        per-dish data drift — the signature-score gap in WP-24 §3 is exactly this shape. Separating
        it from scattered differences is what makes the report actionable.
        """
        if self.matched_count <= 0:
            return []
        counts = self.deltas_by_field()
        return sorted(
            name for name, count in counts.items() if count / self.matched_count >= threshold
        )


def compare_dish(
    dish_name: str,
    bundle_dish: Mapping[str, object],
    publication_dish: Mapping[str, object],
) -> list[FieldDelta]:
    """Compare one dish across both sources and return every field that disagrees."""
    deltas: list[FieldDelta] = []
    for field_name in COMPARED_FIELDS:
        bundle_value = bundle_dish.get(field_name)
        publication_value = publication_dish.get(field_name)
        if _comparable(bundle_value) == _comparable(publication_value):
            continue

        bundle_empty = _is_empty(bundle_value)
        publication_empty = _is_empty(publication_value)
        if publication_empty and not bundle_empty:
            direction = DIRECTION_BUNDLE_RICHER
        elif bundle_empty and not publication_empty:
            direction = DIRECTION_PUBLICATION_RICHER
        else:
            direction = DIRECTION_CONFLICT

        deltas.append(
            FieldDelta(
                dish_name=dish_name,
                field_name=field_name,
                severity=FIELD_SEVERITY[field_name],
                direction=direction,
                bundle_value=bundle_value,
                publication_value=publication_value,
            )
        )
    return deltas


def compare_catalogues(
    bundle_dishes: Iterable[Mapping[str, object]],
    publication_dishes: Iterable[Mapping[str, object]],
) -> ParityReport:
    """Compare two catalogues already in Ghar's constructor shape.

    Matching is by normalized dish name because the static bundle carries no canonical UUID — the
    publication side does, but a name is the only identifier both sides share. Name collisions
    within one source are reported rather than silently deduplicated, since a collision would make
    any per-dish verdict ambiguous.
    """
    bundle_by_name: dict[str, Mapping[str, object]] = {}
    bundle_collisions: list[str] = []
    for dish in bundle_dishes:
        key = normalize_name(dish.get("name"))
        if key in bundle_by_name:
            bundle_collisions.append(key)
            continue
        bundle_by_name[key] = dish

    publication_by_name: dict[str, Mapping[str, object]] = {}
    for dish in publication_dishes:
        key = normalize_name(dish.get("name"))
        if key in publication_by_name:
            continue
        publication_by_name[key] = dish

    report = ParityReport(
        bundle_count=len(bundle_by_name),
        publication_count=len(publication_by_name),
    )
    report.bundle_only_names = sorted(set(bundle_by_name) - set(publication_by_name))
    report.publication_only_names = sorted(set(publication_by_name) - set(bundle_by_name))

    for key in sorted(set(bundle_by_name) & set(publication_by_name)):
        report.matched_count += 1
        report.deltas.extend(compare_dish(key, bundle_by_name[key], publication_by_name[key]))

    return report


def format_report(report: ParityReport) -> str:
    """Render a human-readable summary for a reviewer deciding on a cutover.

    Intentionally reports raw counts and named systemic fields rather than a pass/fail verdict —
    per this module's docstring, the accept/reject decision belongs to the Founder, not here.
    """
    lines: list[str] = []
    lines.append("Catalogue parity report (WP-24 A.1)")
    lines.append("=" * 42)
    lines.append(f"Bundle dishes:       {report.bundle_count}")
    lines.append(f"Publication dishes:  {report.publication_count}")
    lines.append(f"Matched by name:     {report.matched_count}")
    lines.append(f"Bundle-only (lost on cutover):      {len(report.bundle_only_names)}")
    lines.append(f"Publication-only (gained):          {len(report.publication_only_names)}")
    lines.append("")

    severity_counts = report.deltas_by_severity()
    lines.append("Field deltas by severity (matched dishes only):")
    for severity in ("safety", "scoring", "effort", "display"):
        lines.append(f"  {severity:<9} {severity_counts.get(severity, 0)}")
    lines.append("")

    systemic = report.systemic_fields()
    if systemic:
        lines.append("SYSTEMIC fields (differ on >=90% of matched dishes —")
        lines.append("these indicate a hardcoded default or mapping gap, not data drift):")
        for field_name in systemic:
            lines.append(f"  - {field_name} [{FIELD_SEVERITY[field_name]}]")
    else:
        lines.append("No systemic field differences detected.")
    lines.append("")

    field_counts = report.deltas_by_field()
    if field_counts:
        lines.append("All differing fields (count, descending):")
        for field_name, count in sorted(field_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"  {count:>6}  {field_name} [{FIELD_SEVERITY[field_name]}]")

    return "\n".join(lines)

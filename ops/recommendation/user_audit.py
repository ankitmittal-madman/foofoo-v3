"""Generate a privacy-minimized, read-only recommendation audit for one profile."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from ops.recommendation.preference_training import database_url

AUDIT_SQL = """
WITH u AS (
  SELECT id, home_state, current_city, diet_type, cook_capability,
         onboarding_completed, city_overlay_weight, migration_duration_band, last_active_at
  FROM public.profiles WHERE id = %s
), recent_recs AS (
  SELECT created_at, slot, outcome, re_served, plate_count, plates,
         engine_version, config_version
  FROM public.recommendation_events
  WHERE household_id = (SELECT id FROM u)
  ORDER BY created_at DESC LIMIT 10
), feedback_counts AS (
  SELECT event_type, count(*) AS event_count
  FROM public.feedback_events
  WHERE household_id = (SELECT id FROM u) AND data_source = 'real'
  GROUP BY event_type
), feedback_summary AS (
  SELECT count(*) FILTER (WHERE data_source = 'real') AS real_feedback,
         count(*) FILTER (WHERE data_source = 'real' AND dish_id IS NOT NULL) AS resolved_feedback,
         (SELECT coalesce(jsonb_object_agg(event_type, event_count), '{}'::jsonb)
          FROM feedback_counts) AS by_type
  FROM public.feedback_events
  WHERE household_id = (SELECT id FROM u)
), taste AS (
  SELECT (SELECT count(*) FROM jsonb_object_keys(coalesce(t.class_affinity, '{}'::jsonb)))
           AS class_affinity_dimensions,
         (SELECT count(*) FROM jsonb_object_keys(coalesce(t.dish_affinity, '{}'::jsonb)))
           AS dish_affinity_dimensions,
         coalesce(cardinality(t.genome_tag_affinity), 0) AS genome_dimensions, t.updated_at
  FROM public.user_taste_vectors t WHERE t.profile_id = (SELECT id FROM u)
), re_state AS (
  SELECT confidence_score, interaction_count, cold_start_mode, re_engine_version,
         weight_tier, city_overlay_weight, updated_at
  FROM public.user_re_state WHERE profile_id = (SELECT id FROM u)
), lineage AS (
  SELECT
    (SELECT count(*) FROM public.slates s WHERE s.household_id = (SELECT id FROM u)) AS slate_count,
    (SELECT count(*) FROM public.recommendation_runs rr
      JOIN public.slates s ON s.id = rr.slate_id
      WHERE s.household_id = (SELECT id FROM u)) AS run_count,
    (SELECT coalesce(max(rr.candidate_count), 0) FROM public.recommendation_runs rr
      JOIN public.slates s ON s.id = rr.slate_id
      WHERE s.household_id = (SELECT id FROM u)) AS max_candidate_count,
    (SELECT coalesce(sum(rr.candidate_count), 0) FROM public.recommendation_runs rr
      JOIN public.slates s ON s.id = rr.slate_id
      WHERE s.household_id = (SELECT id FROM u)) AS total_candidates,
    (SELECT count(*) FROM public.recommendation_candidates rc
      JOIN public.recommendation_runs rr ON rr.id = rc.recommendation_run_id
      JOIN public.slates s ON s.id = rr.slate_id
      WHERE s.household_id = (SELECT id FROM u)
        AND rc.generator_scores ? 'shadow_preference_score') AS shadow_scored_candidates,
    (SELECT count(*) FROM public.slate_items si
      JOIN public.slates s ON s.id = si.slate_id
      WHERE s.household_id = (SELECT id FROM u)) AS displayed_items,
    (SELECT count(*) FROM public.slate_items si
      JOIN public.slates s ON s.id = si.slate_id
      WHERE s.household_id = (SELECT id FROM u)
        AND si.selection_propensity IS NOT NULL) AS calibrated_propensity_items,
    (SELECT max(s.created_at) FROM public.slates s
      WHERE s.household_id = (SELECT id FROM u)) AS latest_slate_at,
    (SELECT coalesce(jsonb_agg(surface), '[]'::jsonb) FROM (
      SELECT DISTINCT s.surface FROM public.slates s
      WHERE s.household_id = (SELECT id FROM u) ORDER BY s.surface
    ) surfaces) AS surfaces
), attribution AS (
  SELECT count(*) AS exact_attributed_feedback
  FROM public.feedback_events f
  JOIN public.recommendation_events r ON r.id = f.recommendation_event_id
  JOIN public.slates s ON s.household_id = r.household_id AND s.request_id = r.request_id
  JOIN public.recommendation_runs rr ON rr.slate_id = s.id AND rr.run_status = 'success'
  WHERE f.household_id = (SELECT id FROM u) AND f.data_source = 'real'
    AND f.event_type IN ('accept','like','dislike','never','not_today','swap','edit')
), cadence AS (
  SELECT novelty_budget, richness_debt, effort_debt, ordinary_meal_ratio,
         feature_version, updated_at
  FROM re_engine.household_cadence_state WHERE household_id = (SELECT id FROM u)
)
SELECT jsonb_build_object(
  'profile', (SELECT to_jsonb(u) - 'id' FROM u),
  'recommendation_event_count', (SELECT count(*) FROM public.recommendation_events
                                  WHERE household_id = (SELECT id FROM u)),
  'recent_recommendations', (SELECT coalesce(jsonb_agg(to_jsonb(recent_recs)
                                      ORDER BY created_at DESC), '[]'::jsonb) FROM recent_recs),
  'feedback', (SELECT to_jsonb(feedback_summary) FROM feedback_summary),
  'taste_vector', (SELECT to_jsonb(taste) FROM taste),
  're_state', (SELECT to_jsonb(re_state) FROM re_state),
  'lineage', (SELECT to_jsonb(lineage) FROM lineage),
  'attribution', (SELECT to_jsonb(attribution) FROM attribution),
  'cadence', (SELECT to_jsonb(cadence) FROM cadence),
  'variety', jsonb_build_object(
    'status', 'not_implemented',
    'detail', 'public.variety_window_state is absent from the production schema'
  ),
  'active_never', (SELECT count(*) FROM public.never_list
                    WHERE profile_id = (SELECT id FROM u) AND is_active),
  'active_not_today', (SELECT count(*) FROM public.not_today_suppression
                        WHERE profile_id = (SELECT id FROM u) AND is_active
                          AND effective_until > now())
) AS user_audit
"""


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def fetch_user_audit(connection: Any, profile_id: UUID) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(AUDIT_SQL, (str(profile_id),))
        row = cursor.fetchone()
    value = row.get("user_audit") if isinstance(row, Mapping) else row[0] if row else None
    if not isinstance(value, Mapping) or value.get("profile") is None:
        raise RuntimeError("Profile does not exist or is unavailable to the audit role")
    return _json_ready(value)


def write_audit(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = handle.name
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def connect_read_only(dsn: str) -> Any:
    import psycopg2

    connection = psycopg2.connect(dsn, connect_timeout=15, application_name="foofoo-user-audit")
    connection.set_session(readonly=True, autocommit=False)
    with connection.cursor() as cursor:
        cursor.execute("set local statement_timeout = '2min'")
    return connection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-id", type=UUID, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    connection = connect_read_only(database_url())
    try:
        report = fetch_user_audit(connection, args.profile_id)
        connection.rollback()
    finally:
        connection.close()
    write_audit(args.output, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

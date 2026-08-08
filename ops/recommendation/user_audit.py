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

from ghar_re_core.derivation import _state_of_city
from ops.recommendation.preference_training import database_url

PROFILE_CITY_SQL = "SELECT current_city FROM public.profiles WHERE id = %s"

AUDIT_SQL = """
WITH u AS (
  SELECT id, home_state, current_city, diet_type, cook_capability,
         onboarding_completed, city_overlay_weight, migration_duration_band, last_active_at,
         (SELECT state_code FROM re_engine.re_states
          WHERE lower(state_name) = lower(%s) LIMIT 1) AS local_state_code
  FROM public.profiles WHERE id = %s
), recent_recs AS (
  SELECT created_at, slot, outcome, re_served, plate_count, plates,
         engine_version, config_version
  FROM public.recommendation_events
  WHERE household_id = (SELECT id FROM u)
  ORDER BY created_at DESC LIMIT 10
), recent_recommendation_summary AS (
  SELECT
    count(*) AS event_count,
    count(*) FILTER (WHERE outcome = 'success' AND re_served) AS served_success_count,
    coalesce(sum(plate_count), 0) AS reported_plate_count,
    coalesce((SELECT jsonb_object_agg(slot, event_count ORDER BY slot) FROM (
      SELECT coalesce(slot, 'unspecified') AS slot, count(*) AS event_count
      FROM recent_recs GROUP BY coalesce(slot, 'unspecified')
    ) slot_counts), '{}'::jsonb) AS by_slot,
    coalesce(jsonb_agg(DISTINCT engine_version) FILTER (WHERE engine_version IS NOT NULL),
      '[]'::jsonb) AS engine_versions,
    coalesce(jsonb_agg(DISTINCT config_version) FILTER (WHERE config_version IS NOT NULL),
      '[]'::jsonb) AS config_versions
  FROM recent_recs
), recent_refresh_events AS (
  SELECT
    source.created_at,
    coalesce(source.slot, 'unspecified') AS slot,
    md5(coalesce((
      SELECT string_agg(item_key, '|' ORDER BY item_key)
      FROM (
        SELECT lower(coalesce(
          nullif(plate->>'episode_hash', ''),
          nullif(plate->>'display_name', ''),
          nullif(plate->>'name', '')
        )) AS item_key
        FROM jsonb_array_elements(source.plates) plate
      ) items
      WHERE item_key IS NOT NULL
    ), '')) AS set_hash,
    lower(coalesce(
      nullif(source.plates->0->>'episode_hash', ''),
      nullif(source.plates->0->>'display_name', ''),
      nullif(source.plates->0->>'name', '')
    )) AS first_item
  FROM (
    SELECT created_at, slot, plates
    FROM public.recommendation_events
    WHERE household_id = (SELECT id FROM u)
      AND outcome = 'success'
      AND re_served
      AND jsonb_typeof(plates) = 'array'
      AND jsonb_array_length(plates) > 0
    ORDER BY created_at DESC
    LIMIT 50
  ) source
), refresh_sequence AS (
  SELECT *, lag(set_hash) OVER (PARTITION BY slot ORDER BY created_at) AS previous_set_hash
  FROM recent_refresh_events
), refresh_by_slot AS (
  SELECT
    slot,
    count(*) AS event_count,
    count(DISTINCT set_hash) AS unique_sets,
    count(DISTINCT first_item) FILTER (WHERE first_item IS NOT NULL) AS unique_first_items,
    count(*) FILTER (WHERE previous_set_hash IS NOT NULL) AS comparable_refreshes,
    count(*) FILTER (
      WHERE previous_set_hash IS NOT NULL AND set_hash <> previous_set_hash
    ) AS changed_refreshes
  FROM refresh_sequence
  GROUP BY slot
), refresh_quality AS (
  SELECT
    coalesce(sum(event_count), 0) AS measured_events,
    coalesce(sum(unique_sets), 0) AS unique_sets_by_slot,
    coalesce(sum(comparable_refreshes), 0) AS comparable_refreshes,
    coalesce(sum(changed_refreshes), 0) AS changed_refreshes,
    CASE WHEN coalesce(sum(comparable_refreshes), 0) = 0 THEN 0
         ELSE round(sum(changed_refreshes)::numeric / sum(comparable_refreshes), 4)
    END AS meaningful_refresh_rate,
    coalesce(jsonb_object_agg(slot, jsonb_build_object(
      'event_count', event_count,
      'unique_sets', unique_sets,
      'unique_first_items', unique_first_items,
      'comparable_refreshes', comparable_refreshes,
      'changed_refreshes', changed_refreshes,
      'meaningful_refresh_rate', CASE WHEN comparable_refreshes = 0 THEN 0
        ELSE round(changed_refreshes::numeric / comparable_refreshes, 4) END
    ) ORDER BY slot), '{}'::jsonb) AS by_slot
  FROM refresh_by_slot
), recent_serving_events AS (
  SELECT created_at, coalesce(slot, 'unspecified') AS slot, plates
  FROM public.recommendation_events
  WHERE household_id = (SELECT id FROM u)
    AND outcome = 'success'
    AND re_served
    AND jsonb_typeof(plates) = 'array'
  ORDER BY created_at DESC
  LIMIT 50
), recent_served_plates AS (
  SELECT
    event.created_at,
    event.slot,
    plate.value AS plate,
    CASE WHEN jsonb_typeof(plate.value->'richness_score') = 'number'
      THEN (plate.value->>'richness_score')::numeric END AS richness_score
  FROM recent_serving_events event
  CROSS JOIN LATERAL jsonb_array_elements(event.plates) AS plate(value)
), richness_by_slot AS (
  SELECT
    slot,
    count(*) AS plate_count,
    count(richness_score) AS richness_scored_plates,
    round(avg(richness_score), 4) AS mean_richness_score,
    count(*) FILTER (WHERE richness_score > 0.5) AS above_neutral_richness_plates
  FROM recent_served_plates
  GROUP BY slot
), served_richness AS (
  SELECT
    coalesce(sum(plate_count), 0) AS plate_count,
    coalesce(sum(richness_scored_plates), 0) AS richness_scored_plates,
    CASE WHEN coalesce(sum(richness_scored_plates), 0) = 0 THEN NULL
      ELSE round(sum(mean_richness_score * richness_scored_plates) /
        sum(richness_scored_plates), 4) END AS mean_richness_score,
    coalesce(sum(above_neutral_richness_plates), 0) AS above_neutral_richness_plates,
    CASE WHEN coalesce(sum(richness_scored_plates), 0) = 0 THEN NULL
      ELSE round(sum(above_neutral_richness_plates)::numeric /
        sum(richness_scored_plates), 4) END AS above_neutral_richness_rate,
    coalesce(jsonb_object_agg(slot, jsonb_build_object(
      'plate_count', plate_count,
      'richness_scored_plates', richness_scored_plates,
      'mean_richness_score', mean_richness_score,
      'above_neutral_richness_plates', above_neutral_richness_plates,
      'above_neutral_richness_rate', CASE WHEN richness_scored_plates = 0 THEN NULL
        ELSE round(above_neutral_richness_plates::numeric / richness_scored_plates, 4) END
    ) ORDER BY slot), '{}'::jsonb) AS by_slot
  FROM richness_by_slot
), recent_served_components AS (
  SELECT
    plate.created_at,
    plate.slot,
    component.value AS component,
    CASE WHEN coalesce(component.value->>'dish_id', '') ~*
      '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
      THEN (component.value->>'dish_id')::uuid END AS dish_id
  FROM recent_served_plates plate
  CROSS JOIN LATERAL jsonb_array_elements(
    CASE WHEN jsonb_typeof(plate.plate->'components') = 'array'
      THEN plate.plate->'components' ELSE '[]'::jsonb END
  ) AS component(value)
), served_component_facts AS (
  SELECT
    component.created_at,
    component.slot,
    component.component,
    component.dish_id,
    dish.name AS canonical_name,
    cuisine.state_origin AS cuisine_state_origin,
    home.affinity_score AS home_affinity_score,
    local.affinity_score AS local_affinity_score,
    home_state.state_name AS home_state_name,
    local_state.state_name AS local_state_name
  FROM recent_served_components component
  CROSS JOIN u
  LEFT JOIN public.dishes dish ON dish.id = component.dish_id
  LEFT JOIN public.cuisines cuisine ON cuisine.id = dish.cuisine_id
  LEFT JOIN re_engine.re_states home_state ON home_state.state_code = u.home_state
  LEFT JOIN re_engine.re_states local_state ON local_state.state_code = u.local_state_code
  LEFT JOIN re_engine.re_dish_regional_affinity home
    ON home.dish_id = dish.id AND home.state_code = u.home_state
  LEFT JOIN re_engine.re_dish_regional_affinity local
    ON local.dish_id = dish.id AND local.state_code = u.local_state_code
), served_catalogue_quality AS (
  SELECT
    count(*) AS component_count,
    count(canonical_name) AS canonical_identity_count,
    count(*) FILTER (
      WHERE canonical_name IS NOT NULL
        AND lower(btrim(component->>'dish_name')) = lower(btrim(canonical_name))
    ) AS canonical_name_match_count,
    count(*) FILTER (
      WHERE canonical_name IS NOT NULL
        AND nullif(btrim(component->>'dish_name'), '') IS NOT NULL
        AND lower(btrim(component->>'dish_name')) <> lower(btrim(canonical_name))
    ) AS canonical_name_mismatch_count,
    count(home_affinity_score) AS home_affinity_count,
    round(avg(home_affinity_score), 4) AS mean_home_affinity_score,
    count(local_affinity_score) AS local_affinity_count,
    round(avg(local_affinity_score), 4) AS mean_local_affinity_score,
    count(*) FILTER (
      WHERE home_affinity_score IS NOT NULL OR local_affinity_score IS NOT NULL
    ) AS home_or_local_affinity_count,
    count(*) FILTER (
      WHERE lower(coalesce(cuisine_state_origin, '')) IN (
        lower(coalesce(home_state_name, '')), lower(coalesce(local_state_name, ''))
      )
    ) AS home_or_local_cuisine_origin_count,
    CASE WHEN count(*) = 0 THEN NULL
      ELSE round(count(canonical_name)::numeric / count(*), 4) END AS canonical_identity_rate,
    CASE WHEN count(*) = 0 THEN NULL
      ELSE round((count(*) FILTER (
        WHERE home_affinity_score IS NOT NULL OR local_affinity_score IS NOT NULL
      ))::numeric / count(*), 4) END AS regional_affinity_coverage
  FROM served_component_facts
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
         (SELECT count(*) FROM jsonb_object_keys(coalesce(t.tag_affinity, '{}'::jsonb)))
           AS tag_affinity_dimensions,
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
    (SELECT count(*) FROM ml.feature_snapshots fs
      JOIN public.recommendation_runs rr ON rr.feature_snapshot_id = fs.id
      JOIN public.slates s ON s.id = rr.slate_id
      WHERE s.household_id = (SELECT id FROM u)
        AND jsonb_typeof(fs.values->'household') = 'object'
        AND fs.values->'household' <> '{}'::jsonb) AS usable_feature_snapshots,
    (SELECT max(s.created_at) FROM public.slates s
      WHERE s.household_id = (SELECT id FROM u)) AS latest_slate_at,
    (SELECT coalesce(jsonb_agg(surface), '[]'::jsonb) FROM (
      SELECT DISTINCT s.surface FROM public.slates s
      WHERE s.household_id = (SELECT id FROM u) ORDER BY s.surface
    ) surfaces) AS surfaces
), labeled_feedback AS (
  SELECT f.*
  FROM public.feedback_events f
  WHERE f.household_id = (SELECT id FROM u)
    AND f.data_source = 'real'
    AND f.event_type IN (
      'accept','like','make_this','cooked','completed','dislike','never','regretted'
    )
), attribution AS (
  SELECT
    (SELECT count(*) FROM labeled_feedback) AS labeled_feedback,
    (SELECT count(*) FROM labeled_feedback WHERE dish_id IS NOT NULL) AS identity_resolved_feedback,
    count(*) AS exact_attributed_feedback,
    CASE WHEN (SELECT count(*) FROM labeled_feedback) = 0 THEN 0
         ELSE round(count(*)::numeric / (SELECT count(*) FROM labeled_feedback), 4)
    END AS exact_attribution_coverage
  FROM labeled_feedback f
  JOIN public.recommendation_events r ON r.id = f.recommendation_event_id
  JOIN public.slates s ON s.household_id = r.household_id AND s.request_id = r.request_id
  JOIN public.recommendation_runs rr ON rr.slate_id = s.id AND rr.run_status = 'success'
  JOIN ml.feature_snapshots fs ON fs.id = rr.feature_snapshot_id
    AND jsonb_typeof(fs.values->'household') = 'object'
    AND fs.values->'household' <> '{}'::jsonb
  JOIN public.outcome_events o ON o.idempotency_key = f.id
    AND o.slate_id = s.id AND o.episode_hash IS NOT NULL
  JOIN public.slate_items i ON i.slate_id = s.id AND i.episode_hash = o.episode_hash
  JOIN public.dishes d ON d.id = f.dish_id
), cadence AS (
  SELECT novelty_budget, richness_debt, effort_debt, ordinary_meal_ratio,
         feature_version, updated_at
  FROM re_engine.household_cadence_state WHERE household_id = (SELECT id FROM u)
), variety AS (
  SELECT
    count(*) AS dimension_rows,
    count(*) FILTER (WHERE dimension_code = 'dish_name') AS recent_dish_dimensions,
    count(*) FILTER (WHERE dimension_code = 'meal_class') AS recent_class_dimensions,
    count(*) FILTER (WHERE dimension_code = 'cuisine') AS recent_cuisine_dimensions,
    coalesce(sum(count_in_window), 0) AS total_window_exposures,
    max(updated_at) AS updated_at,
    coalesce(jsonb_agg(jsonb_build_object(
      'dimension_code', dimension_code,
      'entity_key', entity_key,
      'window_code', window_code,
      'last_seen_at', last_seen_at,
      'count_in_window', count_in_window
    ) ORDER BY window_code, dimension_code, count_in_window DESC, entity_key)
      FILTER (WHERE dimension_code IS NOT NULL), '[]'::jsonb) AS dimensions
  FROM re_engine.variety_window_state
  WHERE household_id = (SELECT id FROM u)
)
SELECT jsonb_build_object(
  'profile', (SELECT to_jsonb(u) - 'id' FROM u),
  'recommendation_event_count', (SELECT count(*) FROM public.recommendation_events
                                  WHERE household_id = (SELECT id FROM u)),
  'recent_recommendation_summary', (SELECT to_jsonb(recent_recommendation_summary)
                                    FROM recent_recommendation_summary),
  'refresh_quality', (SELECT to_jsonb(refresh_quality) FROM refresh_quality),
  'served_richness', (SELECT to_jsonb(served_richness) FROM served_richness),
  'served_catalogue_quality', (SELECT to_jsonb(served_catalogue_quality)
                               FROM served_catalogue_quality),
  'feedback', (SELECT to_jsonb(feedback_summary) FROM feedback_summary),
  'taste_vector', (SELECT to_jsonb(taste) FROM taste),
  're_state', (SELECT to_jsonb(re_state) FROM re_state),
  'lineage', (SELECT to_jsonb(lineage) FROM lineage),
  'attribution', (SELECT to_jsonb(attribution) FROM attribution),
  'cadence', (SELECT to_jsonb(cadence) FROM cadence),
  'variety', (SELECT to_jsonb(variety) FROM variety),
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
        cursor.execute(PROFILE_CITY_SQL, (str(profile_id),))
        profile_row = cursor.fetchone()
        current_city = (
            profile_row.get("current_city")
            if isinstance(profile_row, Mapping)
            else profile_row[0]
            if profile_row
            else None
        )
        if not isinstance(current_city, str) or not current_city.strip():
            raise RuntimeError("Profile does not exist or has no current city")
        local_state = _state_of_city(current_city)
        cursor.execute(AUDIT_SQL, (local_state, str(profile_id)))
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

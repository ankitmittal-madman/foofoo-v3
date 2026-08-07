-- Aggregate-only validation for migration 095. Safe for production SQL Editor output.
SELECT
  to_regclass('re_engine.current_dish_temporal_attributes') IS NOT NULL AS attribute_view_exists,
  to_regclass('re_engine.meal_attribute_exposures') IS NOT NULL AS exposure_table_exists,
  to_regclass('re_engine.meal_attribute_temporal_state') IS NOT NULL AS state_table_exists,
  to_regprocedure('public.refresh_meal_attribute_temporal_state(uuid)') IS NOT NULL AS refresh_exists,
  to_regprocedure('public.record_meal_attribute_exposure_state(uuid,jsonb)') IS NOT NULL AS writer_exists,
  to_regprocedure('public.get_meal_attribute_temporal_state(uuid)') IS NOT NULL AS reader_exists;

SELECT dimension_code, count(*) AS attribute_rows
FROM re_engine.current_dish_temporal_attributes
GROUP BY dimension_code ORDER BY dimension_code;

SELECT
  count(*) FILTER (WHERE explicit_positive_count_28d < 0) AS invalid_positive_counts,
  count(*) FILTER (WHERE explicit_negative_count_28d < 0) AS invalid_negative_counts,
  count(*) FILTER (WHERE exposure_count_14d < 0) AS invalid_exposure_counts,
  count(*) FILTER (WHERE mean_positive_spacing_days NOT BETWEEN 0 AND 365) AS invalid_spacing,
  count(*) FILTER (WHERE cardinality(positive_meal_dates_28d) > 28) AS oversized_positive_dates,
  count(*) FILTER (WHERE cardinality(negative_meal_dates_28d) > 28) AS oversized_negative_dates,
  count(*) FILTER (WHERE cardinality(exposure_meal_dates_14d) > 14) AS oversized_exposure_dates
FROM re_engine.meal_attribute_temporal_state;

SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 're_engine'
  AND table_name IN ('meal_attribute_exposures','meal_attribute_temporal_state')
ORDER BY table_name, grantee, privilege_type;

-- Rollback 117
BEGIN;
DELETE FROM re_engine.re_dish_regional_affinity;
DELETE FROM re_engine.re_addon_dish_options;
DELETE FROM re_engine.re_class_dish_options;
COMMIT;

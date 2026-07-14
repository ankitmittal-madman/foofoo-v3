-- Migration: 116_seed_re_nonveg_logic.sql
-- Title: re_engine.re_nonveg_logic (36)
-- Layer: re_engine seed (WP-6RE-GEN v1.0); requires migration 030 (SER-001 city_tier)
-- Generated: 2026-07-14T05:57:31Z by database/etl/generate_re_seeds.py (deterministic)
-- Provenance:
--   source: NonVeg_Logic_v3 (sha256:bf8e1bd86d831005)
-- Business rules:
--   - state_code via state_ut crosswalk; weekly_nonveg_slots=default_omnivore_meals_week
--   - preferred_slots = preferred_nonveg_classes split to text[] (source class names carried verbatim)
-- Idempotent: ON CONFLICT DO NOTHING; surrogate UUIDs = md5(natural_key)::uuid. Paired rollback.
-- Supersedes illustrative rows in seed 101/102 for these tables (never edited in place).

BEGIN;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('AP',3.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_CHICKEN_BIRYANI_PULAO|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('AR',4.0,ARRAY['LD_NORTHEAST_SMOKED_PORK_MEAT|LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_COMMUNITY_RED_MEAT|LD_EGG_CURRY_BHURJI']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('AS',4.0,ARRAY['LD_NORTHEAST_SMOKED_PORK_MEAT|LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_COMMUNITY_RED_MEAT|LD_EGG_CURRY_BHURJI']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('BR',2.0,ARRAY['LD_FISH_CURRY_RICE|LD_BENGALI_FISH_MEAL|LD_EGG_CURRY_BHURJI|LD_CHICKEN_HOME_CURRY|LD_FISH_FRY_MEAL']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('CT',2.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('GA',4.0,ARRAY['LD_FISH_CURRY_RICE|LD_PRAWN_CRAB_COASTAL|LD_FISH_FRY_MEAL|LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('GJ',0.5,ARRAY['LD_EGG_CURRY_BHURJI|LD_SUNDAY_OUTSIDE_NONVEG']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('HR',1.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY|LD_TANDOORI_GRILL_NONVEG']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('HP',2.0,ARRAY['LD_MUTTON_SUNDAY_CURRY|LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_NONVEG_LIGHT_SOUP_STEW']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('JH',2.0,ARRAY['LD_FISH_CURRY_RICE|LD_BENGALI_FISH_MEAL|LD_EGG_CURRY_BHURJI|LD_CHICKEN_HOME_CURRY|LD_FISH_FRY_MEAL']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('KA',3.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_CHICKEN_BIRYANI_PULAO|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('KL',4.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_CHICKEN_BIRYANI_PULAO|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('MP',2.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('MH',2.0,ARRAY['LD_FISH_CURRY_RICE|LD_FISH_FRY_MEAL|LD_CHICKEN_HOME_CURRY|LD_MUTTON_SUNDAY_CURRY|LD_PRAWN_CRAB_COASTAL']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('MN',4.0,ARRAY['LD_NORTHEAST_SMOKED_PORK_MEAT|LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_COMMUNITY_RED_MEAT|LD_EGG_CURRY_BHURJI']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('ML',4.0,ARRAY['LD_NORTHEAST_SMOKED_PORK_MEAT|LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_COMMUNITY_RED_MEAT|LD_EGG_CURRY_BHURJI']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('MZ',4.0,ARRAY['LD_NORTHEAST_SMOKED_PORK_MEAT|LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_COMMUNITY_RED_MEAT|LD_EGG_CURRY_BHURJI']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('NL',4.0,ARRAY['LD_NORTHEAST_SMOKED_PORK_MEAT|LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_COMMUNITY_RED_MEAT|LD_EGG_CURRY_BHURJI']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('OD',3.0,ARRAY['LD_FISH_CURRY_RICE|LD_BENGALI_FISH_MEAL|LD_EGG_CURRY_BHURJI|LD_CHICKEN_HOME_CURRY|LD_FISH_FRY_MEAL']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('PB',1.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY|LD_TANDOORI_GRILL_NONVEG']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('RJ',0.5,ARRAY['LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY|LD_TANDOORI_GRILL_NONVEG']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('SK',3.0,ARRAY['LD_MUTTON_SUNDAY_CURRY|LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_NONVEG_LIGHT_SOUP_STEW']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('TN',3.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_CHICKEN_BIRYANI_PULAO|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('TS',3.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_CHICKEN_BIRYANI_PULAO|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('TR',4.0,ARRAY['LD_FISH_CURRY_RICE|LD_BENGALI_FISH_MEAL|LD_EGG_CURRY_BHURJI|LD_CHICKEN_HOME_CURRY|LD_FISH_FRY_MEAL']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('UP',2.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY|LD_TANDOORI_GRILL_NONVEG']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('UK',2.0,ARRAY['LD_MUTTON_SUNDAY_CURRY|LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_NONVEG_LIGHT_SOUP_STEW']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('WB',3.0,ARRAY['LD_FISH_CURRY_RICE|LD_BENGALI_FISH_MEAL|LD_EGG_CURRY_BHURJI|LD_CHICKEN_HOME_CURRY|LD_FISH_FRY_MEAL']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('AN',4.0,ARRAY['LD_FISH_CURRY_RICE|LD_PRAWN_CRAB_COASTAL|LD_FISH_FRY_MEAL|LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('CH',1.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY|LD_TANDOORI_GRILL_NONVEG']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('DN',2.0,ARRAY['LD_FISH_CURRY_RICE|LD_FISH_FRY_MEAL|LD_CHICKEN_HOME_CURRY|LD_MUTTON_SUNDAY_CURRY|LD_PRAWN_CRAB_COASTAL']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('DL',2.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY|LD_TANDOORI_GRILL_NONVEG']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('JK',3.0,ARRAY['LD_MUTTON_SUNDAY_CURRY|LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_NONVEG_LIGHT_SOUP_STEW']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('LA',3.0,ARRAY['LD_MUTTON_SUNDAY_CURRY|LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI|LD_NONVEG_LIGHT_SOUP_STEW']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('LD',4.0,ARRAY['LD_FISH_CURRY_RICE|LD_PRAWN_CRAB_COASTAL|LD_FISH_FRY_MEAL|LD_CHICKEN_HOME_CURRY|LD_EGG_CURRY_BHURJI']::text[]) ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ('PY',3.0,ARRAY['LD_CHICKEN_HOME_CURRY|LD_FISH_CURRY_RICE|LD_CHICKEN_BIRYANI_PULAO|LD_EGG_CURRY_BHURJI|LD_MUTTON_SUNDAY_CURRY']::text[]) ON CONFLICT (state_code) DO NOTHING;
COMMIT;

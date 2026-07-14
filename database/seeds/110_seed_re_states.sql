-- Migration: 110_seed_re_states.sql
-- Title: re_engine.re_states (36)
-- Layer: re_engine seed (WP-6RE-GEN v1.0); requires migration 030 (SER-001 city_tier)
-- Generated: 2026-07-14T05:57:31Z by database/etl/generate_re_seeds.py (deterministic)
-- Provenance:
--   source: State_Profile_v3 (Indian_Meal_Cohort_Persona_DB_v3.xlsx sha256:bf8e1bd86d831005)
-- Business rules:
--   - state_code = documented state_ut->2-letter crosswalk (29/36 verified vs region_food_affinity.csv)
--   - region = documented region_archetype(9)->region(5) collapse (NE->east, HIMALAYAN->north, ISLAND->south)
--   - state_name = state_ut verbatim
-- Idempotent: ON CONFLICT DO NOTHING; surrogate UUIDs = md5(natural_key)::uuid. Paired rollback.
-- Supersedes illustrative rows in seed 101/102 for these tables (never edited in place).

BEGIN;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('AP','Andhra Pradesh','south') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('AR','Arunachal Pradesh','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('AS','Assam','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('BR','Bihar','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('CT','Chhattisgarh','central') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('GA','Goa','south') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('GJ','Gujarat','west') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('HR','Haryana','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('HP','Himachal Pradesh','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('JH','Jharkhand','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('KA','Karnataka','south') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('KL','Kerala','south') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('MP','Madhya Pradesh','central') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('MH','Maharashtra','west') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('MN','Manipur','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('ML','Meghalaya','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('MZ','Mizoram','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('NL','Nagaland','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('OD','Odisha','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('PB','Punjab','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('RJ','Rajasthan','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('SK','Sikkim','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('TN','Tamil Nadu','south') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('TS','Telangana','south') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('TR','Tripura','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('UP','Uttar Pradesh','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('UK','Uttarakhand','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('WB','West Bengal','east') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('AN','Andaman & Nicobar Islands','south') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('CH','Chandigarh','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('DN','Dadra & Nagar Haveli and Daman & Diu','west') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('DL','Delhi','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('JK','Jammu & Kashmir','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('LA','Ladakh','north') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('LD','Lakshadweep','south') ON CONFLICT (state_code) DO NOTHING;
INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES ('PY','Puducherry','south') ON CONFLICT (state_code) DO NOTHING;
COMMIT;

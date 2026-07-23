-- Rollback: 035_ghar_re_household_runtime.sql
DROP TABLE IF EXISTS ghar_re.recommendation_event;
DROP TABLE IF EXISTS ghar_re.feedback_event;
DROP TABLE IF EXISTS ghar_re.household_modes;
DROP TABLE IF EXISTS ghar_re.household_context;
DROP TABLE IF EXISTS ghar_re.household_profile;
DROP TABLE IF EXISTS ghar_re.households;

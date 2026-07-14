-- Rollback 111
BEGIN;
DELETE FROM re_engine.re_persona_assignment_rules;
DELETE FROM re_engine.re_routing_rules;
DELETE FROM re_engine.re_personas WHERE persona_code IN ('P01','P02','P03','P04','P05','P06','P07','P08','P09','P10','P11','P12','P13','P14','P15','P16','P17','P18','P19','P20','P21','P22','P23','P24','P25','P26','P27','P28','P29','P30','P31','P32','P33','P34','P35','P36','P37','P38','P39','P40','P41');
DELETE FROM re_engine.re_subcohorts WHERE subcohort_code IN ('SC1A','SC1B','SC1C','SC1D','SC1E','SC1F','SC2A','SC2B','SC2C','SC2D','SC2E','SC2F','SC2G','SC3A','SC3B','SC3C','SC3D','SC3E','SC3F','SC4A','SC4B','SC4C','SC4D','SC4E','SC4F','SC5A','SC5B','SC5C','SC5D','SC5E','SC5F','SC5G','SC5H','SC5I','SC5J','SC5K','SC5L','SC5M','SC5N','SC5O','SC5P');
DELETE FROM re_engine.re_main_cohorts WHERE cohort_code IN ('MC_SOLO','MC_COUPLE','MC_NUCLEAR_FAMILY','MC_JOINT_FAMILY','MC_PG_HOSTEL');
COMMIT;

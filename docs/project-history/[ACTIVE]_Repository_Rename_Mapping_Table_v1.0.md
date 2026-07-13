# [ACTIVE]_Repository_Rename_Mapping_Table_v1.0

**Status:** ACTIVE  **Version:** v1.0  **Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_Repository_Rename_Mapping_Table_v1.0.md
**Supersedes:** None  **Dependencies:** [ACTIVE]_Repository_Naming_Standard_v1.0, [ACTIVE]_Repository_Normalization_Report_v1.0

## Executive Summary

Complete, git-verified record of all 75 files renamed in the WP-5AA normalization pass (`git mv` only — history preserved). Old path `=>` new path. Generated directly from `git status` at execution time, not hand-transcribed.

## 1. Rename Map (old => new)

```
"database/migrations/[ACTIVE]_001_extensions_and_schema_setup 1.0.sql" => database/migrations/001_extensions_and_schema_setup.sql
"database/migrations/[ACTIVE]_002_reference_tier0 1.0.sql" => database/migrations/002_reference_tier0.sql
"database/migrations/[ACTIVE]_003_reference_tier1 1.1.sql" => database/migrations/003_reference_tier1.sql
"database/migrations/[ACTIVE]_004_reference_tier2 1.0.sql" => database/migrations/004_reference_tier2.sql
"database/migrations/[ACTIVE]_005_profiles 1.0.sql" => database/migrations/005_profiles.sql
"database/migrations/[ACTIVE]_006_profile_dependent_public 1.0.sql" => database/migrations/006_profile_dependent_public.sql
"database/migrations/[ACTIVE]_007_re_identity_interaction_history 1.0.sql" => database/migrations/007_re_identity_interaction_history.sql
database/migrations/[ACTIVE]_008_content_core1.1.sql => database/migrations/008_content_core.sql
"database/migrations/[ACTIVE]_009_content_junctions 1.0.sql" => database/migrations/009_content_junctions.sql
"database/migrations/[ACTIVE]_010_trigger_functions_and_triggers 1.1.sql" => database/migrations/010_trigger_functions_and_triggers.sql
"database/migrations/[ACTIVE]_011_planning_tables 1.1.sql" => database/migrations/011_planning_tables.sql
"database/migrations/[ACTIVE]_012_interaction_audit_appendonly 1.0.sql" => database/migrations/012_interaction_audit_appendonly.sql
"database/migrations/[ACTIVE]_013_config_tables 1.0.sql" => database/migrations/013_config_tables.sql
"database/migrations/[ACTIVE]_014_persona_assignment_and_priors 1.0.sql" => database/migrations/014_persona_assignment_and_priors.sql
"database/migrations/[ACTIVE]_015_operational_audit_public 1.1.sql" => database/migrations/015_operational_audit_public.sql
"database/migrations/[ACTIVE]_016_dish_features 1.0.sql" => database/migrations/016_dish_features.sql
"database/migrations/[ACTIVE]_017_initial_partitions 1.0.sql" => database/migrations/017_initial_partitions.sql
"database/migrations/[ACTIVE]_018_meal_classes_mirror_sync 1.1.sql" => database/migrations/018_meal_classes_mirror_sync.sql
"database/migrations/[ACTIVE]_019_rls_policies 1.0.sql" => database/migrations/019_rls_policies.sql
"database/migrations/[ACTIVE]_020_indexes 1.0.sql" => database/migrations/020_indexes.sql
"docs/architecture/Copy of _ACTIVE__DOC-P3-02_Conceptual_Domain_Model_v1.0.md" => docs/architecture/[DRAFT]_DOC-P3-02_Conceptual_Domain_Model_v1.1.md
"docs/architecture/Copy of _ACTIVE__DOC-P3-03A_Logic_Governance_Matrix_v1.0.md" => docs/architecture/[DRAFT]_DOC-P3-03A_Logic_Governance_Matrix_v1.0.md
"docs/architecture/Copy of _ACTIVE__DOC-P3-03_Business_Logic_Specification_v1.md" => docs/architecture/[DRAFT]_DOC-P3-03_Business_Logic_Specification_v1.0.md
"docs/architecture/Copy of _ACTIVE__DOC-P3-04_Data_Architecture_ERD_v1_3.md" => docs/architecture/[DRAFT]_DOC-P3-04_Data_Architecture_ERD_v1.3.md
"docs/architecture/Copy of _ACTIVE__DOC-P3-05_Part_A_Readiness_Migration_Strategy_v1_2.md" => docs/architecture/[DRAFT]_DOC-P3-05_Part_A_Readiness_Migration_Strategy_v1.2.md
"docs/architecture/Copy of _ACTIVE__DOC-P3-06_API_Contract_Specification_v1_2.md" => docs/architecture/[FROZEN]_DOC-P3-06_API_Contract_Specification_v1.2.md
"docs/architecture/Copy of _ACTIVE__DOC-P3-07_Security_Architecture_v1_2.md" => docs/architecture/[FROZEN]_DOC-P3-07_Security_Architecture_v1.2.md
"docs/architecture/Copy of _ACTIVE__DOC-P3-08_Integration_and_Infrastructure_Architecture_v1_1.md" => docs/architecture/[FROZEN]_DOC-P3-08_Integration_and_Infrastructure_Architecture_v1.1.md
"docs/governance/Copy of _ACTIVE__DOC-P3-05_Architecture_Gap_Register_v1_1.md" => docs/governance/[ACTIVE]_DOC-P3-05_Architecture_Gap_Register_v1.1.md
"docs/governance/Copy of _ACTIVE__DOC-P3-09_Knowledge_Integration_Governance_v1_3.md" => docs/governance/[ACTIVE]_DOC-P3-09_Knowledge_Integration_Governance_v1.3.md
"docs/governance/Copy of _ACTIVE__DOC-P3-10_Seed_Data_Integration_Framework_v1_1.md" => docs/governance/[ACTIVE]_DOC-P3-10_Seed_Data_Integration_Framework_v1.1.md
"docs/governance/Copy of _ACTIVE__DOC-P3-12_Governance_Improvement_Backlog_v1_2.md" => docs/governance/[ACTIVE]_DOC-P3-12_Governance_Improvement_Backlog_v1.2.md
"docs/governance/Copy of _ACTIVE__PM-SUPP-02_Risk_Register.md" => docs/governance/[ACTIVE]_PM-SUPP-02_Risk_Register_v1.0.md
"docs/governance/Copy of _ACTIVE__Project_Baseline_Register_v1_5.md" => docs/governance/[ACTIVE]_Project_Baseline_Register_v1.5.md
docs/governance/Repository_Naming_Conflict_Report_v1_0.md => docs/governance/[ACTIVE]_Repository_Naming_Conflict_Report_v1.0.md
docs/governance/Repository_Recovery_Backlog_v1_0.md => docs/governance/[ACTIVE]_Repository_Recovery_Backlog_v1.0.md
docs/governance/Repository_Recovery_Decision_Log_v1_0.md => docs/governance/[ACTIVE]_Repository_Recovery_Decision_Log_v1.0.md
docs/governance/Repository_Recovery_Risk_Register_v1_0.md => docs/governance/[ACTIVE]_Repository_Recovery_Risk_Register_v1.0.md
"docs/governance/Copy of _ACTIVE__APDF_Framework_vNext_Addendum_v2_0.md" => docs/governance/[DRAFT]_APDF_Framework_vNext_Addendum_v2.0.md
"docs/governance/Copy of _ACTIVE__Phase3_5_Architecture_Decision_Review_v1_0.md" => docs/governance/[DRAFT]_Phase3_5_Architecture_Decision_Review_v1.0.md
"docs/governance/Copy of _ACTIVE__Phase3_5_Architecture_Freeze_v1_0.md" => docs/governance/[DRAFT]_Phase3_5_Architecture_Freeze_v1.0.md
"docs/governance/Copy of _ACTIVE__APDF_Framework_Base_v1.md" => docs/governance/[SUPERSEDED]_APDF_Framework_Base_v1.0.md
"docs/project-history/Copy of _ACTIVE__Engineering_Handover_Project_Continuity_Package_v1_3.md" => docs/project-history/[ACTIVE]_Engineering_Handover_Project_Continuity_Package_v1.3.md
docs/project-history/Migration_Recovery_Decision_Log_v1_0.md => docs/project-history/[ACTIVE]_Migration_Recovery_Decision_Log_v1.0.md
docs/project-history/Migration_Recovery_Evidence_Register_v1_0.md => docs/project-history/[ACTIVE]_Migration_Recovery_Evidence_Register_v1.0.md
docs/project-history/Migration_Recovery_Report_v1_0.md => docs/project-history/[ACTIVE]_Migration_Recovery_Report_v1.0.md
docs/project-history/Migration_Recovery_Validation_Report_v1_0.md => docs/project-history/[ACTIVE]_Migration_Recovery_Validation_Report_v1.0.md
docs/project-history/Repository_Completeness_Audit_v1_0.md => docs/project-history/[ACTIVE]_Repository_Completeness_Audit_v1.0.md
"docs/project-history/certificates/Copy of _ACTIVE__DOC-P3-08_Readiness_Report_v1_1.md" => docs/project-history/certificates/[ACTIVE]_DOC-P3-08_Readiness_Report_v1.1.md
docs/project-history/certificates/REPO-BOOT-03_Repository_Migration_Certification_v1_0.md => docs/project-history/certificates/[DRAFT]_REPO-BOOT-03_Repository_Migration_Certification_v1.0.md
docs/project-history/work-packages/_ACTIVE__REPO-BOOT-01_Repository_Bootstrap_Execution_Package_v1_0.md => docs/project-history/work-packages/[DRAFT]_REPO-BOOT-01_Repository_Bootstrap_Execution_Package_v1.0.md
docs/project-history/work-packages/_ACTIVE__REPO-BOOT-02_Repository_Bootstrap_Work_Package_and_AI_Collaboration_Model_v1_0.md => docs/project-history/work-packages/[DRAFT]_REPO-BOOT-02_Repository_Bootstrap_Work_Package_and_AI_Collaboration_Model_v1.0.md
"docs/research/Copy of _ACTIVE__DOC-P3-11_Discovery_Execution_Register_v1_20.md" => docs/research/[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.20.md
"docs/research/Copy of _ACTIVE__Phase3_5_Phase2_Knowledge_Acquisition_v1_2.md" => docs/research/[ACTIVE]_Phase3_5_Phase2_Knowledge_Acquisition_v1.2.md
docs/research/_ACTIVE__Batch1_Governance_Evaluation_Package_v1_0.md => docs/research/[DRAFT]_Batch1_Governance_Evaluation_Package_v1.0.md
docs/research/_ACTIVE__Batch1_Resolution_Package_v1_1.md => docs/research/[DRAFT]_Batch1_Resolution_Package_v1.1.md
docs/research/_ACTIVE__Batch2_Canonicalization_Package_v1_0.md => docs/research/[DRAFT]_Batch2_Canonicalization_Package_v1.0.md
docs/research/_ACTIVE__Batch2_GapAnalysis_Package_v1_0.md => docs/research/[DRAFT]_Batch2_GapAnalysis_Package_v1.0.md
docs/research/_ACTIVE__Batch2_Mapping_Package_v1_0.md => docs/research/[DRAFT]_Batch2_Mapping_Package_v1.0.md
docs/research/_ACTIVE__Batch2_Resolution_Package_v1_0.md => docs/research/[DRAFT]_Batch2_Resolution_Package_v1.0.md
docs/research/_ACTIVE__Batch3_Pipeline_Package_v1_0.md => docs/research/[DRAFT]_Batch3_Pipeline_Package_v1.0.md
docs/research/_ACTIVE__Batch4_Pipeline_Package_v1_0.md => docs/research/[DRAFT]_Batch4_Pipeline_Package_v1.0.md
docs/research/_ACTIVE__Batch4_Technical_Review_and_Freeze_Recommendation_v1_0.md => docs/research/[DRAFT]_Batch4_Technical_Review_and_Freeze_Recommendation_v1.0.md
docs/research/_ACTIVE__Batch6_Pipeline_Package_v1_0.md => docs/research/[DRAFT]_Batch6_Pipeline_Package_v1.0.md
"docs/research/Copy of _ACTIVE__Phase3_5_Project_Integration_Review_v1_0.md" => docs/research/[DRAFT]_Phase3_5_Project_Integration_Review_v1.0.md
docs/research/_ACTIVE__Batch1_Architecture_Confirmation_Package_v1_1.md => docs/research/[FROZEN]_Batch1_Architecture_Confirmation_Package_v1.1.md
docs/research/_ACTIVE__Batch1_Canonicalization_Package_v1_1.md => docs/research/[FROZEN]_Batch1_Canonicalization_Package_v1.1.md
docs/research/_ACTIVE__Batch1_Discovery_Report_v1_1_FROZEN.md => docs/research/[FROZEN]_Batch1_Discovery_Report_v1.1.md
docs/research/_ACTIVE__Batch1_GapAnalysis_Package_v1_1.md => docs/research/[FROZEN]_Batch1_GapAnalysis_Package_v1.1.md
docs/research/_ACTIVE__Batch1_Mapping_Package_v1_1.md => docs/research/[FROZEN]_Batch1_Mapping_Package_v1.1.md
docs/research/_ACTIVE__Batch2_Discovery_Report_v1_1.md => docs/research/[FROZEN]_Batch2_Discovery_Report_v1.1.md
docs/research/_ACTIVE__Batch5_Pipeline_Package_v1_1.md => docs/research/[FROZEN]_Batch5_Pipeline_Package_v1.1.md
"docs/roadmaps/Copy of _ACTIVE__FooFoo_Project_Roadmap_v1_1.md" => docs/roadmaps/[ACTIVE]_FooFoo_Project_Roadmap_v1.1.md
"docs/roadmaps/Copy of _ACTIVE__PM-SUPP-01_Roadmap.md" => docs/roadmaps/[ACTIVE]_PM-SUPP-01_Roadmap_v1.0.md
docs/roadmaps/Repository_Recovery_Roadmap_v1_0.md => docs/roadmaps/[ACTIVE]_Repository_Recovery_Roadmap_v1.0.md
```

## 2. Totals

- Documents renamed: 55 (22 [ACTIVE], 22 [DRAFT], 10 [FROZEN], 1 [SUPERSEDED])
- SQL migrations renamed to bare NNN_description.sql: 20 (001–020)
- Total: 75. Errors: 0. All recorded by git as renames (R), preserving history.

## Critical Self-Review

Generated mechanically from git to avoid transcription error. Status tokens were derived from each document's own header per the Naming Standard §Status-Resolution; see the Engineering Decision Log and Exception Register for judgment calls and the 8 files deliberately left unchanged.

## Versioning & Placement

`[ACTIVE]_Repository_Rename_Mapping_Table_v1.0.md` → docs/project-history/. New file.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________

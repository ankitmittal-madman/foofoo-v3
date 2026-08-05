# Documentation Classification Register

**Status:** ACTIVE — repository documentation governance source of truth
**Version:** v1.1
**Date:** 2026-08-05
**Placement:** `docs/governance/`
**Supersedes:** v1.0 and the partial audit-only restructure from commit `8147d0a`

## Executive Summary

The repository was reassessed by purpose rather than filename, age, or implementation status. Product, architecture, algorithm, domain, API, database, security, deployment, ADR, engineering-standard, and knowledge-design material remains active. Fulfilled work packages, certificates, audits, execution logs, validation reports, completed recovery material, and superseded duplicates are archived.

Documents retained conservatively because their completion or continuing purpose is uncertain are listed in `docs/active/OPEN_ITEMS.md`.

## Classification counts

| Category | Meaning | Count |
|---|---|---:|
| A | Foundation documents kept active | 133 |
| B | Living operational documents kept active | 23 |
| C | Historical implementation documents archived | 200 |
| D | Superseded, duplicate, or obsolete documents archived | 22 |

## Method and scope

- Audited repository-authored Markdown, Markdown-named `.docx` text, true DOCX, HTML, the deferred-knowledge CSV register, READMEs, agent guidance, runbooks, and current quality-report documents.
- Excluded dependency-vendor documentation, generated cache metadata, lock files, raw data CSVs, JSON/XML machine evidence, screenshots, and log attachments from the document count. These were not discarded; dated report attachments moved with their reports.
- Preferred Category A/B whenever long-term purpose or completion state was uncertain.
- Did not change application behavior, algorithms, schemas, or architecture. Reference-only comments were rebased where they named moved evidence.

## Category A — Foundation documents kept active

- `.claude/skills/audit-api-contract/SKILL.md`
- `.claude/skills/audit-data-integrity/SKILL.md`
- `.claude/skills/audit-dependencies/SKILL.md`
- `.claude/skills/audit-dpdp/SKILL.md`
- `.claude/skills/audit-eas/SKILL.md`
- `.claude/skills/audit-edge-functions/SKILL.md`
- `.claude/skills/audit-onboarding-funnel/SKILL.md`
- `.claude/skills/audit-performance/SKILL.md`
- `.claude/skills/audit-prelaunch/SKILL.md`
- `.claude/skills/audit-rls/SKILL.md`
- `.claude/skills/audit-rollback-readiness/SKILL.md`
- `.claude/skills/coding-standards-enforcer/SKILL.md`
- `.claude/skills/debug-root-cause/SKILL.md`
- `.claude/skills/hygiene-dead-code/SKILL.md`
- `.claude/skills/hygiene-secrets/SKILL.md`
- `.claude/skills/hygiene-test-sync/SKILL.md`
- `.claude/skills/incident-postmortem/SKILL.md`
- `.claude/skills/install-logging-infrastructure/references/changelog-template.md`
- `.claude/skills/install-logging-infrastructure/references/structured-logger-template.md`
- `.claude/skills/install-logging-infrastructure/references/system-logger-template.md`
- `.claude/skills/install-logging-infrastructure/references/transaction-export-template.md`
- `.claude/skills/install-logging-infrastructure/references/user-journey-logger-template.md`
- `.claude/skills/install-logging-infrastructure/SKILL.md`
- `.claude/skills/session-knowledge-doc/references/session-block-template.md`
- `.claude/skills/session-knowledge-doc/references/shell-template.md`
- `.claude/skills/session-knowledge-doc/SKILL.md`
- `.claude/skills/session-resume/SKILL.md`
- `.claude/skills/session-resumption-protocol/SKILL.md`
- `CLAUDE.md`
- `data/source/README.md`
- `database/archive/re_engine_backup_20260803/README.md`
- `docs/architecture/[ACTIVE]_Canonical_Planning_Model_v1.0.md`
- `docs/architecture/[ACTIVE]_Canonical_Planning_Semantics_Architecture_v1.0.md`
- `docs/architecture/[ACTIVE]_Canonical_RE_Architecture_Final_Review_v1.0.md`
- `deliverables/FooFoo_Comprehensive_PRD_and_Bibles.md`
- `deliverables/FooFoo_Database_Architecture_Review_and_Target_Schema.md`
- `docs/architecture/[ACTIVE]_Food_Intelligence_and_Meal_Episode_Architecture_v2.0.md`
- `docs/architecture/[ACTIVE]_DOC-05_Information_Architecture_v1.2.docx`
- `docs/architecture/[ACTIVE]_DOC-06_UX_Design_System_v1.1.docx`
- `docs/architecture/[ACTIVE]_DOC-P3-02_Conceptual_Domain_Model_v1.1.md`
- `docs/architecture/[ACTIVE]_DOC-P3-03_Business_Logic_Specification_v1.0.md`
- `docs/architecture/[ACTIVE]_DOC-P3-03A_Logic_Governance_Matrix_v1.0.md`
- `docs/architecture/[ACTIVE]_DOC-P3-04_Data_Architecture_ERD_v1.3.md`
- `docs/architecture/[ACTIVE]_DOC-P3-05_Part_A_Readiness_Migration_Strategy_v1.2.md`
- `docs/architecture/[ACTIVE]_DOC-P3-06_API_Contract_Specification_v1.2.md`
- `docs/architecture/[ACTIVE]_DOC-P3-07_Security_Architecture_v1.2.md`
- `docs/architecture/[ACTIVE]_DOC-P3-08_Integration_and_Infrastructure_Architecture_v1.1.md`
- `docs/architecture/[ACTIVE]_DOC-P3-13_Main_Ingredient_Derivation_Heuristic_v1.0.md`
- `docs/architecture/[ACTIVE]_DOC-P4-00_Backend_Foundation_Architecture_v1.0.md`
- `docs/architecture/[ACTIVE]_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.1.md`
- `docs/architecture/[ACTIVE]_Phase1_Persona_Decomposition_Catalog_v1.0.md`
- `docs/architecture/[ACTIVE]_Phase1B_Attribute_to_Class_Rule_Extraction_v1.0.md`
- `docs/architecture/[ACTIVE]_RE-DOC-01_Architecture.docx`
- `docs/architecture/[ACTIVE]_RE-DOC-02_Four_Layers.docx`
- `docs/architecture/[ACTIVE]_RE-DOC-03_Class_Taxonomy_Scoring.docx`
- `docs/architecture/[ACTIVE]_RE-DOC-04_ColdStart_Variety_Suppression.docx`
- `docs/architecture/[DRAFT]_Cold_Start_Design_Specification_Swipe_Blend_v1.0.md`
- `docs/architecture/[DRAFT]_DOC-P4-03_Mobile_App_Architecture_Note_v1.0.md`
- `docs/architecture/ghar-re/Final_RE_-_Markdown_File.md`
- `docs/architecture/ghar-re/ghar_knowledge_base_v0_2.md`
- `docs/architecture/ghar-re/ghar_re_v1_0_core_spine_FROZEN.md`
- `docs/architecture/ghar-re/ghar_re_v1_0_derivation_D1_D7_FROZEN.md`
- `docs/architecture/ghar-re/ghar_re_v1_derivation_layer_reconciled.md`
- `docs/architecture/ghar-re/README.md`
- `docs/architecture/Ghar_RE_Project_Context_and_Mission_v1_0.md`
- `docs/architecture/RE-DOC-10_Ghar_RE_Production_Implementation_Plan_v1_0.md`
- `docs/architecture/RE-DOC-11_Ghar_RE_Extensibility_Review_v1_0.md`
- `docs/architecture/RE-DOC-13_Ghar_RE_Deployment_Topology_v1_0.md`
- `docs/architecture/schema_map_live_v1.0.html`
- `docs/governance/[ACTIVE]_AGR-005_routing_rules_nullable_show_key_v1.0.md`
- `docs/governance/[ACTIVE]_AGR-006_weight_ladder_numeric_conversion_v1.0.md`
- `docs/governance/[ACTIVE]_APDF_Framework_Base_v1.0.md`
- `docs/governance/[ACTIVE]_APDF_Framework_vNext_Addendum_v2.0.md`
- `docs/governance/[ACTIVE]_DOC-P3-05_Architecture_Gap_Register_v1.1.md`
- `docs/governance/[ACTIVE]_DOC-P3-09_Knowledge_Integration_Governance_v1.3.md`
- `docs/governance/[ACTIVE]_DOC-P3-10_Seed_Data_Integration_Framework_v1.1.md`
- `docs/governance/[ACTIVE]_DOC-P3-12_Governance_Improvement_Backlog_v1.4.md`
- `docs/governance/[ACTIVE]_Documentation_Classification_Register_v1.1.md`
- `docs/governance/[ACTIVE]_Founder_Decision_Register_v1.0.md`
- `docs/governance/[ACTIVE]_Founder_Ratification_Certificate_2026-07-16_v1.0.md`
- `docs/governance/[ACTIVE]_IDR-001_WP5_Sequence_Reconciliation_v1.0.md`
- `docs/governance/[ACTIVE]_Phase3_5_Architecture_Decision_Review_v1.0.md`
- `docs/governance/[ACTIVE]_Phase3_5_Architecture_Freeze_v1.0.md`
- `docs/governance/[ACTIVE]_PM-SUPP-02_Risk_Register_v1.0.docx`
- `docs/governance/[ACTIVE]_PM-SUPP-02_Risk_Register_v1.0.md`
- `docs/governance/[ACTIVE]_Project_Baseline_Register_v1.5.md`
- `docs/governance/[ACTIVE]_Repository_Naming_Correction_Addendum_v1.0.md`
- `docs/governance/[ACTIVE]_Repository_Naming_Engineering_Decision_Log_v1.0.md`
- `docs/governance/[ACTIVE]_Repository_Naming_Exception_Register_v1.0.md`
- `docs/governance/[ACTIVE]_Repository_Naming_Standard_v1.1.md`
- `docs/governance/[ACTIVE]_Rollback_Decision_Log_v1.0.md`
- `docs/governance/[ACTIVE]_SER-001_re_cohorts_city_tier_v1.0.md`
- `docs/governance/[ACTIVE]_SER-002_dish_ingredients_main_ingredient_flag_v1.0.md`
- `docs/governance/[ACTIVE]_SER-003_interaction_events_idempotency_key_v1.0.md`
- `docs/governance/[ACTIVE]_SER-004_household_members_conditions_vocabulary_v1.0.md`
- `docs/product/[ACTIVE]_DOC-01_Product_Brief_v1.1.docx`
- `docs/product/[ACTIVE]_DOC-02_Market_Research_v1.0.docx`
- `docs/product/[ACTIVE]_DOC-03_User_Personas_v1.0.docx`
- `docs/product/[ACTIVE]_DOC-07_GTM_v1.0.docx`
- `docs/product/[ACTIVE]_DOC-08_Revenue_v1.0.docx`
- `docs/product/[ACTIVE]_DOC-09_Legal_v1.0.docx`
- `docs/README.md`
- `docs/research/[ACTIVE]_Batch1_Architecture_Confirmation_Package_v1.1.md`
- `docs/research/[ACTIVE]_Batch1_Canonicalization_Package_v1.1.md`
- `docs/research/[ACTIVE]_Batch1_Discovery_Report_v1.1.md`
- `docs/research/[ACTIVE]_Batch1_GapAnalysis_Package_v1.1.md`
- `docs/research/[ACTIVE]_Batch1_Governance_Evaluation_Package_v1.0.md`
- `docs/research/[ACTIVE]_Batch1_Mapping_Package_v1.1.md`
- `docs/research/[ACTIVE]_Batch1_Resolution_Package_v1.1.md`
- `docs/research/[ACTIVE]_Batch2_Canonicalization_Package_v1.0.md`
- `docs/research/[ACTIVE]_Batch2_Discovery_Report_v1.1.md`
- `docs/research/[ACTIVE]_Batch2_GapAnalysis_Package_v1.0.md`
- `docs/research/[ACTIVE]_Batch2_Mapping_Package_v1.0.md`
- `docs/research/[ACTIVE]_Batch2_Resolution_Package_v1.0.md`
- `docs/research/[ACTIVE]_Batch3_Pipeline_Package_v1.0.md`
- `docs/research/[ACTIVE]_Batch4_Pipeline_Package_v1.0.md`
- `docs/research/[ACTIVE]_Batch4_Technical_Review_and_Freeze_Recommendation_v1.0.md`
- `docs/research/[ACTIVE]_Batch5_Pipeline_Package_v1.1.md`
- `docs/research/[ACTIVE]_Batch6_Pipeline_Package_v1.0.md`
- `docs/research/[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.20.md`
- `docs/research/[ACTIVE]_Phase3_5_Phase2_Knowledge_Acquisition_v1.2.md`
- `docs/visuals/[ACTIVE]_DOC-06_Visual_Design_System_Explorer_v1.0.html`
- `docs/visuals/[ACTIVE]_RE-Visual-01_Pipeline_Explorer.html`
- `docs/visuals/[ACTIVE]_RE-Visual-02_ColdStart_Scoring.html`
- `docs/visuals/[ACTIVE]_RE-Visual-03_Evolution_Map.html`
- `docs/visuals/[ACTIVE]_RE-Visual-04_Live_Engine_Architecture_and_Roadmap_v1.0.html`
- `docs/visuals/[ACTIVE]_RE-Visual-05_ClassFirst_vs_Live_Journey_v1.0.html`
- `ghar_re_core/README.md`
- `ghar_re_service/README.md`
- `ops/audits/audit-edge-functions/onboarding-orchestrator-decision-2026-07-30.md`
- `ops/quality/README.md`
- `README.md`
- `supabase/README.md`

## Category B — Living operational documents kept active

- `.claude/projects/-home-ankit-mittal-mds02-foofoo-v3/memory/MEMORY.md`
- `.claude/projects/-home-ankit-mittal-mds02-foofoo-v3/memory/quality-gate.md`
- `CHANGELOG.md`
- `docs/active/CURRENT_STATUS.md`
- `docs/active/LAUNCH_BLOCKERS.md`
- `docs/active/OPEN_ITEMS.md`
- `docs/active/ROADMAP.md`
- `docs/project-history/work-packages/[ACTIVE]_REPO-WP-04DA_Validation_Script_Corrections_v1.0.md`
- `docs/project-history/work-packages/[ACTIVE]_WP-6_Deferred_Knowledge_Register_v1.0.csv`
- `docs/project-history/work-packages/[DRAFT]_WP-12_Per_User_Recommendation_Decision_Trace_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-14_RE_Intelligence_Roadmap_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-18_Onboarding_Plan_Recipe_Flow_v1.0.md`
- `docs/project-history/work-packages/[DRAFT]_WP-22_Synthetic_Persona_UI_Journey_Reports_v1.0.md`
- `docs/roadmaps/[ACTIVE]_PM-SUPP-01_Roadmap_v1.0.docx`
- `docs/roadmaps/[ACTIVE]_PM-SUPP-01_Roadmap_v1.0.md`
- `docs/roadmaps/[ACTIVE]_RE-DOC-05_Evolution_Roadmap.docx`
- `KNOWLEDGE.html`
- `ops/audits/audit-dpdp/RUNBOOK_schedule-retention-jobs-2026-07-30.md`
- `ops/quality/reports/2026-08-04_023647/inventory/feature_matrix.md`
- `ops/quality/reports/2026-08-04_023647/inventory/inventory.md`
- `ops/quality/reports/2026-08-04_023647/summary.html`
- `ops/quality/reports/2026-08-04_023647/summary.md`
- `ops/quality/reports/2026-08-04_023647/summary.txt`

## Category C — Historical implementation documents archived

- `docs/archive/audits/ops/audit-api-contract/ARCHIVED_api-contract-audit-2026-07-30.md`
- `docs/archive/audits/ops/audit-data-integrity/ARCHIVED_data-integrity.md`
- `docs/archive/audits/ops/audit-dependencies/ARCHIVED_dependency-audit.md`
- `docs/archive/audits/ops/audit-dpdp/ARCHIVED_dpdp-compliance-report.md`
- `docs/archive/audits/ops/audit-eas/ARCHIVED_eas-presubmission.md`
- `docs/archive/audits/ops/audit-edge-functions/ARCHIVED_edge-function-audit.md`
- `docs/archive/audits/ops/audit-onboarding-funnel/ARCHIVED_onboarding-funnel-audit-2026-07-30.md`
- `docs/archive/audits/ops/audit-performance/ARCHIVED_performance-baseline-2026-07-30.md`
- `docs/archive/audits/ops/audit-prelaunch/ARCHIVED_prelaunch-checklist-2026-07-30.md`
- `docs/archive/audits/ops/audit-rls/ARCHIVED_rls-audit.md`
- `docs/archive/audits/ops/audit-rls/ARCHIVED_rls-fix-2026-07-30.md`
- `docs/archive/audits/ops/audit-rollback-readiness/ARCHIVED_rollback-readiness-2026-07-30.md`
- `docs/archive/audits/ops/hygiene-dead-code/ARCHIVED_dead-code-audit-2026-07-30.md`
- `docs/archive/audits/ops/hygiene-test-sync/ARCHIVED_test-sync-audit-2026-07-30.md`
- `docs/archive/audits/ops/install-logging-infrastructure/ARCHIVED_logging-compliance.md`
- `docs/archive/audits/ops/root-rls-audit/ARCHIVED_rls-audit.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_00_executive_summary.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_01_repository_inventory.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_02_system_topology.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_03_recommendation_engine_audit.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_04_food_knowledge_audit.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_05_database_audit.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_06_e2e_workflow_audit.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_07_security_audit.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_08_testing_audit.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_09_deployment_audit.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_10_production_readiness_scorecard.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_11_prioritized_backlog.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_12_recommended_build_sequence.md`
- `docs/archive/audits/re_audit_v2/ARCHIVED_README.md`
- `docs/archive/certificates/ARCHIVED_DOC-P3-05_Part_B_Completion_Summary_1_0.md`
- `docs/archive/certificates/ARCHIVED_DOC-P3-05_Part_C_Completion_Summary.md`
- `docs/archive/certificates/ARCHIVED_DOC-P3-05_Part_D_Completion_Summary.md`
- `docs/archive/certificates/ARCHIVED_DOC-P3-05_Regression_Validation_AGR002_003.md`
- `docs/archive/certificates/ARCHIVED_DOC-P3-08_Readiness_Report_v1.1.md`
- `docs/archive/certificates/ARCHIVED_P3-03_Context_Baseline_Readiness.md`
- `docs/archive/certificates/ARCHIVED_P3-03_Logic_Inventory_QualityGate.md`
- `docs/archive/certificates/ARCHIVED_REPO-BOOT-03_Repository_Migration_Certification_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-001_WP-5F_CleanRoom_Validation_Execution_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-002_WP-5E_Validation_Remediation_Execution_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-003_WP-5F2_CleanRoom_Execution_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-004_WP-5D_Production_Parity_Execution_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-005_WP-5D_Completion_Execution_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-006_Repository_Green_Certification_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-007_WP-6E_Data_Gate_Execution_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-008_WP-8B_Backend_Foundation_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-009_WP-6E2_Canonical_Production_Sync_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-010_WP-6E3_Security_Hardening_and_Validation_Modernization_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-011_WP-8C_Auth_and_Consent_Execution_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-012_WP-8C_Architectural_Reconciliation_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-013_WP-8D_Pre_Implementation_Reconciliation_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-014_WP-8D_Recommendation_Engine_Core_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-015_WP-8E_RE_Integration_Layer_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-016_WP-K01_Knowledge_Platform_Refactoring_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-018_WP-8F_Runtime_Mapping_Blocker_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-019_WP-8FA_CandidateRepository_Audit_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-020_WP-9_Due_Diligence_Audit_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-021_WP-10_Schema_Evolution_Batch_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-022_WP-11_CandidateRepository_Adapter_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-023_WP-12_Planning_Semantics_Architecture_Batch_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-024_WP-13_Household_Members_Conditions_Vocabulary_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-025_WP-17_Compositional_Cohort_Plan_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-026_WP-16_Cohort_Intelligence_Engine_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-027_WP-19_Dish_Ontology_Batch1_Deploy_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-028_WP-20_Partial_Cutover_Migration046_RLSFix_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-029_WP-20_Full_Cutover_Completion_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-030_WP-21_Ghar_Re_Schema_Retirement_v1.0.md`
- `docs/archive/certificates/ARCHIVED_REPO-CERT-031_WP-19_Dish_Ontology_Batches_2-22_Deploy_v1.0.md`
- `docs/archive/completed-phases/ARCHIVED_RE_Compliance_Review_2026-08-04_v1.0.md`
- `docs/archive/completed-phases/repository-recovery/ARCHIVED_Repository_Recovery_Backlog_v1.0.md`
- `docs/archive/completed-phases/repository-recovery/ARCHIVED_Repository_Recovery_Decision_Log_v1.0.md`
- `docs/archive/completed-phases/repository-recovery/ARCHIVED_Repository_Recovery_Risk_Register_v1.0.md`
- `docs/archive/completed-phases/repository-recovery/ARCHIVED_Repository_Recovery_Roadmap_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_Engineering_Execution_Baseline_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_Engineering_Launch_Plan_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_Final_Evidence_Closure_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_REPO-BOOT-01_Repository_Bootstrap_Execution_Package_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_REPO-BOOT-02_Repository_Bootstrap_Work_Package_and_AI_Collaboration_Model_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_REPO-WP-02_Schema_Baseline_Establishment_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_REPO-WP-03_Seed_Readiness_Engineering_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_REPO-WP-03_Seed_Readiness_Engineering_v1.1.md`
- `docs/archive/implementation/work-packages/ARCHIVED_REPO-WP-03D_Seed_Readiness_Certification_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_REPO-WP-04B_Seed_Loading_v1.1.md`
- `docs/archive/implementation/work-packages/ARCHIVED_REPO-WP-04DB_Validation_Execution_Certification_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_REPO-WP-04DC_RLS_Diagnostic_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_Repository_Recovery_Work_Package_Plan_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-10_FD12_FD11_FD13_Schema_Evolution_Batch_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-11_CandidateRepository_Adapter_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-11_Launch_Readiness_Remediation_Plan_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-12_Planning_Semantics_Architecture_Batch_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-13_Household_Members_Conditions_Vocabulary_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-15_Class_Enriched_Recommendation_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-16_Cohort_Intelligence_Engine_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-17_Compositional_Cohort_Plan_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-20_Retire_Legacy_re_engine_Schema_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-21_Production_Hardening_Audit_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-5D_Production_Parity_Completion_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-5D_Production_Parity_Recovery_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-5E_Validation_Remediation_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-5F2_CleanRoom_Execution_Validation_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-5F_CleanRoom_Repository_Validation_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-5G_Repository_Green_Certification_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-6_Canonical_Knowledge_Engineering_Plan_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-6A-6D_Knowledge_Mapping_and_Seed_Pipeline_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-6D-gen_Canonical_Seed_Engineering_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-6E_Staging_Data_Gate_Execution_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-6RE_Recommendation_Engine_Knowledge_Audit_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-8B_Backend_Foundation_Scaffold_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-8C_Auth_Framework_and_Consent_Endpoint_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-8D_Recommendation_Engine_Core_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-8E_RE_Integration_Layer_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-8F_Runtime_Adapters_Blocker_Report_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-8FA_CandidateRepository_Architecture_Audit_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-8G_Recommendation_Variety_on_Refresh_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-9_Independent_Engineering_Due_Diligence_Audit_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-9_Validation_Audit_v1.0.md`
- `docs/archive/implementation/work-packages/ARCHIVED_WP-K01_Knowledge_Platform_Refactoring_v1.0.md`
- `docs/archive/reports/architecture/ARCHIVED_RE-DOC-12_Ghar_RE_Status_and_Roadmap_v1_0.md`
- `docs/archive/reports/governance/ARCHIVED_Repository_Naming_Conflict_Report_v1.0.md`
- `docs/archive/reports/incidents/ARCHIVED_debug-log.md`
- `docs/archive/reports/project-history/ARCHIVED_CleanRoom_Validation_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Engineering_Handover_Project_Continuity_Package_v1.3.md`
- `docs/archive/reports/project-history/ARCHIVED_Migration_Recovery_Decision_Log_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Migration_Recovery_Evidence_Register_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Migration_Recovery_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Migration_Recovery_Validation_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Repository_Completeness_Audit_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Repository_Naming_Validation_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Repository_Normalization_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Repository_Rename_Mapping_Table_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Rollback_Confidence_Matrix_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Rollback_Dependency_Graph_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Rollback_Evidence_Register_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_Rollback_Validation_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_SESSION_HANDOFF-4.md`
- `docs/archive/reports/project-history/ARCHIVED_SESSION_HANDOFF_v1_0-1.docx`
- `docs/archive/reports/project-history/ARCHIVED_WP-5C_Rollback_Recovery_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5D_Engineering_Decision_Log_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5D_Evidence_Register_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5D_Production_Parity_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5D_Validation_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5E_Engineering_Decision_Log_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5E_Evidence_Register_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5E_Validation_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5F2_Decision_Log_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5F2_Evidence_Register_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5F2_Execution_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-5F2_Validation_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-8C_Architectural_Reconciliation_Report_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-8D_Pre_Implementation_Architecture_Reconciliation_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-K01_Decision_Log_v1.0.md`
- `docs/archive/reports/project-history/ARCHIVED_WP-K01_Repository_Impact_Report_v1.0.md`
- `docs/archive/reports/quality/2026-08-03_062119/ARCHIVED_summary.html`
- `docs/archive/reports/quality/2026-08-03_062119/ARCHIVED_summary.md`
- `docs/archive/reports/quality/2026-08-03_062119/ARCHIVED_summary.txt`
- `docs/archive/reports/quality/2026-08-03_062119/inventory/ARCHIVED_feature_matrix.md`
- `docs/archive/reports/quality/2026-08-03_062119/inventory/ARCHIVED_inventory.md`
- `docs/archive/reports/quality/2026-08-03_085525/ARCHIVED_summary.html`
- `docs/archive/reports/quality/2026-08-03_085525/ARCHIVED_summary.md`
- `docs/archive/reports/quality/2026-08-03_085525/ARCHIVED_summary.txt`
- `docs/archive/reports/quality/2026-08-03_085525/inventory/ARCHIVED_feature_matrix.md`
- `docs/archive/reports/quality/2026-08-03_085525/inventory/ARCHIVED_inventory.md`
- `docs/archive/reports/quality/2026-08-03_105158/ARCHIVED_summary.html`
- `docs/archive/reports/quality/2026-08-03_105158/ARCHIVED_summary.md`
- `docs/archive/reports/quality/2026-08-03_105158/ARCHIVED_summary.txt`
- `docs/archive/reports/quality/2026-08-03_105158/inventory/ARCHIVED_feature_matrix.md`
- `docs/archive/reports/quality/2026-08-03_105158/inventory/ARCHIVED_inventory.md`
- `docs/archive/reports/quality/2026-08-03_105332/ARCHIVED_summary.html`
- `docs/archive/reports/quality/2026-08-03_105332/ARCHIVED_summary.md`
- `docs/archive/reports/quality/2026-08-03_105332/ARCHIVED_summary.txt`
- `docs/archive/reports/quality/2026-08-03_105332/inventory/ARCHIVED_feature_matrix.md`
- `docs/archive/reports/quality/2026-08-03_105332/inventory/ARCHIVED_inventory.md`
- `docs/archive/reports/quality/2026-08-03_110648/inventory/ARCHIVED_feature_matrix.md`
- `docs/archive/reports/quality/2026-08-03_110648/inventory/ARCHIVED_inventory.md`
- `docs/archive/reports/quality/2026-08-03_110919/ARCHIVED_summary.html`
- `docs/archive/reports/quality/2026-08-03_110919/ARCHIVED_summary.md`
- `docs/archive/reports/quality/2026-08-03_110919/ARCHIVED_summary.txt`
- `docs/archive/reports/quality/2026-08-03_110919/inventory/ARCHIVED_feature_matrix.md`
- `docs/archive/reports/quality/2026-08-03_110919/inventory/ARCHIVED_inventory.md`
- `docs/archive/reports/quality/2026-08-04_022436/ARCHIVED_summary.html`
- `docs/archive/reports/quality/2026-08-04_022436/ARCHIVED_summary.md`
- `docs/archive/reports/quality/2026-08-04_022436/ARCHIVED_summary.txt`
- `docs/archive/reports/quality/2026-08-04_022436/inventory/ARCHIVED_feature_matrix.md`
- `docs/archive/reports/quality/2026-08-04_022436/inventory/ARCHIVED_inventory.md`
- `docs/archive/reports/quality/2026-08-04_023220/ARCHIVED_summary.html`
- `docs/archive/reports/quality/2026-08-04_023220/ARCHIVED_summary.md`
- `docs/archive/reports/quality/2026-08-04_023220/ARCHIVED_summary.txt`
- `docs/archive/reports/quality/2026-08-04_023220/inventory/ARCHIVED_feature_matrix.md`
- `docs/archive/reports/quality/2026-08-04_023220/inventory/ARCHIVED_inventory.md`
- `docs/archive/reports/quality/2026-08-04_023519/ARCHIVED_summary.html`
- `docs/archive/reports/quality/2026-08-04_023519/ARCHIVED_summary.md`
- `docs/archive/reports/quality/2026-08-04_023519/ARCHIVED_summary.txt`
- `docs/archive/reports/quality/2026-08-04_023519/inventory/ARCHIVED_feature_matrix.md`
- `docs/archive/reports/quality/2026-08-04_023519/inventory/ARCHIVED_inventory.md`
- `docs/archive/reports/research/ARCHIVED_Phase3_5_Project_Integration_Review_v1.0.md`
- `docs/archive/reports/research/ARCHIVED_Project_Checkpoint_v1_0.md`
- `docs/archive/reports/session-logs/ARCHIVED_test_10.md`
- `docs/archive/reports/session-logs/ARCHIVED_test_13.md`
- `docs/archive/reports/session-logs/ARCHIVED_test_14.md`
- `docs/archive/reports/session-logs/ARCHIVED_test_17.md`

## Category D — Superseded, duplicate, or obsolete documents archived

- `docs/archive/historical/architecture/ARCHIVED_DOC-04_PRD_v1.1.docx`
- `docs/archive/historical/architecture/ARCHIVED_DOC-10_Technical_Architecture_v1.0.docx`
- `docs/archive/historical/architecture/ARCHIVED_Food_Ontology_and_Meal_Taxonomy_Architecture_v1.0.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_01_requirement_traceability.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_02_algorithm_coverage.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_03_meal_genome_audit.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_04_food_ontology_audit.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_05_knowledge_base_audit.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_06_seed_data_audit.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_07_database_audit.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_08_synergy_matrix.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_09_missing_implementation_algorithm_delta.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_10_remaining_work.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_11_production_readiness.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_12_final_verdict.md`
- `docs/archive/audits/re_audit_archive/ARCHIVED_README.md`
- `docs/archive/historical/architecture/ARCHIVED_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.0.md`
- `docs/archive/historical/architecture/ARCHIVED_Ghar_RE_Project_Context_and_Mission_v1_0.md`
- `docs/archive/historical/governance/ARCHIVED_Founder_Decision_Book_v1.0.md`
- `docs/archive/historical/governance/ARCHIVED_Project_Baseline_Register_v1.1.docx`
- `docs/archive/historical/governance/ARCHIVED_Repository_Naming_Standard_v1.0.md`
- `docs/archive/historical/roadmaps/ARCHIVED_FooFoo_Project_Roadmap_v1.1.md`

## References updated

- `CLAUDE.md`: archive hierarchy, authoritative naming standard, repository-history provenance, and certificate lifecycle paths.
- `KNOWLEDGE.html`: encoded and plain certificate links rebased to `docs/archive/certificates/`.
- Active architecture, governance, and research documents: authoritative naming-standard references moved from v1.0 to v1.1; historical evidence paths rebased.
- Repository agent skills: new incident/debug output remains active under `logs/hygiene-reports/` instead of appending into an archive.
- Recommendation-engine comments and docstrings: stale `reports/re_audit/` citations rebased to preserved audit evidence.
- Archived documents: cross-references to moved records rebased without changing their historical findings.
- `docs/README.md`: replaced the stale bootstrap-era landing page with the complete current hierarchy.

## Broken links fixed

- Certificate links in `KNOWLEDGE.html` that still targeted the removed `docs/project-history/certificates/` tree.
- Stale `docs/README.md` links to completed work packages and certificates.
- `CLAUDE.md` references to the archived naming-standard version and removed certificate folder.
- Debug-root-cause guidance that would have appended new operational records to an archived log.
- Audit citations that still targeted the removed `reports/re_audit/` tree.

## New hierarchy

```text
docs/
├── active/                 # current status, open items, blockers, roadmap
├── product/                # product foundation
├── architecture/           # architecture, algorithms, API, DB, RE design
├── governance/             # standing rules, ADRs, living registers
├── research/               # durable food/knowledge discovery and mappings
├── roadmaps/               # durable product and RE evolution roadmaps
├── visuals/                # active explanatory references
├── project-history/
│   └── work-packages/      # unresolved/current work only
└── archive/
    ├── audits/
    ├── certificates/
    ├── completed-phases/
    ├── historical/
    ├── implementation/
    └── reports/
```

## Review flags

- Six specific work documents and one SQL reference remain under `docs/project-history/work-packages/`; the six documents are explicitly tracked in `docs/active/OPEN_ITEMS.md`.
- The active product and several architecture sources use a `.docx` extension while containing Markdown text. They remain foundational and were not renamed because format normalization is distinct from lifecycle classification.
- The current dated quality report remains active operational evidence; older dated runs are archived.

## Critical Self-Review

- No product, mathematical, algorithm, architecture, domain-model, database-design, API-contract, security, deployment-topology, ADR, food-knowledge, or engineering-standard source was archived solely because implementation completed.
- Completed certificates and execution reports remain available as evidence, but active navigation does not present them as current implementation guidance.
- Historical machine evidence was preserved without injecting prose into JSON, XML, screenshots, or other formats whose validity would be damaged.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________

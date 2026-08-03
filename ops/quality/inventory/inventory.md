# Repository Inventory (Phase 1)

_Generated 2026-08-03T06:04:43.638640+00:00 · git `1860c9e`_

**62 components discovered.**

## By kind

| kind | count |
| --- | --- |
| api-contract | 1 |
| ci-workflow | 5 |
| edge-function | 8 |
| http-endpoint | 9 |
| mobile-api-client | 7 |
| mobile-screen | 13 |
| python-package | 1 |
| python-service | 1 |
| sql-migration | 2 |
| sql-rollback | 1 |
| sql-seed | 1 |
| sql-validation | 1 |
| test-suite | 12 |


## Components

| name | kind | path | detail | files |
| --- | --- | --- | --- | --- |
| ghar_re_core | python-package | ghar_re_core | Recommendation-engine math (frozen reference impl) | 22 |
| ghar_re_service | python-service | ghar_re_service | FastAPI production service hosting the RE | 25 |
| GET /healthz | http-endpoint | ghar_re_service/ghar_re_service/main.py | FastAPI route on the RE service | 0 |
| GET /readyz | http-endpoint | ghar_re_service/ghar_re_service/main.py | FastAPI route on the RE service | 0 |
| GET /v1/meta | http-endpoint | ghar_re_service/ghar_re_service/main.py | FastAPI route on the RE service | 0 |
| POST /v1/recommendations | http-endpoint | ghar_re_service/ghar_re_service/main.py | FastAPI route on the RE service | 0 |
| POST /v1/cold-start | http-endpoint | ghar_re_service/ghar_re_service/main.py | FastAPI route on the RE service | 0 |
| POST /v1/meal-plan | http-endpoint | ghar_re_service/ghar_re_service/main.py | FastAPI route on the RE service | 0 |
| POST /v1/weekly-plan | http-endpoint | ghar_re_service/ghar_re_service/main.py | FastAPI route on the RE service | 0 |
| POST /v1/class-dishes | http-endpoint | ghar_re_service/ghar_re_service/main.py | FastAPI route on the RE service | 0 |
| POST /v1/recipe | http-endpoint | ghar_re_service/ghar_re_service/main.py | FastAPI route on the RE service | 0 |
| consent | edge-function | supabase/functions/consent | Supabase/Deno edge function | 2 |
| cron-hard-delete | edge-function | supabase/functions/cron-hard-delete | Supabase/Deno edge function | 1 |
| cron-retention-purge | edge-function | supabase/functions/cron-retention-purge | Supabase/Deno edge function | 1 |
| feedback | edge-function | supabase/functions/feedback | Supabase/Deno edge function | 3 |
| household | edge-function | supabase/functions/household | Supabase/Deno edge function | 4 |
| recommendations | edge-function | supabase/functions/recommendations | Supabase/Deno edge function | 9 |
| user-delete | edge-function | supabase/functions/user-delete | Supabase/Deno edge function | 4 |
| user-export | edge-function | supabase/functions/user-export | Supabase/Deno edge function | 3 |
| mobile/app/(auth)/sign-in.tsx | mobile-screen | mobile/app/(auth)/sign-in.tsx | Expo Router screen | 0 |
| mobile/app/(onboarding)/_layout.tsx | mobile-screen | mobile/app/(onboarding)/_layout.tsx | Expo Router screen | 0 |
| mobile/app/(onboarding)/consent.tsx | mobile-screen | mobile/app/(onboarding)/consent.tsx | Expo Router screen | 0 |
| mobile/app/(onboarding)/step-1.tsx | mobile-screen | mobile/app/(onboarding)/step-1.tsx | Expo Router screen | 0 |
| mobile/app/(onboarding)/step-2.tsx | mobile-screen | mobile/app/(onboarding)/step-2.tsx | Expo Router screen | 0 |
| mobile/app/(onboarding)/step-3.tsx | mobile-screen | mobile/app/(onboarding)/step-3.tsx | Expo Router screen | 0 |
| mobile/app/(onboarding)/step-4.tsx | mobile-screen | mobile/app/(onboarding)/step-4.tsx | Expo Router screen | 0 |
| mobile/app/(onboarding)/step-5.tsx | mobile-screen | mobile/app/(onboarding)/step-5.tsx | Expo Router screen | 0 |
| mobile/app/_layout.tsx | mobile-screen | mobile/app/_layout.tsx | Expo Router screen | 0 |
| mobile/app/create-id.tsx | mobile-screen | mobile/app/create-id.tsx | Expo Router screen | 0 |
| mobile/app/index.tsx | mobile-screen | mobile/app/index.tsx | Expo Router screen | 0 |
| mobile/app/recommendations.tsx | mobile-screen | mobile/app/recommendations.tsx | Expo Router screen | 0 |
| mobile/app/splash-2.tsx | mobile-screen | mobile/app/splash-2.tsx | Expo Router screen | 0 |
| mobile/src/api/client.ts | mobile-api-client | mobile/src/api/client.ts | Mobile API client | 0 |
| mobile/src/api/consent.ts | mobile-api-client | mobile/src/api/consent.ts | Mobile API client | 0 |
| mobile/src/api/errorMessages.ts | mobile-api-client | mobile/src/api/errorMessages.ts | Mobile API client | 0 |
| mobile/src/api/feedback.ts | mobile-api-client | mobile/src/api/feedback.ts | Mobile API client | 0 |
| mobile/src/api/household.ts | mobile-api-client | mobile/src/api/household.ts | Mobile API client | 0 |
| mobile/src/api/recommendations.ts | mobile-api-client | mobile/src/api/recommendations.ts | Mobile API client | 0 |
| mobile/src/api/types.ts | mobile-api-client | mobile/src/api/types.ts | Mobile API client | 0 |
| database/migrations | sql-migration | database/migrations | 44 SQL files | 44 |
| database/rollback | sql-rollback | database/rollback | 64 SQL files | 64 |
| database/seeds | sql-seed | database/seeds | 20 SQL files | 20 |
| database/validation | sql-validation | database/validation | 8 SQL files | 8 |
| supabase/migrations | sql-migration | supabase/migrations | 1 SQL files | 1 |
| contracts/ghar-re-v1.schema.json | api-contract | contracts/ghar-re-v1.schema.json | JSON Schema contract | 0 |
| ghar_re_core/tests/test_golden_master.py | test-suite | ghar_re_core/tests/test_golden_master.py | Existing automated tests | 0 |
| ghar_re_core/tests/test_cohort_intel.py | test-suite | ghar_re_core/tests/test_cohort_intel.py | Existing automated tests | 0 |
| ghar_re_core/tests/test_pipeline.py | test-suite | ghar_re_core/tests/test_pipeline.py | Existing automated tests | 0 |
| ghar_re_core/tests/test_meal_planner.py | test-suite | ghar_re_core/tests/test_meal_planner.py | Existing automated tests | 0 |
| ghar_re_core/tests/test_class_first_cohort.py | test-suite | ghar_re_core/tests/test_class_first_cohort.py | Existing automated tests | 0 |
| ghar_re_core/tests/test_cohort_plan.py | test-suite | ghar_re_core/tests/test_cohort_plan.py | Existing automated tests | 0 |
| ghar_re_service/tests/test_service.py | test-suite | ghar_re_service/tests/test_service.py | Existing automated tests | 0 |
| ghar_re_service/tests/test_bundle.py | test-suite | ghar_re_service/tests/test_bundle.py | Existing automated tests | 0 |
| ghar_re_service/tests/test_auth.py | test-suite | ghar_re_service/tests/test_auth.py | Existing automated tests | 0 |
| ghar_re_service/tests/test_contract.py | test-suite | ghar_re_service/tests/test_contract.py | Existing automated tests | 0 |
| ghar_re_service/tests/test_ratelimit.py | test-suite | ghar_re_service/tests/test_ratelimit.py | Existing automated tests | 0 |
| ghar_re_service/tests/test_planning.py | test-suite | ghar_re_service/tests/test_planning.py | Existing automated tests | 0 |
| .github/workflows/backend-ci.yml | ci-workflow | .github/workflows/backend-ci.yml | GitHub Actions workflow | 0 |
| .github/workflows/drive-backup.yml | ci-workflow | .github/workflows/drive-backup.yml | GitHub Actions workflow | 0 |
| .github/workflows/fly_deploy.yml | ci-workflow | .github/workflows/fly_deploy.yml | GitHub Actions workflow | 0 |
| .github/workflows/mirror.yml | ci-workflow | .github/workflows/mirror.yml | GitHub Actions workflow | 0 |
| .github/workflows/re-ci.yml | ci-workflow | .github/workflows/re-ci.yml | GitHub Actions workflow | 0 |

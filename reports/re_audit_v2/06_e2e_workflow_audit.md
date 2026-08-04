# End-to-End Workflow Audit (fresh, 2026-08-04)

| # | Journey | Status | Key evidence |
|---|---|---|---|
| 1 | Signup/login | Working | Real Supabase Auth (JWT), single source-of-truth routing gate (`fetchOnboardingStatus`), handles unconfirmed-email case |
| 2 | Household creation/onboarding | Working | Full chain traced mobile→Edge Function→DB; atomic profile creation (`ON CONFLICT DO NOTHING`), `onboarding_completed` correctly set at profile-creation time |
| 3 | Recommendation generation | Working (pipeline), but **the screen calling it directly is dead code** | `recommendations.tsx`'s own header comment: "no route in the app links here anymore." Actively-routed home flow uses a different `/v1/plan`-family surface. |
| 4 | Recommendation explanation | **Missing** | `contributions`/`decision_trace` flow fully into the API response and get persisted server-side; zero mobile screens read or render either field |
| 5 | Feedback capture | Working, but narrow reach | Backend solid (feedback_events writes with dish resolution); only reachable from the dead `recommendations.tsx` screen and a single like-only tap on the calibration screen — the daily-use screens (`today.tsx`, `recipe/[dish].tsx`) have no feedback UI at all |
| 6 | History/past plans | **Missing** | No GET endpoint exists for any household state; the only "history" is a device-local AsyncStorage cache, explicitly documented in its own code as "no backend table exists yet" |
| 7 | Profile update/preferences editing | **Missing** | No route exists (`profile`/`settings` search returned nothing); household endpoint is create-once, never revisited after onboarding |
| 8 | Cold-start/calibration screen | Working | Fully wired, actively routed immediately post-onboarding, graceful skip path |

## The structural problem this surfaces
Journeys 3 and 5 reveal that the mobile app has **two parallel recommendation surfaces**: an older
one (`/v1/recommendations` + `recommendations.tsx`, with contributions/feedback UI) that is now
dead code, and a newer one (`/v1/plan` family + `today.tsx`/`weekly-plan.tsx`) that is actively
routed but has **no feedback or explanation UI at all**. The newer surface inherited the backend
sophistication (contributions, decision trace, feedback recording) without inheriting the UI that
exposed it. This is not two separate small gaps — it's one migration that stopped halfway.
</content>

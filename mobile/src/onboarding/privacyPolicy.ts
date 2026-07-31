/**
 * Shared with app/(onboarding)/consent.tsx and app/(onboarding)/step-5.tsx (the capture screen
 * and the deferred-dispatch call site respectively — see consent.tsx's header comment for why
 * the two are split). Kept out of the route file so both can import it without importing runtime
 * code from an Expo Router screen module.
 *
 * No dedicated "current privacy policy version" source exists yet in this repo (no
 * docs/governance/legal doc found). "2026-07-01" matches the fixture value already used by the
 * backend's own consent tests (supabase/functions/_tests/consent.test.ts) as the
 * least-arbitrary placeholder available — flagged for Founder/legal confirmation of the real value.
 */
export const PRIVACY_POLICY_VERSION = "2026-07-01";

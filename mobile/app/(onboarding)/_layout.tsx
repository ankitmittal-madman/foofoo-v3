import { Redirect, Stack, usePathname } from "expo-router";
import { useSession } from "@/auth/SessionContext";
import { OnboardingProvider, earliestIncompleteStep, useOnboarding } from "@/onboarding/OnboardingContext";
import { useTheme } from "@/theme";

/**
 * OnboardingLayout — the expo-router group layout wrapping all five onboarding step screens
 * (step-1..step-5). Renders nothing while the session is still loading, bounces a signed-out
 * user to sign-in, and otherwise wraps the steps in OnboardingProvider so every step screen can
 * read/write the same in-memory `answers` bag via useOnboarding(). Its Stack has no header of
 * its own — each step screen supplies its own StepHeader progress bar instead.
 */
export default function OnboardingLayout() {
  const { session, loading } = useSession();
  const t = useTheme();
  if (loading) return null;
  if (!session) return <Redirect href="/(auth)/sign-in" />;
  return (
    <OnboardingProvider userId={session.user.id}>
      <StepGuard>
        <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: t.colors.background } }} />
      </StepGuard>
    </OnboardingProvider>
  );
}

/**
 * StepGuard — redirects a step-N route (N=2..5) back to the earliest step whose required
 * answers are actually missing, once persisted progress has been restored. Without this, a deep
 * link or hard refresh landing directly on e.g. step-5 rendered that screen immediately; each
 * step only validates its OWN required field, so steps 1-4's requirements went unchecked until
 * step 5's submit failed against the backend with an opaque "required details missing" error.
 * consent.tsx and step-1 (nothing earlier to be missing) are left alone.
 */
function StepGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { answers, restored } = useOnboarding();
  const match = /\/step-(\d)$/.exec(pathname);
  const routeStep = match ? Number(match[1]) : null;

  if (restored && routeStep !== null && routeStep > 1) {
    const target = earliestIncompleteStep(answers);
    if (target !== null && target < routeStep) {
      return <Redirect href={`/(onboarding)/step-${target}`} />;
    }
  }
  return <>{children}</>;
}

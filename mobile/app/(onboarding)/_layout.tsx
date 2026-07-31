import { Redirect, Stack } from "expo-router";
import { useSession } from "@/auth/SessionContext";
import { OnboardingProvider } from "@/onboarding/OnboardingContext";
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
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: t.colors.background } }} />
    </OnboardingProvider>
  );
}

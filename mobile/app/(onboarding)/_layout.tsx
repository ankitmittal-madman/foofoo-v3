import { Redirect, Stack } from "expo-router";
import { useSession } from "@/auth/SessionContext";
import { OnboardingProvider } from "@/onboarding/OnboardingContext";
import { useTheme } from "@/theme";

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

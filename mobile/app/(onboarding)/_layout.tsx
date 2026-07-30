import { Redirect, Stack } from "expo-router";
import { useSession } from "@/auth/SessionContext";

export default function OnboardingLayout() {
  const { session, loading } = useSession();
  if (loading) return null;
  if (!session) return <Redirect href="/(auth)/sign-in" />;
  return <Stack screenOptions={{ headerShown: false }} />;
}

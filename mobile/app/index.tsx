import { Redirect } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { useSession } from "@/auth/SessionContext";
import { fetchOnboardingStatus } from "@/api/household";
import { ActivityIndicator, View } from "react-native";

/**
 * Root gate. Fix (audit-onboarding-funnel HIGH finding): this used to unconditionally send every
 * signed-in user back to /(onboarding)/step-1 ("no onboarding-complete flag to branch on yet" —
 * its own prior comment), while sign-in.tsx's explicit sign-in action routed straight to
 * /recommendations — two different, contradictory rules for the same "already has a session"
 * state. Both now share one source of truth: household.ts's fetchOnboardingStatus() (see its
 * header comment for what "complete" means and why this is a safe, non-mutating call).
 */
export default function Index() {
  const { session, loading } = useSession();

  const statusQuery = useQuery({
    queryKey: ["onboarding-status"],
    queryFn: fetchOnboardingStatus,
    enabled: !!session && !loading,
    retry: false,
  });

  if (loading || (!!session && statusQuery.isPending)) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator />
      </View>
    );
  }

  if (!session) return <Redirect href="/splash-2" />;

  const complete = statusQuery.data?.complete === true;
  return <Redirect href={complete ? "/recommendations" : "/(onboarding)/consent"} />;
}

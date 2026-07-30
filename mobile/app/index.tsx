import { Redirect } from "expo-router";
import { useSession } from "@/auth/SessionContext";
import { ActivityIndicator, View } from "react-native";

export default function Index() {
  const { session, loading } = useSession();

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator />
      </View>
    );
  }

  if (!session) return <Redirect href="/splash-2" />;

  // Phase 1 always routes a signed-in user back into onboarding's first screen; it is idempotent
  // (household/handler.ts never re-creates an existing profile) so re-visiting is safe, and Phase 1
  // has no "onboarding complete" flag to branch on yet.
  return <Redirect href="/(onboarding)/step-1" />;
}

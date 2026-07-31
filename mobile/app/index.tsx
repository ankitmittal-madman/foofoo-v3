import { Redirect } from "expo-router";
import { useSession } from "@/auth/SessionContext";
import { ActivityIndicator, View } from "react-native";

/**
 * Index — the app's entry route (`/`). Renders nothing but a spinner while the Supabase
 * session is still loading, then redirects: signed-out users go to the marketing splash
 * screen, signed-in users go straight back into onboarding's step 1 (see the inline note
 * below for why that's always the destination in Phase 1, regardless of prior progress).
 */
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

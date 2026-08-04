import { useState } from "react";
import { View, Text, ScrollView, ActivityIndicator, Pressable, StyleSheet } from "react-native";
import { useMutation, useQuery } from "@tanstack/react-query";
import { router, Redirect } from "expo-router";
import { postRecommendations } from "@/api/recommendations";
import { postFeedback } from "@/api/feedback";
import { fetchOnboardingStatus } from "@/api/household";
import { describeApiError } from "@/api/errorMessages";
import type { FeedbackEventType, Plate, RecommendationsResponse } from "@/api/types";

/**
 * ORPHANED as of the tabs/home restructuring: no route in the app links here anymore (index.tsx
 * and sign-in.tsx now redirect to "/today" — the (tabs) Home tab's today's-meal-selection screen —
 * instead of here). Left in place unrouted rather than deleted: its feedback-capture UI
 * (like/dislike/accept -> POST /v1/feedback, see PlateCard below) is real, working logic that
 * nothing else in the app currently duplicates, and no other screen was confirmed to have fully
 * absorbed it, so removing the file outright risked silently losing that capability rather than
 * just its route. If a future pass confirms feedback capture has a home elsewhere (e.g. wired into
 * the Home tab's dish cards), this file can be deleted then.
 *
 * Phase 1: proves the wire, not the UI (task instruction §4) — plain list rendering of whatever
 * `plates[]` the RE returns, no photos/cards/swipe. recommendations/handler.ts always returns a
 * valid 200 (RE failure -> fallback plate), so this screen has no "recommendation failed" case to
 * design for; only the network/auth failure path needs an error state.
 *
 * Completeness guard (audit-onboarding-funnel HIGH finding): this screen previously had none —
 * a user with an incomplete profile (e.g. reached via a stale deep link) would silently get a
 * generic fallback plate forever. Now shares the same source of truth as index.tsx/sign-in.tsx
 * (household.ts's fetchOnboardingStatus) and redirects into onboarding if incomplete, before
 * spending a recommendations call on a profile that can't yet produce a real one.
 */
export default function Recommendations() {
  const statusQuery = useQuery({
    queryKey: ["onboarding-status"],
    queryFn: fetchOnboardingStatus,
    retry: false,
  });

  const recsQuery = useQuery<RecommendationsResponse>({
    queryKey: ["recommendations"],
    queryFn: () => postRecommendations(),
    // Don't spend a recommendations call until we know the profile is complete enough to serve one.
    enabled: statusQuery.data?.complete === true,
  });

  if (statusQuery.isPending) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  if (statusQuery.isError) {
    // Can't verify completeness (e.g. offline) — don't guess either way; offer retry rather than
    // silently redirecting into onboarding (which could interrupt someone who is, in fact, done).
    return (
      <View style={styles.center}>
        <Text style={styles.error}>{describeApiError(statusQuery.error)}</Text>
        <Pressable style={styles.button} onPress={() => statusQuery.refetch()}>
          <Text style={styles.buttonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  if (statusQuery.data?.complete !== true) {
    return <Redirect href="/(onboarding)/consent" />;
  }

  if (recsQuery.isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  if (recsQuery.isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>{describeApiError(recsQuery.error)}</Text>
        <Pressable style={styles.button} onPress={() => recsQuery.refetch()}>
          <Text style={styles.buttonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  const data = recsQuery.data;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.header}>Your plates</Text>
      {data?.warnings?.length ? (
        <Text style={styles.warning}>{data.warnings.join(" · ")}</Text>
      ) : null}
      {data?.plates.map((plate: Plate) => (
        <PlateCard key={plate.plate_id} plate={plate} requestId={data.request_id} />
      ))}
      <Pressable style={styles.button} onPress={() => recsQuery.refetch()} disabled={recsQuery.isRefetching}>
        <Text style={styles.buttonText}>{recsQuery.isRefetching ? "Refreshing..." : "Refresh"}</Text>
      </Pressable>
      {/* WP-18: the new onboarding->plan flow (cold-start -> weekly-plan -> daily-plan -> recipe) */}
      <Pressable style={styles.secondaryButton} onPress={() => router.push("/cold-start")}>
        <Text style={styles.secondaryButtonText}>Try the new weekly plan</Text>
      </Pressable>
      <Pressable style={styles.secondaryButton} onPress={() => router.replace("/(onboarding)/consent")}>
        <Text style={styles.secondaryButtonText}>Back to onboarding</Text>
      </Pressable>
    </ScrollView>
  );
}

/**
 * PlateCard — one recommended meal in the plates list, showing its dish name(s), any
 * supporting side, a debug-style meta line (form + final score) useful while Phase 1 is proving
 * the recommendation wire rather than a polished dish presentation, and (WP-15) three feedback
 * buttons that record what the user actually did with this plate via POST /v1/feedback.
 *
 * This is the mobile half of WP-15's feedback-capture instrumentation: `feedback_events` has
 * existed since migration 038 but had no writer and no UI until now. Recording a reaction here
 * has no effect on scoring yet (the Core Spine's `w_pref·S_pref` term stays pinned to 0 in v1) —
 * this only starts building the history a future version could learn from.
 * @param plate - one plate object from the recommendations API response.
 * @param requestId - RecommendationsResponse.request_id, the only identifier the backend can
 *                    resolve back to this specific recommendation (see api/feedback.ts).
 */
function PlateCard({ plate, requestId }: { plate: Plate; requestId?: string }) {
  const [sent, setSent] = useState<FeedbackEventType | null>(null);
  const feedback = useMutation({
    mutationFn: (eventType: FeedbackEventType) => {
      if (!requestId) return Promise.reject(new Error("no request_id on this response"));
      return postFeedback({
        request_id: requestId,
        event_type: eventType,
        dish_name: plate.hero_dish_names?.[0],
        slot: undefined,
      });
    },
    onSuccess: (_data, eventType) => setSent(eventType),
  });

  return (
    <View style={styles.card}>
      <Text style={styles.plateTitle}>
        {plate.hero_dish_names?.join(" + ") ?? plate.hero_dish_ids.join(" + ")}
      </Text>
      {plate.support ? <Text style={styles.plateSupport}>with {plate.support}</Text> : null}
      <Text style={styles.plateMeta}>
        {plate.form} · score {plate.final_score.toFixed(2)}
      </Text>
      {sent ? (
        <Text style={styles.feedbackSent}>
          {sent === "like" ? "Thanks — glad you liked it!" : sent === "dislike"
            ? "Got it — we'll show this less."
            : "Noted, thanks!"}
        </Text>
      ) : (
        <View style={styles.feedbackRow}>
          <Pressable
            style={styles.feedbackButton}
            disabled={feedback.isPending || !requestId}
            onPress={() => feedback.mutate("like")}
          >
            <Text style={styles.feedbackButtonText}>👍 Like</Text>
          </Pressable>
          <Pressable
            style={styles.feedbackButton}
            disabled={feedback.isPending || !requestId}
            onPress={() => feedback.mutate("dislike")}
          >
            <Text style={styles.feedbackButtonText}>👎 Not for me</Text>
          </Pressable>
          <Pressable
            style={styles.feedbackButton}
            disabled={feedback.isPending || !requestId}
            onPress={() => feedback.mutate("accept")}
          >
            <Text style={styles.feedbackButtonText}>✓ I'll cook this</Text>
          </Pressable>
        </View>
      )}
      {feedback.isError ? (
        <Text style={styles.feedbackError}>Couldn't record that — try again.</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 12 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 12 },
  header: { fontSize: 24, fontWeight: "600", marginBottom: 8 },
  warning: { color: "#B8860B" },
  card: { borderWidth: 1, borderColor: "#E5E5E5", borderRadius: 8, padding: 16, gap: 4 },
  plateTitle: { fontSize: 18, fontWeight: "600" },
  plateSupport: { color: "#6B6B6B" },
  plateMeta: { color: "#6B6B6B", fontSize: 12 },
  button: { backgroundColor: "#1F7A3F", borderRadius: 8, padding: 14, alignItems: "center", marginTop: 8 },
  buttonText: { color: "white", fontWeight: "600" },
  secondaryButton: { alignItems: "center", padding: 8 },
  secondaryButtonText: { color: "#1F7A3F" },
  error: { color: "#C0392B", textAlign: "center" },
  feedbackRow: { flexDirection: "row", gap: 8, marginTop: 6, flexWrap: "wrap" },
  feedbackButton: {
    borderWidth: 1,
    borderColor: "#1F7A3F",
    borderRadius: 6,
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  feedbackButtonText: { color: "#1F7A3F", fontSize: 13 },
  feedbackSent: { color: "#1F7A3F", fontSize: 13, marginTop: 6 },
  feedbackError: { color: "#C0392B", fontSize: 12, marginTop: 4 },
});

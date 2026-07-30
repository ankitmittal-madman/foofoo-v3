import { View, Text, ScrollView, ActivityIndicator, Pressable, StyleSheet } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { postRecommendations } from "@/api/recommendations";
import { ApiError } from "@/api/client";
import type { Plate, RecommendationsResponse } from "@/api/types";

/**
 * Phase 1: proves the wire, not the UI (task instruction §4) — plain list rendering of whatever
 * `plates[]` the RE returns, no photos/cards/swipe. recommendations/handler.ts always returns a
 * valid 200 (RE failure -> fallback plate), so this screen has no "recommendation failed" case to
 * design for; only the network/auth failure path needs an error state.
 */
export default function Recommendations() {
  const { data, isLoading, isError, error, refetch, isRefetching } = useQuery<RecommendationsResponse>({
    queryKey: ["recommendations"],
    queryFn: () => postRecommendations(),
  });

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>
          {error instanceof ApiError ? error.message : "Could not load recommendations"}
        </Text>
        <Pressable style={styles.button} onPress={() => refetch()}>
          <Text style={styles.buttonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.header}>Your plates</Text>
      {data?.warnings?.length ? (
        <Text style={styles.warning}>{data.warnings.join(" · ")}</Text>
      ) : null}
      {data?.plates.map((plate: Plate) => (
        <PlateCard key={plate.plate_id} plate={plate} />
      ))}
      <Pressable style={styles.button} onPress={() => refetch()} disabled={isRefetching}>
        <Text style={styles.buttonText}>{isRefetching ? "Refreshing..." : "Refresh"}</Text>
      </Pressable>
      <Pressable style={styles.secondaryButton} onPress={() => router.replace("/(onboarding)/step-1")}>
        <Text style={styles.secondaryButtonText}>Back to onboarding</Text>
      </Pressable>
    </ScrollView>
  );
}

function PlateCard({ plate }: { plate: Plate }) {
  return (
    <View style={styles.card}>
      <Text style={styles.plateTitle}>
        {plate.hero_dish_names?.join(" + ") ?? plate.hero_dish_ids.join(" + ")}
      </Text>
      {plate.support ? <Text style={styles.plateSupport}>with {plate.support}</Text> : null}
      <Text style={styles.plateMeta}>
        {plate.form} · score {plate.final_score.toFixed(2)}
      </Text>
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
});

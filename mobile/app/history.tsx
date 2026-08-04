import { View, Text, ScrollView, ActivityIndicator, StyleSheet } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { fetchHistory } from "@/api/plan";
import { describeApiError } from "@/api/errorMessages";
import type { RecommendationHistoryRow } from "@/api/plan";

const OUTCOME_LABEL: Record<string, string> = {
  success: "Served",
  partial: "Served (partial)",
  timeout: "Timed out",
  network: "Network error",
  http: "Failed",
  bad_body: "Failed",
  fallback: "Unavailable",
};

/**
 * History screen (P1-3, 2026-08) — the first UI for public.recommendation_events, which had real
 * rows accumulating with zero read path anywhere (docs/active/OPEN_ITEMS.md P1-3). Reachable from
 * Settings. Deliberately simple: a reverse-chronological list of past recommendation requests
 * (when, which slot, how many dishes, whether it succeeded) — not a full plan-detail replay, since
 * the underlying table stores plates as an audit jsonb blob, not a structure this screen
 * re-renders from.
 */
export default function History() {
  const query = useQuery({
    queryKey: ["recommendation-history"],
    queryFn: () => fetchHistory(20),
  });

  if (query.isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }
  if (query.isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>{describeApiError(query.error)}</Text>
      </View>
    );
  }

  const events = query.data?.events ?? [];

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.header}>Your recommendation history</Text>
      {events.length === 0 ? (
        <Text style={styles.empty}>No recommendations yet.</Text>
      ) : (
        events.map((e: RecommendationHistoryRow) => (
          <View key={e.id} style={styles.row}>
            <Text style={styles.rowTitle}>
              {new Date(e.created_at).toLocaleDateString()} {e.slot ? `— ${e.slot}` : ""}
            </Text>
            <Text style={styles.rowMeta}>
              {OUTCOME_LABEL[e.outcome] ?? e.outcome} · {e.plate_count} dish
              {e.plate_count === 1 ? "" : "es"}
            </Text>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 12 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  header: { fontSize: 20, fontWeight: "600", marginBottom: 8 },
  empty: { color: "#6B6B6B" },
  row: { borderTopWidth: 1, borderTopColor: "#EEE", paddingTop: 10, gap: 2 },
  rowTitle: { fontSize: 14, fontWeight: "600" },
  rowMeta: { fontSize: 12, color: "#6B6B6B" },
  error: { color: "#C0392B" },
});

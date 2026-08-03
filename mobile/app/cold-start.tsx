import { useState } from "react";
import { View, Text, ScrollView, ActivityIndicator, Pressable, StyleSheet, Image } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { fetchColdStart } from "@/api/plan";
import { describeApiError } from "@/api/errorMessages";
import type { ColdStartResponse, PlanDish } from "@/api/plan";

/**
 * WP-18 surface 1 — the post-onboarding preference primer. Shows the household's top 15 diverse
 * dishes (already ranked by the RE across breakfast/lunch/dinner) and lets the user tap the ones
 * they like, seeding their cold-start taste profile before the weekly plan is built.
 *
 * "Liked" is local UI state only in this pass — it is not yet persisted to feedback_events (that
 * wiring is a follow-on once the weekly-plan/reconciliation flow this unblocks is proven). The
 * screen still fulfils its purpose: the user reviews and reacts to a representative slice of their
 * own plan before committing to it.
 */
export default function ColdStart() {
  const [liked, setLiked] = useState<Set<string>>(new Set());
  const query = useQuery<ColdStartResponse>({
    queryKey: ["cold-start"],
    queryFn: () => fetchColdStart(15),
  });

  function toggleLike(name: string) {
    setLiked((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

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
        <Pressable style={styles.button} onPress={() => query.refetch()}>
          <Text style={styles.buttonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  const dishes = query.data?.dishes ?? [];

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.header}>Tell us what you like</Text>
      <Text style={styles.subheader}>
        Tap the dishes that sound good — this helps us build your weekly plan.
      </Text>
      {dishes.map((d: PlanDish) => (
        <DishRow key={d.name} dish={d} liked={liked.has(d.name)} onToggle={() => toggleLike(d.name)} />
      ))}
      <Pressable style={styles.button} onPress={() => router.push("/weekly-plan")}>
        <Text style={styles.buttonText}>
          {liked.size > 0 ? `Continue (${liked.size} liked)` : "Continue"}
        </Text>
      </Pressable>
    </ScrollView>
  );
}

function DishRow({ dish, liked, onToggle }: { dish: PlanDish; liked: boolean; onToggle: () => void }) {
  return (
    <Pressable style={[styles.card, liked && styles.cardLiked]} onPress={onToggle}>
      {dish.image_url ? (
        <Image source={{ uri: dish.image_url }} style={styles.thumb} />
      ) : (
        <View style={[styles.thumb, styles.thumbPlaceholder]} />
      )}
      <View style={styles.cardBody}>
        <Text style={styles.dishName}>{dish.name}</Text>
        <Text style={styles.dishMeta}>
          {dish.slot ?? ""}
          {dish.meal_class_name ? ` · ${dish.meal_class_name}` : ""}
        </Text>
      </View>
      <Text style={styles.likeMark}>{liked ? "❤️" : "🤍"}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 10 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 12 },
  header: { fontSize: 24, fontWeight: "600" },
  subheader: { color: "#6B6B6B", marginBottom: 8 },
  card: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 10,
    padding: 10,
    gap: 12,
  },
  cardLiked: { borderColor: "#1F7A3F", backgroundColor: "#F3FBF6" },
  thumb: { width: 56, height: 56, borderRadius: 8, backgroundColor: "#EEE" },
  thumbPlaceholder: { alignItems: "center", justifyContent: "center" },
  cardBody: { flex: 1 },
  dishName: { fontSize: 16, fontWeight: "600" },
  dishMeta: { color: "#6B6B6B", fontSize: 12, textTransform: "capitalize" },
  likeMark: { fontSize: 20 },
  button: { backgroundColor: "#1F7A3F", borderRadius: 8, padding: 14, alignItems: "center", marginTop: 12 },
  buttonText: { color: "white", fontWeight: "600" },
  error: { color: "#C0392B", textAlign: "center" },
});

import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";

import { describeApiError } from "@/api/errorMessages";
import { fetchHistoryEvent, type PlanDish } from "@/api/plan";

/** History detail — show the dishes recorded for one recommendation event owned by the user. */
export default function HistoryDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const query = useQuery({
    queryKey: ["recommendation-history", id],
    queryFn: () => fetchHistoryEvent(id),
    enabled: Boolean(id),
  });

  if (query.isLoading) {
    return <View style={styles.center}><ActivityIndicator /></View>;
  }
  if (query.isError || !query.data?.event) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>
          {query.isError ? describeApiError(query.error) : "Recommendation not found."}
        </Text>
      </View>
    );
  }

  const event = query.data.event;
  const dishes = Array.isArray(event.plates) ? event.plates : [];

  return (
    <ScrollView testID="history-detail-screen" contentContainerStyle={styles.container}>
      <Pressable onPress={() => router.back()} accessibilityRole="button">
        <Text style={styles.back}>‹ Recommendation history</Text>
      </Pressable>
      <Text style={styles.title}>
        {new Date(event.created_at).toLocaleDateString(undefined, {
          weekday: "long", month: "long", day: "numeric", year: "numeric",
        })}
      </Text>
      {event.slot ? <Text style={styles.subtitle}>{event.slot}</Text> : null}
      {dishes.length === 0 ? (
        <Text style={styles.empty}>Dish details were not recorded for this recommendation.</Text>
      ) : (
        dishes.map((dish: PlanDish) => (
          <Pressable
            key={dish.name}
            style={styles.dish}
            onPress={() => router.push({ pathname: "/recipe/[dish]", params: { dish: dish.name } })}
          >
            {dish.image_url ? (
              <Image source={{ uri: dish.image_url }} style={styles.image} />
            ) : (
              <View style={styles.image} />
            )}
            <View style={styles.dishBody}>
              <Text style={styles.dishName}>{dish.name}</Text>
              <Text style={styles.meta}>{dish.meal_class_name ?? dish.cuisine}</Text>
            </View>
            <Text style={styles.chevron}>›</Text>
          </Pressable>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 12 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  back: { color: "#1F7A3F", fontWeight: "600" },
  title: { fontSize: 22, fontWeight: "700", marginTop: 4 },
  subtitle: { color: "#666", textTransform: "capitalize", marginTop: -8 },
  dish: { flexDirection: "row", alignItems: "center", gap: 12, borderTopWidth: 1, borderTopColor: "#EEE", paddingTop: 12 },
  image: { width: 64, height: 64, borderRadius: 8, backgroundColor: "#EEE" },
  dishBody: { flex: 1, gap: 2 },
  dishName: { fontSize: 16, fontWeight: "600" },
  meta: { color: "#666", fontSize: 12 },
  chevron: { color: "#1F7A3F", fontSize: 24 },
  empty: { color: "#666" },
  error: { color: "#C0392B", textAlign: "center" },
});

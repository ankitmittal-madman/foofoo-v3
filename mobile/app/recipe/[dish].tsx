import { View, Text, ScrollView, ActivityIndicator, Pressable, StyleSheet, Image } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import { fetchRecipe } from "@/api/plan";
import type { RecipeResponse } from "@/api/plan";
import { describeApiError } from "@/api/errorMessages";

/**
 * WP-18 surface 5 — the meal-detail screen. Full recipe (ingredients, steps, times) + Cloudinary
 * image for one dish, reached by tapping any dish card in cold-start / the Home tab (formerly
 * daily-plan.tsx, relocated to app/(tabs)/today.tsx).
 */
export default function RecipeDetail() {
  const { dish } = useLocalSearchParams<{ dish: string }>();
  const query = useQuery<RecipeResponse>({
    queryKey: ["recipe", dish],
    queryFn: () => fetchRecipe(dish),
    enabled: !!dish,
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
        <Pressable style={styles.button} onPress={() => query.refetch()}>
          <Text style={styles.buttonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  const data = query.data;
  const recipe = data?.recipe;

  return (
    <ScrollView testID="recipe-screen" contentContainerStyle={styles.container}>
      {data?.image_url ? (
        <Image source={{ uri: data.image_url }} style={styles.hero} />
      ) : (
        <View style={[styles.hero, styles.heroPlaceholder]}>
          <Text style={styles.heroPlaceholderText}>No photo yet</Text>
        </View>
      )}
      <Text style={styles.title}>{dish}</Text>

      {!recipe ? (
        <Text style={styles.error}>No recipe available for this dish yet.</Text>
      ) : (
        <>
          <View style={styles.metaRow}>
            <Meta label="Serves" value={recipe.serves} />
            <Meta label="Prep" value={`${recipe.prep_mins} min`} />
            <Meta label="Cook" value={`${recipe.cook_mins} min`} />
            {recipe.spice_level != null ? (
              <Meta label="Spice" value={"🌶".repeat(Math.max(1, recipe.spice_level))} />
            ) : null}
          </View>

          <Text style={styles.sectionTitle}>Ingredients</Text>
          {recipe.ingredients.map((ing: string, i: number) => (
            <Text key={i} style={styles.listItem}>
              • {ing}
            </Text>
          ))}

          <Text style={styles.sectionTitle}>Method</Text>
          {recipe.steps.map((step: string, i: number) => (
            <View key={i} style={styles.stepRow}>
              <Text style={styles.stepNumber}>{i + 1}</Text>
              <Text style={styles.stepText}>{step}</Text>
            </View>
          ))}
        </>
      )}

      <Pressable testID="recipe-back" style={styles.secondaryButton} onPress={() => router.back()}>
        <Text style={styles.secondaryButtonText}>Back</Text>
      </Pressable>
    </ScrollView>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metaItem}>
      <Text style={styles.metaLabel}>{label}</Text>
      <Text style={styles.metaValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 12 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 12 },
  hero: { width: "100%", height: 220, borderRadius: 12, backgroundColor: "#EEE" },
  heroPlaceholder: { alignItems: "center", justifyContent: "center" },
  heroPlaceholderText: { color: "#999" },
  title: { fontSize: 24, fontWeight: "700" },
  metaRow: { flexDirection: "row", flexWrap: "wrap", gap: 16, marginBottom: 8 },
  metaItem: { minWidth: 70 },
  metaLabel: { fontSize: 11, color: "#6B6B6B" },
  metaValue: { fontSize: 15, fontWeight: "600" },
  sectionTitle: { fontSize: 18, fontWeight: "700", marginTop: 8 },
  listItem: { fontSize: 14, color: "#333" },
  stepRow: { flexDirection: "row", gap: 8, alignItems: "flex-start" },
  stepNumber: { fontWeight: "700", color: "#1F7A3F", width: 20 },
  stepText: { flex: 1, fontSize: 14, color: "#333" },
  secondaryButton: { alignItems: "center", padding: 12, marginTop: 12 },
  secondaryButtonText: { color: "#1F7A3F" },
  error: { color: "#C0392B", textAlign: "center" },
  button: { backgroundColor: "#1F7A3F", borderRadius: 8, padding: 14, alignItems: "center", marginTop: 8 },
  buttonText: { color: "white", fontWeight: "600" },
});

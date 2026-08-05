import { useState } from "react";
import {
  ActivityIndicator,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";

import { describeApiError } from "@/api/errorMessages";
import { searchDishes, type Slot } from "@/api/plan";

const SLOTS: Array<Slot | undefined> = [undefined, "breakfast", "lunch", "dinner"];

/** Safety-aware catalogue search for explicit cravings outside the generated daily slate. */
export default function SearchScreen() {
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [slot, setSlot] = useState<Slot | undefined>();
  const results = useQuery({
    queryKey: ["dish-search", query, slot ?? "all"],
    queryFn: () => searchDishes(query, { slot, limit: 30 }),
    enabled: query.length > 0,
  });

  return (
    <ScrollView
      testID="search-screen"
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Text style={styles.header}>Find a dish</Text>
      <View style={styles.searchRow}>
        <TextInput
          testID="search-input"
          accessibilityLabel="Dish, cuisine, or meal class"
          placeholder="Dish, cuisine, or meal class"
          value={draft}
          onChangeText={setDraft}
          onSubmitEditing={() => setQuery(draft.trim())}
          style={styles.input}
        />
        <Pressable
          testID="search-submit"
          style={styles.searchButton}
          onPress={() => setQuery(draft.trim())}
        >
          <Text style={styles.searchButtonText}>Search</Text>
        </Pressable>
      </View>
      <View style={styles.filters}>
        {SLOTS.map((value) => (
          <Pressable
            key={value ?? "all"}
            style={[styles.chip, slot === value && styles.chipActive]}
            onPress={() => setSlot(value)}
          >
            <Text style={slot === value ? styles.chipTextActive : styles.chipText}>
              {value ?? "all meals"}
            </Text>
          </Pressable>
        ))}
      </View>
      {results.isFetching ? <ActivityIndicator /> : null}
      {results.isError ? <Text style={styles.error}>{describeApiError(results.error)}</Text> : null}
      {results.data && results.data.options.length === 0
        ? <Text>No matching safe dishes found.</Text>
        : null}
      {(results.data?.options ?? []).map((dish, index) => (
        <Pressable
          testID={`search-result-${index}`}
          key={dish.name}
          style={styles.result}
          onPress={() => router.push({ pathname: "/recipe/[dish]", params: { dish: dish.name } })}
        >
          {dish.image_url
            ? <Image source={{ uri: dish.image_url }} style={styles.image} />
            : <View style={styles.image} />}
          <View style={styles.resultBody}>
            <Text style={styles.name}>{dish.name}</Text>
            <Text style={styles.meta}>{dish.cuisine} · {dish.total_mins ?? "?"} min</Text>
          </View>
        </Pressable>
      ))}
      <Pressable
        testID="submit-missing-dish"
        style={styles.addDish}
        onPress={() => router.push("/submit-dish")}
      >
        <Text style={styles.addDishText}>Can’t find it? Add a dish</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 12 },
  header: { fontSize: 24, fontWeight: "700" },
  searchRow: { flexDirection: "row", gap: 8 },
  input: { flex: 1, borderWidth: 1, borderColor: "#CCC", borderRadius: 8, padding: 10 },
  searchButton: {
    backgroundColor: "#1F7A3F",
    borderRadius: 8,
    paddingHorizontal: 16,
    justifyContent: "center",
  },
  searchButtonText: { color: "white", fontWeight: "600" },
  filters: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    borderWidth: 1,
    borderColor: "#1F7A3F",
    borderRadius: 16,
    paddingVertical: 5,
    paddingHorizontal: 10,
  },
  chipActive: { backgroundColor: "#1F7A3F" },
  chipText: { color: "#1F7A3F" },
  chipTextActive: { color: "white" },
  result: {
    flexDirection: "row",
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#EEE",
    paddingVertical: 10,
  },
  image: { width: 64, height: 64, borderRadius: 8, backgroundColor: "#EEE" },
  resultBody: { flex: 1, justifyContent: "center" },
  name: { fontSize: 16, fontWeight: "600" },
  meta: { color: "#666" },
  error: { color: "#C0392B" },
  addDish: {
    borderWidth: 1,
    borderColor: "#1F7A3F",
    borderRadius: 8,
    padding: 12,
    alignItems: "center",
    marginTop: 8,
  },
  addDishText: { color: "#1F7A3F", fontWeight: "600" },
});

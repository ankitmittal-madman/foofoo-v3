import { useEffect, useState } from "react";
import { View, Text, ScrollView, ActivityIndicator, Pressable, StyleSheet } from "react-native";
import { useMutation, useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { fetchProfile } from "@/api/plan";
import { postHousehold } from "@/api/household";
import { allergenFlags } from "@/onboarding/toHouseholdWrite";
import { ChipGroup, type ChipOption } from "@/onboarding/OnboardingChips";
import { describeApiError } from "@/api/errorMessages";

const DIET_OPTIONS: ChipOption[] = [
  { value: "veg", label: "Vegetarian" },
  { value: "non_veg", label: "Non-vegetarian" },
  { value: "egg", label: "Eggetarian" },
  { value: "vegan", label: "Vegan" },
];

const ALLERGENS: ChipOption[] = [
  { value: "peanuts", label: "Peanut" },
  { value: "dairy", label: "Dairy" },
  { value: "gluten", label: "Gluten" },
  { value: "soy", label: "Soy" },
  { value: "sesame", label: "Sesame" },
  { value: "shellfish", label: "Shellfish" },
  { value: "fish", label: "Fish" },
  { value: "mustard", label: "Mustard" },
];

/**
 * Profile/preferences edit screen (P1-4, 2026-08) — the first way to change diet/allergens after
 * onboarding finishes. Reachable from Settings. household/handler.ts's write path
 * (POST /v1/household) was always create-once-then-accumulate; this screen is the first caller to
 * re-invoke it for an UPDATE (diet_type/allergen_flags are idempotent upserts server-side, so
 * re-sending them for an existing profile is safe — verified by reading store.ts's
 * upsertHouseholdAnswers/profiles update path before building this).
 */
export default function ProfileEdit() {
  const query = useQuery({ queryKey: ["profile"], queryFn: fetchProfile });
  const [diet, setDiet] = useState<string | null>(null);
  const [allergens, setAllergens] = useState<string[]>([]);

  useEffect(() => {
    if (query.data) {
      setDiet(query.data.household.q5_diet);
      setAllergens(query.data.household.q9_allergies);
    }
  }, [query.data]);

  const save = useMutation({
    mutationFn: () =>
      postHousehold([
        { screen_id: "profile-edit", question_key: "diet_type", answer_value: diet },
        {
          screen_id: "profile-edit",
          question_key: "allergen_flags",
          answer_value: allergenFlags(allergens),
        },
      ]),
    onSuccess: () => router.back(),
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

  return (
    <ScrollView testID="profile-edit-screen" contentContainerStyle={styles.container}>
      <Text style={styles.header}>Edit preferences</Text>

      <Text style={styles.label}>Diet</Text>
      <ChipGroup
        options={DIET_OPTIONS}
        selected={diet ? [diet] : []}
        onToggle={(v) => setDiet(v)}
        testIDPrefix="profile-edit-diet"
      />

      <Text style={styles.label}>Allergies</Text>
      <ChipGroup
        options={ALLERGENS}
        selected={allergens}
        onToggle={(v) =>
          setAllergens((prev) => (prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v]))}
        testIDPrefix="profile-edit-allergen"
      />

      <Pressable
        style={styles.button}
        disabled={save.isPending}
        onPress={() => save.mutate()}
        testID="profile-edit-save"
      >
        {save.isPending ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonLabel}>Save</Text>}
      </Pressable>
      {save.isError ? <Text style={styles.error}>{describeApiError(save.error)}</Text> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 12 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  header: { fontSize: 20, fontWeight: "600", marginBottom: 8 },
  label: { fontSize: 14, fontWeight: "700", marginTop: 12 },
  button: {
    backgroundColor: "#4A6FA5",
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: "center",
    marginTop: 20,
  },
  buttonLabel: { color: "#fff", fontWeight: "600" },
  error: { color: "#C0392B", fontSize: 12, marginTop: 8 },
});

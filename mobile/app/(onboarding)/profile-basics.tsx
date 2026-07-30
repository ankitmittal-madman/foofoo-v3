import { useState } from "react";
import { View, Text, TextInput, Pressable, ScrollView, StyleSheet } from "react-native";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { postHousehold } from "@/api/household";
import type { ScreenAnswer } from "@/api/types";
import { ApiError } from "@/api/client";

const DIET_TYPES = ["veg", "non_veg", "egg", "vegan", "jain"] as const;
const COOK_CAPABILITIES = ["beginner", "intermediate", "advanced"] as const;

/**
 * Screen 1 of 4 — the five public.profiles NOT NULL columns (schema.ts's PROFILE_REQUIRED_FIELDS).
 * Ordered first (ahead of DOC-05's cohort/household screens) because household/handler.ts hard-
 * rejects household_members writes until a profiles row exists (see DOC-P4-03 §3).
 */
export default function ProfileBasics() {
  const [primaryCookName, setPrimaryCookName] = useState("");
  const [homeState, setHomeState] = useState("");
  const [currentCity, setCurrentCity] = useState("");
  const [dietType, setDietType] = useState<(typeof DIET_TYPES)[number] | null>(null);
  const [cookCapability, setCookCapability] = useState<(typeof COOK_CAPABILITIES)[number] | null>(
    null,
  );

  const mutation = useMutation({
    mutationFn: () => {
      const screens: ScreenAnswer[] = [
        { screen_id: "profile-basics", question_key: "primary_cook_name", answer_value: primaryCookName },
        { screen_id: "profile-basics", question_key: "home_state", answer_value: homeState },
        { screen_id: "profile-basics", question_key: "current_city", answer_value: currentCity },
        { screen_id: "profile-basics", question_key: "diet_type", answer_value: dietType },
        { screen_id: "profile-basics", question_key: "cook_capability", answer_value: cookCapability },
      ];
      return postHousehold(screens, []);
    },
    onSuccess: () => router.push("/(onboarding)/household"),
  });

  const canSubmit =
    primaryCookName.trim().length > 0 &&
    homeState.trim().length > 0 &&
    currentCity.trim().length > 0 &&
    dietType !== null &&
    cookCapability !== null;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.progress}>Step 1 of 4</Text>
      <Text style={styles.header}>Tell us about your kitchen</Text>

      <Field label="Who's the primary cook? (name)">
        <TextInput style={styles.input} value={primaryCookName} onChangeText={setPrimaryCookName} />
      </Field>

      <Field label="Home state (question_key: home_state)">
        <TextInput style={styles.input} value={homeState} onChangeText={setHomeState} placeholder="e.g. Madhya Pradesh" />
      </Field>

      <Field label="Current city (question_key: current_city)">
        <TextInput style={styles.input} value={currentCity} onChangeText={setCurrentCity} placeholder="e.g. Pune" />
      </Field>

      <Field label="Diet type">
        <ChipRow options={DIET_TYPES} value={dietType} onChange={setDietType} />
      </Field>

      <Field label="Cook capability">
        <ChipRow options={COOK_CAPABILITIES} value={cookCapability} onChange={setCookCapability} />
      </Field>

      {mutation.isError ? (
        <Text style={styles.error}>
          {mutation.error instanceof ApiError ? mutation.error.message : "Something went wrong"}
        </Text>
      ) : null}

      <Pressable
        style={[styles.button, !canSubmit && styles.buttonDisabled]}
        disabled={!canSubmit || mutation.isPending}
        onPress={() => mutation.mutate()}
      >
        <Text style={styles.buttonText}>{mutation.isPending ? "Saving..." : "Continue"}</Text>
      </Pressable>
    </ScrollView>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      {children}
    </View>
  );
}

function ChipRow<T extends string>({
  options,
  value,
  onChange,
}: {
  options: readonly T[];
  value: T | null;
  onChange: (v: T) => void;
}) {
  return (
    <View style={styles.chipRow}>
      {options.map((opt) => (
        <Pressable
          key={opt}
          style={[styles.chip, value === opt && styles.chipSelected]}
          onPress={() => onChange(opt)}
        >
          <Text style={[styles.chipText, value === opt && styles.chipTextSelected]}>{opt}</Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 16 },
  progress: { color: "#6B6B6B", fontSize: 12, textTransform: "uppercase" },
  header: { fontSize: 24, fontWeight: "600", marginBottom: 8 },
  field: { gap: 6 },
  label: { fontSize: 14, color: "#3A3A3A" },
  input: { borderWidth: 1, borderColor: "#D1D1D1", borderRadius: 8, padding: 12 },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: { borderWidth: 1, borderColor: "#D1D1D1", borderRadius: 20, paddingVertical: 8, paddingHorizontal: 14 },
  chipSelected: { backgroundColor: "#1F7A3F", borderColor: "#1F7A3F" },
  chipText: { color: "#1C1C1E" },
  chipTextSelected: { color: "white" },
  button: { backgroundColor: "#1F7A3F", borderRadius: 8, padding: 14, alignItems: "center", marginTop: 8 },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: "white", fontWeight: "600" },
  error: { color: "#C0392B" },
});

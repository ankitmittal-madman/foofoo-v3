import { useState } from "react";
import { View, Text, TextInput, Pressable, ScrollView, StyleSheet } from "react-native";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { postHousehold } from "@/api/household";
import type { ScreenAnswer } from "@/api/types";
import { ApiError } from "@/api/client";

// household/schema.ts's HOUSEHOLD_ANSWERS_SCHEMAS: q6/q7/q11 are string arrays with no fixed
// CHECK-constraint vocabulary in migration 038 (unlike q1/diet_type/etc.) — Phase 1 collects them
// as free-text comma-separated lists rather than inventing a chip vocabulary not backed by a schema
// constraint (see DOC-P4-03 Critical Self-Review).
function parseList(input: string): string[] {
  return input
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function FoodAndHealth() {
  const [nonvegTypes, setNonvegTypes] = useState("");
  const [vegDays, setVegDays] = useState("");
  const [allergyOther, setAllergyOther] = useState("");
  const [conditions, setConditions] = useState("");

  const mutation = useMutation({
    mutationFn: () => {
      const screens: ScreenAnswer[] = [
        { screen_id: "food-and-health", question_key: "q6_nonveg_types", answer_value: parseList(nonvegTypes) },
        { screen_id: "food-and-health", question_key: "q7_veg_days", answer_value: parseList(vegDays) },
        { screen_id: "food-and-health", question_key: "q10_allergy_other", answer_value: allergyOther },
        { screen_id: "food-and-health", question_key: "q11_conditions", answer_value: parseList(conditions) },
      ];
      return postHousehold(screens, []);
    },
    onSuccess: () => router.push("/(onboarding)/lifestyle"),
  });

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.progress}>Step 3 of 4</Text>
      <Text style={styles.header}>Food & health</Text>

      <Field label="Non-veg types you eat (comma-separated, e.g. chicken, fish)">
        <TextInput style={styles.input} value={nonvegTypes} onChangeText={setNonvegTypes} />
      </Field>

      <Field label="Veg days (comma-separated, e.g. Monday, Thursday)">
        <TextInput style={styles.input} value={vegDays} onChangeText={setVegDays} />
      </Field>

      <Field label="Any allergy not listed elsewhere">
        <TextInput style={styles.input} value={allergyOther} onChangeText={setAllergyOther} />
      </Field>

      <Field label="Health conditions in the household (comma-separated)">
        <TextInput style={styles.input} value={conditions} onChangeText={setConditions} />
      </Field>

      {mutation.isError ? (
        <Text style={styles.error}>
          {mutation.error instanceof ApiError ? mutation.error.message : "Something went wrong"}
        </Text>
      ) : null}

      <Pressable style={styles.button} disabled={mutation.isPending} onPress={() => mutation.mutate()}>
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

const styles = StyleSheet.create({
  container: { padding: 24, gap: 16 },
  progress: { color: "#6B6B6B", fontSize: 12, textTransform: "uppercase" },
  header: { fontSize: 24, fontWeight: "600", marginBottom: 8 },
  field: { gap: 6 },
  label: { fontSize: 14, color: "#3A3A3A" },
  input: { borderWidth: 1, borderColor: "#D1D1D1", borderRadius: 8, padding: 12 },
  button: { backgroundColor: "#1F7A3F", borderRadius: 8, padding: 14, alignItems: "center", marginTop: 8 },
  buttonText: { color: "white", fontWeight: "600" },
  error: { color: "#C0392B" },
});

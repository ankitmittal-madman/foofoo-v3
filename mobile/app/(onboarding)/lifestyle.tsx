import { useState } from "react";
import { View, Text, TextInput, Pressable, ScrollView, StyleSheet } from "react-native";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { postHousehold } from "@/api/household";
import type { ScreenAnswer } from "@/api/types";
import { ApiError } from "@/api/client";

const WHO_COOKS = ["self", "family", "hired_cook", "order_tiffin"] as const;
const OBJECTIVES = ["awesome_taste", "healthy_living", "into_fitness", "protein_calculator"] as const;

export default function Lifestyle() {
  const [whoCooks, setWhoCooks] = useState<(typeof WHO_COOKS)[number] | null>(null);
  const [eatOutPerWeek, setEatOutPerWeek] = useState("2");
  const [objective, setObjective] = useState<(typeof OBJECTIVES)[number] | null>(null);

  const mutation = useMutation({
    mutationFn: () => {
      const screens: ScreenAnswer[] = [
        { screen_id: "lifestyle", question_key: "q13_who_cooks", answer_value: whoCooks },
        {
          screen_id: "lifestyle",
          question_key: "q14_eat_out_per_week",
          answer_value: Number(eatOutPerWeek) || 0,
        },
        { screen_id: "lifestyle", question_key: "q15_objective", answer_value: objective },
      ];
      return postHousehold(screens, []);
    },
    onSuccess: () => router.replace("/recommendations"),
  });

  const canSubmit = whoCooks !== null && objective !== null;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.progress}>Step 4 of 4</Text>
      <Text style={styles.header}>Lifestyle & goals</Text>

      <View style={styles.field}>
        <Text style={styles.label}>Who cooks?</Text>
        <View style={styles.chipRow}>
          {WHO_COOKS.map((opt) => (
            <Pressable key={opt} style={[styles.chip, whoCooks === opt && styles.chipSelected]} onPress={() => setWhoCooks(opt)}>
              <Text style={[styles.chipText, whoCooks === opt && styles.chipTextSelected]}>{opt}</Text>
            </Pressable>
          ))}
        </View>
      </View>

      <View style={styles.field}>
        <Text style={styles.label}>How many times a week do you eat out?</Text>
        <TextInput style={styles.input} keyboardType="number-pad" value={eatOutPerWeek} onChangeText={setEatOutPerWeek} />
      </View>

      <View style={styles.field}>
        <Text style={styles.label}>Your main objective</Text>
        <View style={styles.chipRow}>
          {OBJECTIVES.map((opt) => (
            <Pressable key={opt} style={[styles.chip, objective === opt && styles.chipSelected]} onPress={() => setObjective(opt)}>
              <Text style={[styles.chipText, objective === opt && styles.chipTextSelected]}>{opt}</Text>
            </Pressable>
          ))}
        </View>
      </View>

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
        <Text style={styles.buttonText}>{mutation.isPending ? "Saving..." : "See my plan"}</Text>
      </Pressable>
    </ScrollView>
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

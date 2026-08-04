import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { addDishToDate, type Slot } from "@/api/plan";

export default function AddToDate() {
  const params = useLocalSearchParams<{ dish: string; classCode: string; slot: Slot; date?: string }>();
  const queryClient = useQueryClient();
  const [chosen, setChosen] = useState<string | null>(params.date ?? null);
  const dates = Array.from({ length: 7 }, (_, index) => {
    const date = new Date();
    date.setHours(12, 0, 0, 0);
    date.setDate(date.getDate() + index);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  });
  const mutation = useMutation({
    mutationFn: (slotDate: string) => addDishToDate({
      slot_date: slotDate,
      slot: params.slot,
      class_code: params.classCode,
      dish_name: params.dish,
    }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["saved-week"] }),
        queryClient.invalidateQueries({ queryKey: ["daily-plan"] }),
      ]);
      router.back();
    },
  });
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Add {params.dish} to your plan</Text>
      {dates.map((date) => (
        <Pressable key={date} style={[styles.date, chosen === date && styles.selected]}
          onPress={() => setChosen(date)}>
          <Text>{new Date(`${date}T12:00:00`).toLocaleDateString(undefined, {
            weekday: "long", month: "short", day: "numeric",
          })}</Text>
        </Pressable>
      ))}
      <Pressable disabled={!chosen || mutation.isPending} style={styles.button}
        onPress={() => chosen && mutation.mutate(chosen)}>
        <Text style={styles.buttonText}>{mutation.isPending ? "Adding…" : "Add to plan"}</Text>
      </Pressable>
      {mutation.isError ? <Text style={styles.error}>Could not update your plan. Try again.</Text> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, gap: 12 },
  title: { fontSize: 22, fontWeight: "700", marginBottom: 8 },
  date: { borderWidth: 1, borderColor: "#DDD", borderRadius: 10, padding: 14 },
  selected: { borderColor: "#1F7A3F", backgroundColor: "#EDF7F0" },
  button: { backgroundColor: "#1F7A3F", padding: 14, borderRadius: 10, alignItems: "center" },
  buttonText: { color: "white", fontWeight: "700" },
  error: { color: "#C0392B" },
});

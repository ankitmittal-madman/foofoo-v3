import { useState } from "react";
import { View, Text, ScrollView, ActivityIndicator, Pressable, StyleSheet } from "react-native";
import { useQuery, useMutation } from "@tanstack/react-query";
import { router } from "expo-router";
import { fetchWeeklyPlan } from "@/api/plan";
import type { WeeklyClass, WeeklyPlanResponse } from "@/api/plan";
import { describeApiError } from "@/api/errorMessages";
import type { SlotName } from "@/lib/weeklyPlanStore";
import { saveWeeklyPlan, type FinalizedWeek } from "@/lib/weeklyPlanStore";

const SLOTS: SlotName[] = ["breakfast", "lunch", "dinner"];

/**
 * WP-18 surface 3 — the weekly class plan. For each day and slot, shows the top-3 meal CLASSES
 * (already filtered server-side to classes with at least one backing dish — see meal_planner.
 * weekly_class_plan's dish_count) and lets the user pick one per day/slot, then finalize.
 *
 * Finalizing writes the selection to weeklyPlanStore (device-local for now) and moves to the daily
 * plan, which reconciles that day's dishes to ONLY the finalized class — the WP-18 guarantee.
 */
export default function WeeklyPlan() {
  const query = useQuery<WeeklyPlanResponse>({
    queryKey: ["weekly-plan"],
    queryFn: () => fetchWeeklyPlan(3),
  });
  const [selected, setSelected] = useState<FinalizedWeek>({});

  const finalize = useMutation({
    mutationFn: (plan: FinalizedWeek) => saveWeeklyPlan(plan),
    onSuccess: () => router.replace("/daily-plan"),
  });

  function choose(weekday: string, slot: SlotName, classCode: string) {
    setSelected((prev) => ({ ...prev, [weekday]: { ...prev[weekday], [slot]: classCode } }));
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

  const days = query.data?.days ?? [];
  const totalSlots = days.length * SLOTS.length;
  const chosenCount = Object.values(selected).reduce((n, s) => n + Object.keys(s).length, 0);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.header}>Your weekly plan</Text>
      <Text style={styles.subheader}>Pick a meal class for each slot, then finalize.</Text>
      {days.map((day: WeeklyPlanResponse["days"][number]) => (
        <View key={day.weekday} style={styles.dayBlock}>
          <Text style={styles.dayTitle}>{day.weekday}</Text>
          {SLOTS.map((slot) => (
            <View key={slot} style={styles.slotRow}>
              <Text style={styles.slotLabel}>{slot}</Text>
              <View style={styles.chipRow}>
                {(day.slots[slot] ?? []).map((c: WeeklyClass) => {
                  const isChosen = selected[day.weekday]?.[slot] === c.class_code;
                  return (
                    <Pressable
                      key={c.class_code}
                      style={[styles.chip, isChosen && styles.chipChosen]}
                      onPress={() => choose(day.weekday, slot, c.class_code)}
                    >
                      <Text style={[styles.chipText, isChosen && styles.chipTextChosen]}>
                        {c.class_name}
                      </Text>
                    </Pressable>
                  );
                })}
                {(day.slots[slot] ?? []).length === 0 ? (
                  <Text style={styles.noClasses}>No options for this slot</Text>
                ) : null}
              </View>
            </View>
          ))}
        </View>
      ))}
      <Pressable
        style={[styles.button, chosenCount === 0 && styles.buttonDisabled]}
        disabled={chosenCount === 0 || finalize.isPending}
        onPress={() => finalize.mutate(selected)}
      >
        <Text style={styles.buttonText}>
          {finalize.isPending
            ? "Saving..."
            : `Finalize plan (${chosenCount}/${totalSlots} chosen)`}
        </Text>
      </Pressable>
      {finalize.isError ? <Text style={styles.error}>Couldn't save your plan — try again.</Text> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 14 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 12 },
  header: { fontSize: 24, fontWeight: "600" },
  subheader: { color: "#6B6B6B", marginBottom: 4 },
  dayBlock: { borderTopWidth: 1, borderTopColor: "#EEE", paddingTop: 10, gap: 8 },
  dayTitle: { fontSize: 16, fontWeight: "700" },
  slotRow: { gap: 6 },
  slotLabel: { fontSize: 13, color: "#6B6B6B", textTransform: "capitalize" },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    borderWidth: 1,
    borderColor: "#1F7A3F",
    borderRadius: 16,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  chipChosen: { backgroundColor: "#1F7A3F" },
  chipText: { color: "#1F7A3F", fontSize: 12 },
  chipTextChosen: { color: "white" },
  noClasses: { color: "#B8860B", fontSize: 12 },
  button: { backgroundColor: "#1F7A3F", borderRadius: 8, padding: 14, alignItems: "center", marginTop: 8 },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: "white", fontWeight: "600" },
  error: { color: "#C0392B", textAlign: "center" },
});

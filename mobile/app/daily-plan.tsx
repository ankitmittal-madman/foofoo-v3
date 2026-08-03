import { useEffect, useState } from "react";
import { View, Text, ScrollView, ActivityIndicator, Pressable, StyleSheet, Image } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { fetchClassDishes, fetchSlotOptions } from "@/api/plan";
import { describeApiError } from "@/api/errorMessages";
import { loadWeeklyPlan, type FinalizedWeek, type SlotName } from "@/lib/weeklyPlanStore";
import type { PlanDish } from "@/api/plan";

const SLOTS: SlotName[] = ["breakfast", "lunch", "dinner"];
const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

/**
 * WP-18 surface 2 + 4 — the daily meal plan. Shows today's Breakfast/Lunch/Dinner, each with 4–5
 * dish options.
 *
 * RECONCILIATION (the WP-18 guarantee): if the user finalized a meal CLASS for this slot on the
 * weekly-plan screen, the options here come ONLY from that class (fetchClassDishes) — never a
 * generic slot ranking that could disagree with the chosen plan. A slot the user never finalized
 * falls back to the plain top-ranked options (fetchSlotOptions) so the screen is still useful
 * before the weekly plan is set.
 */
export default function DailyPlan() {
  const [weekday, setWeekday] = useState<string>(WEEKDAYS[new Date().getDay()]);
  const [plan, setPlan] = useState<FinalizedWeek | null>(null);
  const [planLoaded, setPlanLoaded] = useState(false);

  useEffect(() => {
    loadWeeklyPlan().then((p) => {
      setPlan(p);
      setPlanLoaded(true);
    });
  }, []);

  if (!planLoaded) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.header}>Today's plan</Text>
      <View style={styles.dayPicker}>
        {WEEKDAYS.map((d) => (
          <Pressable
            key={d}
            style={[styles.dayChip, weekday === d && styles.dayChipActive]}
            onPress={() => setWeekday(d)}
          >
            <Text style={[styles.dayChipText, weekday === d && styles.dayChipTextActive]}>
              {d.slice(0, 3)}
            </Text>
          </Pressable>
        ))}
      </View>
      {SLOTS.map((slot) => (
        <SlotSection key={slot} slot={slot} weekday={weekday} classCode={plan?.[weekday]?.[slot]} />
      ))}
      <Pressable style={styles.secondaryButton} onPress={() => router.push("/weekly-plan")}>
        <Text style={styles.secondaryButtonText}>Edit weekly plan</Text>
      </Pressable>
    </ScrollView>
  );
}

function SlotSection({
  slot,
  weekday,
  classCode,
}: {
  slot: SlotName;
  weekday: string;
  classCode?: string;
}) {
  const query = useQuery({
    queryKey: ["daily-plan", slot, weekday, classCode ?? null],
    queryFn: () =>
      classCode
        ? fetchClassDishes(slot, classCode, weekday, 5)
        : fetchSlotOptions(slot, { weekday, count: 5 }),
  });

  return (
    <View style={styles.slotBlock}>
      <Text style={styles.slotTitle}>{slot}</Text>
      {classCode ? (
        <Text style={styles.reconciledNote}>from your finalized plan</Text>
      ) : (
        <Text style={styles.reconciledNote}>no class finalized — showing top picks</Text>
      )}
      {query.isLoading ? (
        <ActivityIndicator />
      ) : query.isError ? (
        <Text style={styles.error}>{describeApiError(query.error)}</Text>
      ) : (
        (query.data?.options ?? []).map((d: PlanDish) => (
          <Pressable
            key={d.name}
            style={styles.dishCard}
            onPress={() => router.push({ pathname: "/recipe/[dish]", params: { dish: d.name } })}
          >
            {d.image_url ? (
              <Image source={{ uri: d.image_url }} style={styles.thumb} />
            ) : (
              <View style={[styles.thumb, styles.thumbPlaceholder]} />
            )}
            <View style={styles.dishBody}>
              <Text style={styles.dishName}>{d.name}</Text>
              <Text style={styles.dishMeta}>{d.meal_class_name ?? d.cuisine}</Text>
            </View>
          </Pressable>
        ))
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 16 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  header: { fontSize: 24, fontWeight: "600" },
  dayPicker: { flexDirection: "row", gap: 6, flexWrap: "wrap" },
  dayChip: { borderWidth: 1, borderColor: "#E5E5E5", borderRadius: 14, paddingVertical: 6, paddingHorizontal: 10 },
  dayChipActive: { backgroundColor: "#1F7A3F", borderColor: "#1F7A3F" },
  dayChipText: { fontSize: 12, color: "#333" },
  dayChipTextActive: { color: "white" },
  slotBlock: { gap: 8, borderTopWidth: 1, borderTopColor: "#EEE", paddingTop: 10 },
  slotTitle: { fontSize: 18, fontWeight: "700", textTransform: "capitalize" },
  reconciledNote: { fontSize: 11, color: "#6B6B6B" },
  dishCard: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 10,
    padding: 10,
    gap: 12,
  },
  thumb: { width: 48, height: 48, borderRadius: 8, backgroundColor: "#EEE" },
  thumbPlaceholder: { alignItems: "center", justifyContent: "center" },
  dishBody: { flex: 1 },
  dishName: { fontSize: 15, fontWeight: "600" },
  dishMeta: { color: "#6B6B6B", fontSize: 12 },
  secondaryButton: { alignItems: "center", padding: 8, marginTop: 4 },
  secondaryButtonText: { color: "#1F7A3F" },
  error: { color: "#C0392B" },
});

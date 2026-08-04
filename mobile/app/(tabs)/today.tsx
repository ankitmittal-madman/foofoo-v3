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
 * Home tab — today's meal selection (breakfast/lunch/dinner), the app's new default landing
 * surface. Adapted from the former daily-plan.tsx: same SLOTS/SlotSection logic and the same
 * WP-18 reconciliation guarantee (a slot with a finalized weekly class shows ONLY that class's
 * dishes via fetchClassDishes; an unfinalized slot falls back to fetchSlotOptions' top picks) —
 * only the presentation changed. Per the Founder's restructuring request this screen now shows
 * ONLY today (the actual current weekday, computed once from `new Date()`, no day-picker) and
 * drops the "Edit weekly plan" button now that Week Plan is its own persistent tab rather than a
 * screen reached mid-flow from here.
 */
export default function Home() {
  const weekday = WEEKDAYS[new Date().getDay()];
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
      <Text style={styles.subheader}>{weekday}</Text>
      {SLOTS.map((slot) => (
        <SlotSection key={slot} slot={slot} weekday={weekday} classCode={plan?.[weekday]?.[slot]} />
      ))}
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
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.cardRow}
        >
          {(query.data?.options ?? []).map((d: PlanDish) => (
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
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 16 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  header: { fontSize: 24, fontWeight: "600" },
  subheader: { color: "#6B6B6B", fontSize: 14, marginTop: -8 },
  slotBlock: { gap: 8, borderTopWidth: 1, borderTopColor: "#EEE", paddingTop: 10 },
  slotTitle: { fontSize: 18, fontWeight: "700", textTransform: "capitalize" },
  reconciledNote: { fontSize: 11, color: "#6B6B6B" },
  cardRow: { paddingRight: 12 },
  dishCard: {
    width: 180,
    marginRight: 12,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 10,
    padding: 10,
    gap: 8,
  },
  thumb: { width: "100%", height: 90, borderRadius: 8, backgroundColor: "#EEE" },
  thumbPlaceholder: { alignItems: "center", justifyContent: "center" },
  dishBody: { gap: 2 },
  dishName: { fontSize: 15, fontWeight: "600" },
  dishMeta: { color: "#6B6B6B", fontSize: 12 },
  error: { color: "#C0392B" },
});

import { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  fetchClassDishes,
  fetchSavedWeek,
  fetchSlotOptions,
  savedWeekLocks,
  savedWeekSelections,
  setPlanSlotLock,
} from "@/api/plan";
import { postFeedback } from "@/api/feedback";
import type { PlanDish } from "@/api/plan";
import type { FeedbackEventType } from "@/api/types";
import { loadWeeklyPlan, type FinalizedWeek, type SlotName } from "@/lib/weeklyPlanStore";
import { palette } from "@/ui/foofoo";
import { useI18n } from "@/i18n";
import { MealEpisodeSection } from "@/components/MealEpisodeSection";

const SLOTS: SlotName[] = ["breakfast", "lunch", "dinner"];
const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

function isoLocalDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function upcomingDates(): string[] {
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date();
    date.setHours(12, 0, 0, 0);
    date.setDate(date.getDate() + index);
    return isoLocalDate(date);
  });
}

export default function Home() {
  const { t } = useI18n();
  const dates = useRef(upcomingDates()).current;
  const today = dates[0];
  const [selectedDate, setSelectedDate] = useState(today);
  const [offlinePlan, setOfflinePlan] = useState<FinalizedWeek | null>(null);
  const [refreshNonce, setRefreshNonce] = useState(0);
  const weekday = WEEKDAYS[new Date(`${selectedDate}T12:00:00`).getDay()];
  const saved = useQuery({
    queryKey: ["saved-week", selectedDate],
    queryFn: () => fetchSavedWeek(selectedDate),
    staleTime: 0,
  });

  useEffect(() => {
    loadWeeklyPlan().then(setOfflinePlan).catch(() => setOfflinePlan(null));
  }, []);

  useFocusEffect(useCallback(() => {
    saved.refetch();
  }, [selectedDate]));

  const serverPlan = savedWeekSelections(saved.data);
  const plan = Object.keys(serverPlan).length > 0
    ? serverPlan
    : selectedDate === today ? offlinePlan : null;
  const locks = savedWeekLocks(saved.data);

  if (saved.isLoading && !offlinePlan) {
    return <View style={styles.center}><ActivityIndicator color={palette.purple} /></View>;
  }

  return (
    <View style={styles.screen} testID="home-screen">
      <ScrollView contentContainerStyle={styles.page} showsVerticalScrollIndicator={false}>
        <View style={styles.brandRow}><View><Text style={styles.brand}>FooFoo<Text style={styles.brandMark}>♡</Text></Text><Text style={styles.tagline}>AI Meal Decision Platform{`\n`}for your household</Text></View><Pressable onPress={() => router.push("/notifications")} style={styles.topIcon}><Text>♧</Text><View style={styles.dot} /></Pressable></View>
        <Text style={styles.greeting}>{t("greeting")}</Text><Text style={styles.question}>{t("question")}</Text>
        <View style={styles.insight}><Text style={styles.insightIcon}>✦</Text><Text style={styles.insightText}>{t("insight")}</Text></View>
        <View style={styles.sectionHead}><Text style={styles.sectionTitle}>{t("todayPlan")}</Text><Pressable onPress={() => router.push("/weekly-plan")}><Text style={styles.viewAll}>{t("viewAll")}  ›</Text></Pressable></View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.dateRow}>
          {dates.map((date) => {
            const active = date === selectedDate;
            const parsed = new Date(`${date}T12:00:00`);
            return <Pressable testID={`home-date-${date}`} key={date} accessibilityRole="button" accessibilityState={{ selected: active }} style={[styles.dateChip, active && styles.dateChipActive]} onPress={() => setSelectedDate(date)}><Text style={[styles.dateWeekday, active && styles.dateTextActive]}>{parsed.toLocaleDateString(undefined, { weekday: "short" })}</Text><Text style={[styles.dateDay, active && styles.dateTextActive]}>{parsed.getDate()}</Text></Pressable>;
          })}
        </ScrollView>
        <View style={styles.planActions}><Text style={styles.selectedDate}>{new Date(`${selectedDate}T12:00:00`).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}</Text><Pressable testID="home-refresh" style={styles.refreshButton} onPress={() => setRefreshNonce((value) => value + 1)}><Text style={styles.refreshText}>↻ Refresh</Text></Pressable></View>
        <View style={styles.episodeList}>
          {SLOTS.map((slot) => <MealEpisodeSection key={slot} slot={slot} weekday={weekday} slotDate={selectedDate} classCode={plan?.[weekday]?.[slot]} initiallyLocked={locks[weekday]?.[slot] === true} refreshNonce={refreshNonce} />)}
        </View>
      </ScrollView>
    </View>
  );
}

/** Compatibility surface for API-backed recommendation tests and progressive rollout. */
export function SlotSection({ slot, weekday, slotDate, classCode, initiallyLocked, refreshNonce }: { slot: SlotName; weekday: string; slotDate?: string; classCode?: string; initiallyLocked: boolean; refreshNonce: number }) {
  const [locked, setLocked] = useState(initiallyLocked);
  const [why, setWhy] = useState(false);
  const [sent, setSent] = useState<FeedbackEventType | null>(null);
  const query = useQuery({ queryKey: ["daily-plan", slotDate ?? weekday, classCode, refreshNonce], queryFn: () => classCode ? fetchClassDishes(slot, classCode, weekday, 8) : fetchSlotOptions(slot, { weekday, count: 8 }) });
  const lock = useMutation({ mutationFn: (value: boolean) => setPlanSlotLock(weekday, slot, value, slotDate), onSuccess: (_v, value) => setLocked(value) });
  const feedback = useMutation({ mutationFn: (event: FeedbackEventType) => postFeedback({ request_id: query.data?.request_id ?? "", event_type: event, dish_name: query.data?.options?.[0]?.name ?? "" }), onSuccess: (_v, event) => setSent(event) });
  const dish = query.data?.options?.[0] as PlanDish | undefined;
  return <View style={styles.legacy}><View style={styles.sectionHead}><Text style={styles.sectionTitle}>{slot}</Text><Pressable disabled={lock.isPending} onPress={() => lock.mutate(!locked)}><Text>{locked ? "Locked" : "Lock this meal"}</Text></Pressable></View>{dish ? <><Text style={styles.legacyDish}>{dish.name}</Text><Pressable onPress={() => setWhy(!why)}><Text style={styles.viewAll}>{why ? "Hide why" : "Why this?"}</Text></Pressable>{why ? <View><Text>Match score {dish.score.toFixed(2)}</Text>{(dish.explanation?.top_contributors ?? []).map((x) => <Text key={x.module}>{x.module.replace(/^m_/, "").replaceAll("_", " ")}: {x.weighted >= 0 ? "+" : ""}{x.weighted.toFixed(2)}</Text>)}</View> : null}<Pressable onPress={() => feedback.mutate("like")}><Text>{sent === "like" ? "Liked" : "Like"}</Text></Pressable></> : null}</View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.bg }, center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: palette.bg }, page: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 112 }, brandRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }, brand: { fontFamily: "Fraunces_600SemiBold", fontSize: 30, color: "#EC315A" }, brandMark: { fontSize: 17 }, tagline: { fontSize: 11, lineHeight: 15, color: palette.ink, marginTop: 3 }, topIcon: { width: 42, height: 42, borderRadius: 21, backgroundColor: "white", borderWidth: 1, borderColor: palette.line, alignItems: "center", justifyContent: "center" }, dot: { position: "absolute", right: 7, top: 6, width: 7, height: 7, borderRadius: 4, backgroundColor: palette.red }, greeting: { fontFamily: "Mukta_600SemiBold", fontSize: 22, color: palette.ink }, question: { color: palette.muted, fontSize: 15, marginTop: -2 }, insight: { flexDirection: "row", gap: 8, backgroundColor: palette.purpleSoft, borderRadius: 12, padding: 11, marginTop: 13, marginBottom: 4 }, insightIcon: { color: palette.purple }, insightText: { color: "#603190", flex: 1, fontSize: 12 }, sectionHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 22, marginBottom: 11 }, sectionTitle: { fontWeight: "800", color: palette.ink, fontSize: 18 }, viewAll: { color: palette.purple, fontWeight: "600", fontSize: 13 }, dateRow: { gap: 8, paddingBottom: 12 }, dateChip: { minWidth: 50, paddingVertical: 8, paddingHorizontal: 10, borderRadius: 12, alignItems: "center", backgroundColor: "white", borderWidth: 1, borderColor: palette.line }, dateChipActive: { backgroundColor: palette.purple, borderColor: palette.purple }, dateWeekday: { fontSize: 11, color: palette.muted }, dateDay: { fontSize: 16, fontWeight: "800", color: palette.ink, marginTop: 2 }, dateTextActive: { color: "white" }, planActions: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }, selectedDate: { color: palette.ink, fontWeight: "700", fontSize: 13 }, refreshButton: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 16, backgroundColor: palette.purpleSoft }, refreshText: { color: palette.purple, fontWeight: "700", fontSize: 12 }, episodeList: { gap: 20 }, legacy: { margin: 20, padding: 16, backgroundColor: "white", gap: 8 }, legacyDish: { fontSize: 16, fontWeight: "700" },
});

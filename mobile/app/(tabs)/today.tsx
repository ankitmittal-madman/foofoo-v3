import { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { fetchClassDishes, fetchSavedWeek, fetchSlotOptions, savedWeekLocks, savedWeekSelections, setPlanSlotLock } from "@/api/plan";
import { postFeedback } from "@/api/feedback";
import type { PlanDish } from "@/api/plan";
import type { FeedbackEventType } from "@/api/types";
import { loadWeeklyPlan, type FinalizedWeek, type SlotName } from "@/lib/weeklyPlanStore";
import { palette, SectionHeader } from "@/ui/foofoo";
import { useI18n } from "@/i18n";
import { MealEpisodeSection } from "@/components/MealEpisodeSection";

const SLOTS: SlotName[] = ["breakfast", "lunch", "dinner"];
const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const TIMES: Record<SlotName, string> = { breakfast: "7:30 AM", lunch: "1:30 PM", dinner: "8:00 PM" };

function isoLocalDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function Home() {
  const { t, locale } = useI18n();
  const today = useRef(isoLocalDate(new Date())).current;
  const [selectedDate, setSelectedDate] = useState(today);
  const weekday = WEEKDAYS[new Date(`${selectedDate}T12:00:00`).getDay()];
  const dates = Array.from({ length: 7 }, (_, offset) => {
    const date = new Date(`${today}T12:00:00`);
    date.setDate(date.getDate() + offset);
    return isoLocalDate(date);
  });
  const [offlinePlan, setOfflinePlan] = useState<FinalizedWeek | null>(null);
  const [refreshNonce, setRefreshNonce] = useState(0);
  const [servedBySlot, setServedBySlot] = useState<Partial<Record<SlotName, string[]>>>({});
  const saved = useQuery({ queryKey: ["saved-week", selectedDate], queryFn: () => fetchSavedWeek(selectedDate), staleTime: 0 });

  useEffect(() => { loadWeeklyPlan().then(setOfflinePlan).catch(() => setOfflinePlan(null)); }, []);
  useEffect(() => setServedBySlot({}), [selectedDate, refreshNonce]);
  useFocusEffect(useCallback(() => { saved.refetch(); }, [selectedDate]));

  const serverPlan = savedWeekSelections(saved.data);
  const plan = Object.keys(serverPlan).length > 0 ? serverPlan : offlinePlan;
  const locks = savedWeekLocks(saved.data);

  if (saved.isLoading && !offlinePlan) return <View style={styles.center}><ActivityIndicator color={palette.purple} /></View>;

  return <View style={styles.screen} testID="home-screen"><ScrollView contentContainerStyle={styles.page} showsVerticalScrollIndicator={false}>
    <View style={styles.brandRow}><View><Text style={styles.brand}>FooFoo<Text style={styles.brandMark}>♡</Text></Text><Text style={styles.tagline}>{t("brandTagline")}</Text></View><Pressable accessibilityRole="button" onPress={() => router.push("/notifications")} style={({ pressed }) => [styles.topIcon, pressed && styles.pressed]}><Text style={styles.bell}>♧</Text><View style={styles.dot} /></Pressable></View>
    <Text style={styles.greeting}>{t("greeting")}</Text><Text style={styles.question}>{t("question")}</Text><Text style={styles.household}>{t("householdContext")}</Text>
    <View style={styles.insight}><Text style={styles.insightIcon}>✦</Text><Text style={styles.insightText}>{t("insight")}</Text></View>
    <View style={styles.dateRow}><View><Text style={styles.todayLabel}>{t("todayPlan")}</Text><Text testID="home-selected-date" style={styles.todayDate}>{new Date(`${selectedDate}T12:00:00`).toLocaleDateString(locale === "hi" ? "hi-IN" : "en-IN", { weekday: "long", month: "long", day: "numeric" })}</Text></View><Pressable testID="home-refresh" style={styles.refreshButton} onPress={() => setRefreshNonce((value) => value + 1)}><Text style={styles.refreshText}>↻ {t("refresh")}</Text></Pressable></View>
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.datePicker}>{dates.map((date) => { const active = date === selectedDate; const parsed = new Date(`${date}T12:00:00`); return <Pressable key={date} testID={`home-date-${date}`} accessibilityRole="button" accessibilityState={{ selected: active }} onPress={() => setSelectedDate(date)} style={[styles.dateOption, active && styles.dateOptionActive]}><Text style={[styles.dateOptionDay, active && styles.dateOptionTextActive]}>{parsed.toLocaleDateString(locale === "hi" ? "hi-IN" : "en-IN", { weekday: "short" })}</Text><Text style={[styles.dateOptionNumber, active && styles.dateOptionTextActive]}>{parsed.getDate()}</Text></Pressable>; })}</ScrollView>
    <View style={styles.episodeList}>{SLOTS.map((slot, index) => {
      const earlierSlots = SLOTS.slice(0, index);
      const enabled = index === 0 || servedBySlot[SLOTS[index - 1]] !== undefined;
      const exclusions = earlierSlots.flatMap((earlier) => servedBySlot[earlier] ?? []);
      return <MealEpisodeSection
        key={`${selectedDate}-${slot}-${refreshNonce}`}
        slot={slot}
        weekday={weekday}
        slotDate={selectedDate}
        classCode={plan?.[weekday]?.[slot]}
        initiallyLocked={locks[weekday]?.[slot] === true}
        refreshNonce={refreshNonce}
        enabled={enabled}
        excludeDishNames={exclusions}
        onEpisodes={(names) => setServedBySlot((current) =>
          current[slot]?.join("\u0000") === names.join("\u0000")
            ? current
            : { ...current, [slot]: names }
        )}
      />;
    })}</View>
    <SectionHeader title={t("todayPlan")} action={t("viewAll")} onAction={() => router.push("/weekly-plan")} />
    <View style={styles.summaryRow}>{SLOTS.map((slot) => <View key={slot} style={styles.summary}><View style={styles.summaryIcon}><Text>{slot === "breakfast" ? "☀" : slot === "lunch" ? "◉" : "☾"}</Text></View><Text numberOfLines={1} style={styles.summaryTitle}>{t(slot)}</Text><Text style={styles.summaryTime}>{TIMES[slot]}</Text><View style={styles.readyDot} /></View>)}</View>
  </ScrollView></View>;
}

/** Compatibility surface retained for the existing scored-dish integration tests. */
export function SlotSection({ slot, weekday, slotDate, classCode, initiallyLocked, refreshNonce }: { slot: SlotName; weekday: string; slotDate?: string; classCode?: string; initiallyLocked: boolean; refreshNonce: number }) {
  const [locked, setLocked] = useState(initiallyLocked); const [why, setWhy] = useState(false); const [sent, setSent] = useState<FeedbackEventType | null>(null);
  const query = useQuery({ queryKey: ["daily-plan", slotDate ?? weekday, classCode, refreshNonce], queryFn: () => classCode ? fetchClassDishes(slot, classCode, weekday, 8) : fetchSlotOptions(slot, { weekday, count: 8 }) });
  const lock = useMutation({ mutationFn: (value: boolean) => setPlanSlotLock(weekday, slot, value, slotDate), onSuccess: (_v, value) => setLocked(value) });
  const feedback = useMutation({ mutationFn: (event: FeedbackEventType) => postFeedback({ request_id: query.data?.request_id ?? "", event_type: event, dish_name: query.data?.options?.[0]?.name ?? "" }), onSuccess: (_v, event) => setSent(event) });
  const dish = query.data?.options?.[0] as PlanDish | undefined;
  return <View style={styles.legacy}><View style={styles.legacyHead}><Text style={styles.legacyTitle}>{slot}</Text><Pressable disabled={lock.isPending} onPress={() => lock.mutate(!locked)}><Text>{locked ? "Locked" : "Lock this meal"}</Text></Pressable></View>{dish ? <><Text style={styles.legacyDish}>{dish.name}</Text><Pressable onPress={() => setWhy(!why)}><Text style={styles.link}>{why ? "Hide why" : "Why this?"}</Text></Pressable>{why ? <View><Text>Match score {dish.score.toFixed(2)}</Text>{(dish.explanation?.top_contributors ?? []).map((x) => <Text key={x.module}>{x.module.replace(/^m_/, "").replaceAll("_", " ")}: {x.weighted >= 0 ? "+" : ""}{x.weighted.toFixed(2)}</Text>)}</View> : null}<Pressable onPress={() => feedback.mutate("like")}><Text>{sent === "like" ? "Liked" : "Like"}</Text></Pressable></> : null}</View>;
}

const styles = StyleSheet.create({ screen: { flex: 1, backgroundColor: palette.bg }, center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: palette.bg }, page: { paddingHorizontal: 18, paddingTop: 16, paddingBottom: 110, gap: 14 }, brandRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 5 }, brand: { fontFamily: "Fraunces_600SemiBold", fontSize: 29, color: "#E73E65" }, brandMark: { fontSize: 16 }, tagline: { fontSize: 10, color: palette.muted, marginTop: 2 }, topIcon: { width: 44, height: 44, borderRadius: 22, backgroundColor: palette.surface, borderWidth: 1, borderColor: palette.line, alignItems: "center", justifyContent: "center" }, pressed: { opacity: .72, transform: [{ scale: .97 }] }, bell: { fontSize: 19 }, dot: { position: "absolute", right: 7, top: 6, width: 7, height: 7, borderRadius: 4, backgroundColor: palette.red }, greeting: { fontFamily: "Mukta_600SemiBold", fontSize: 23, color: palette.ink }, question: { color: palette.muted, fontSize: 15, marginTop: -12 }, household: { color: palette.purple, fontSize: 11, fontWeight: "700", marginTop: -8 }, insight: { flexDirection: "row", gap: 8, backgroundColor: palette.purpleSoft, borderRadius: 13, padding: 12, alignItems: "center" }, insightIcon: { color: palette.purple }, insightText: { color: "#5B3AB8", flex: 1, fontSize: 12, lineHeight: 17 }, dateRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 1 }, todayLabel: { fontSize: 19, fontWeight: "800", color: palette.ink }, todayDate: { color: palette.muted, fontSize: 11, marginTop: 2 }, datePicker: { gap: 8, paddingRight: 6 }, dateOption: { width: 52, minHeight: 58, alignItems: "center", justifyContent: "center", borderRadius: 13, borderWidth: 1, borderColor: palette.line, backgroundColor: palette.surface }, dateOptionActive: { borderColor: palette.purple, backgroundColor: palette.purple }, dateOptionDay: { color: palette.muted, fontSize: 10, fontWeight: "600" }, dateOptionNumber: { color: palette.ink, fontSize: 16, fontWeight: "800", marginTop: 3 }, dateOptionTextActive: { color: "white" }, refreshButton: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: palette.purpleSoft, minHeight: 36, justifyContent: "center" }, refreshText: { color: palette.purple, fontWeight: "700", fontSize: 11 }, episodeList: { gap: 22 }, summaryRow: { flexDirection: "row", gap: 8 }, summary: { flex: 1, minWidth: 0, alignItems: "center", backgroundColor: palette.surface, borderWidth: 1, borderColor: palette.line, borderRadius: 15, paddingVertical: 12, paddingHorizontal: 5 }, summaryIcon: { width: 38, height: 38, borderRadius: 19, backgroundColor: palette.beige, alignItems: "center", justifyContent: "center" }, summaryTitle: { fontWeight: "700", color: palette.ink, fontSize: 11, marginTop: 7, maxWidth: "100%" }, summaryTime: { color: palette.muted, fontSize: 9, marginTop: 3 }, readyDot: { position: "absolute", right: 7, top: 7, width: 7, height: 7, borderRadius: 4, backgroundColor: palette.green }, legacy: { margin: 20, padding: 16, backgroundColor: "white", gap: 8 }, legacyHead: { flexDirection: "row", justifyContent: "space-between" }, legacyTitle: { fontWeight: "800", textTransform: "capitalize" }, legacyDish: { fontSize: 16, fontWeight: "700" }, link: { color: palette.purple, fontWeight: "600", fontSize: 13 } });

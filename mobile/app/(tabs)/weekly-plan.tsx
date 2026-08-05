import { useEffect, useState } from "react";
import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { describeApiError } from "@/api/errorMessages";
import { fetchSavedWeek, fetchWeeklyPlan, savedWeekSelections, saveWeekPlan } from "@/api/plan";
import type { WeeklyClass, WeeklyPlanResponse } from "@/api/plan";
import { useI18n } from "@/i18n";
import { saveWeeklyPlan, type FinalizedWeek, type SlotName } from "@/lib/weeklyPlanStore";
import { palette } from "@/ui/foofoo";

const FOOD = require("../../assets/images/poha-idli-fruit.png");
const SLOTS: SlotName[] = ["breakfast", "lunch", "dinner"];

/** Server-authoritative weekly class planner presented in the polished FooFoo card system. */
export default function WeeklyPlan() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const query = useQuery<WeeklyPlanResponse>({ queryKey: ["weekly-plan"], queryFn: () => fetchWeeklyPlan(3) });
  const saved = useQuery({ queryKey: ["saved-week"], queryFn: () => fetchSavedWeek() });
  const [selected, setSelected] = useState<FinalizedWeek>({});

  useEffect(() => {
    if (saved.data?.plan) setSelected(savedWeekSelections(saved.data));
  }, [saved.data]);

  const finalize = useMutation({
    mutationFn: async (plan: FinalizedWeek) => {
      await saveWeekPlan(plan, true);
      await saveWeeklyPlan(plan);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["saved-week"] }),
        queryClient.invalidateQueries({ queryKey: ["daily-plan"] }),
        queryClient.invalidateQueries({ queryKey: ["meal-episodes"] }),
      ]);
    },
    onSuccess: () => router.replace("/today"),
  });

  function choose(weekday: string, slot: SlotName, classCode: string) {
    setSelected((current) => ({ ...current, [weekday]: { ...current[weekday], [slot]: classCode } }));
  }

  if (query.isLoading) return <View style={styles.center}><ActivityIndicator color={palette.purple} /></View>;
  if (query.isError) return <View style={styles.center}><Text style={styles.error}>{describeApiError(query.error)}</Text><Pressable style={styles.retry} onPress={() => query.refetch()}><Text style={styles.retryText}>Retry</Text></Pressable></View>;

  const days = query.data?.days ?? [];
  const totalSlots = days.length * SLOTS.length;
  const chosenCount = Object.values(selected).reduce((count, slots) => count + Object.keys(slots).length, 0);

  return (
    <View style={styles.screen} testID="weekly-plan-screen">
      <ScrollView contentContainerStyle={styles.page} showsVerticalScrollIndicator={false}>
        <View style={styles.header}><Pressable onPress={() => router.back()}><Text style={styles.back}>‹</Text></Pressable><View><Text style={styles.title}>{t("weeklyTitle")}</Text><Text style={styles.subtitle}>Choose one real meal class for every household meal.</Text></View><View style={styles.headerSpacer} /></View>
        <View style={styles.progress}><View style={[styles.progressFill, { width: `${totalSlots ? (chosenCount / totalSlots) * 100 : 0}%` }]} /></View>
        <Text style={styles.progressText}>{chosenCount} of {totalSlots} meals selected</Text>
        {days.map((day) => (
          <View key={day.weekday} style={styles.dayCard}>
            <Text style={styles.dayTitle}>{day.weekday}</Text>
            {SLOTS.map((slot) => (
              <View key={slot} style={styles.group}>
                <View style={styles.groupHead}><Text style={styles.groupTitle}>{t(slot)}</Text><Text style={styles.intent}>Ranked for your household</Text></View>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.options}>
                  {(day.slots[slot] ?? []).map((mealClass: WeeklyClass, index: number) => {
                    const isSelected = selected[day.weekday]?.[slot] === mealClass.class_code;
                    return (
                      <Pressable testID={`weekly-plan-${day.weekday}-${slot}-${index}`} key={mealClass.class_code} style={[styles.option, isSelected && styles.optionActive]} onPress={() => choose(day.weekday, slot, mealClass.class_code)}>
                        <View><Image source={FOOD} style={styles.food} /><View style={[styles.number, isSelected && styles.numberActive]}><Text style={styles.numberText}>{index + 1}</Text></View>{isSelected ? <View style={styles.check}><Text style={styles.checkText}>✓</Text></View> : null}</View>
                        <Text numberOfLines={3} style={styles.optionName}>{mealClass.class_name}</Text>
                        <Text style={styles.optionMeta}>{mealClass.dish_count} dishes</Text>
                      </Pressable>
                    );
                  })}
                  {(day.slots[slot] ?? []).length === 0 ? <Text style={styles.empty}>No safe class is available for this slot.</Text> : null}
                </ScrollView>
              </View>
            ))}
          </View>
        ))}
        <Pressable testID="weekly-plan-finalize" accessibilityRole="button" disabled={chosenCount !== totalSlots || finalize.isPending} style={[styles.finalize, chosenCount !== totalSlots && styles.disabled]} onPress={() => finalize.mutate(selected)}><Text style={styles.finalizeText}>{finalize.isPending ? "Saving…" : `Finalize plan (${chosenCount}/${totalSlots})`}</Text></Pressable>
        {finalize.isError ? <Text style={styles.error}>Couldn't save your plan. Please try again.</Text> : null}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.bg }, page: { padding: 18, paddingBottom: 112 }, center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 12, backgroundColor: palette.bg }, header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 15 }, back: { fontSize: 34, color: palette.ink }, title: { fontFamily: "Fraunces_600SemiBold", fontSize: 22, color: palette.ink, textAlign: "center" }, subtitle: { color: palette.muted, fontSize: 12, marginTop: 2, textAlign: "center" }, headerSpacer: { width: 20 }, progress: { height: 6, borderRadius: 3, backgroundColor: palette.line, overflow: "hidden" }, progressFill: { height: "100%", backgroundColor: palette.purple }, progressText: { color: palette.muted, fontSize: 11, textAlign: "right", marginTop: 5, marginBottom: 12 }, dayCard: { backgroundColor: "white", borderWidth: 1, borderColor: palette.line, borderRadius: 18, padding: 14, marginBottom: 14 }, dayTitle: { fontSize: 18, fontWeight: "800", color: palette.ink, marginBottom: 2 }, group: { paddingVertical: 11, borderTopWidth: 1, borderTopColor: palette.line }, groupHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 9 }, groupTitle: { fontSize: 14, fontWeight: "800", color: palette.ink, textTransform: "capitalize" }, intent: { fontSize: 10, color: palette.muted }, options: { gap: 9, paddingRight: 8 }, option: { width: 112, padding: 6, borderRadius: 12, borderWidth: 1, borderColor: "transparent", backgroundColor: palette.beige }, optionActive: { borderColor: palette.green, backgroundColor: "#F7FFF9" }, food: { width: 98, height: 66, borderRadius: 9 }, number: { position: "absolute", left: 3, top: 3, width: 18, height: 18, borderRadius: 9, alignItems: "center", justifyContent: "center", backgroundColor: "#2B2926" }, numberActive: { backgroundColor: palette.green }, numberText: { color: "white", fontSize: 10, fontWeight: "800" }, check: { position: "absolute", right: 3, top: 3, width: 18, height: 18, borderRadius: 9, backgroundColor: palette.green, alignItems: "center", justifyContent: "center" }, checkText: { color: "white", fontSize: 11 }, optionName: { textAlign: "center", fontSize: 10, lineHeight: 13, color: palette.ink, marginTop: 5, fontWeight: "600" }, optionMeta: { textAlign: "center", color: palette.muted, fontSize: 9, marginTop: 3 }, empty: { color: palette.amber, fontSize: 12, paddingVertical: 8 }, finalize: { minHeight: 50, borderRadius: 13, alignItems: "center", justifyContent: "center", backgroundColor: palette.purple, marginTop: 4 }, finalizeText: { color: "white", fontWeight: "800", fontSize: 15 }, disabled: { opacity: 0.45 }, retry: { backgroundColor: palette.purple, borderRadius: 12, paddingVertical: 10, paddingHorizontal: 18 }, retryText: { color: "white", fontWeight: "700" }, error: { color: palette.red, textAlign: "center" },
});

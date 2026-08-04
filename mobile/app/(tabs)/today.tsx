import { useEffect, useState } from "react";
import { View, Text, ScrollView, ActivityIndicator, Pressable, StyleSheet, Image } from "react-native";
import { useMutation, useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import {
  fetchClassDishes,
  fetchSavedWeek,
  fetchSlotOptions,
  savedWeekLocks,
  savedWeekSelections,
  setPlanSlotLock,
} from "@/api/plan";
import { postFeedback } from "@/api/feedback";
import { describeApiError } from "@/api/errorMessages";
import { loadWeeklyPlan, type FinalizedWeek, type SlotName } from "@/lib/weeklyPlanStore";
import type { PlanAddon, PlanDish } from "@/api/plan";
import type { FeedbackEventType } from "@/api/types";

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
  const [locks, setLocks] = useState<Record<string, Partial<Record<SlotName, boolean>>>>({});
  const [planLoaded, setPlanLoaded] = useState(false);
  const [refreshNonce, setRefreshNonce] = useState(0);

  useEffect(() => {
    fetchSavedWeek()
      .then((response) => {
        setLocks(savedWeekLocks(response));
        const serverPlan = savedWeekSelections(response);
        if (Object.keys(serverPlan).length > 0) return serverPlan;
        return loadWeeklyPlan();
      })
      .catch(() => loadWeeklyPlan())
      .then((p) => setPlan(p))
      .finally(() => setPlanLoaded(true));
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
      <Pressable style={styles.refreshButton} onPress={() => setRefreshNonce((value) => value + 1)}>
        <Text style={styles.refreshButtonText}>Refresh unlocked meals</Text>
      </Pressable>
      {SLOTS.map((slot) => (
        <SlotSection
          key={slot}
          slot={slot}
          weekday={weekday}
          classCode={plan?.[weekday]?.[slot]}
          initiallyLocked={locks[weekday]?.[slot] === true}
          refreshNonce={refreshNonce}
        />
      ))}
    </ScrollView>
  );
}

export function SlotSection({
  slot,
  weekday,
  classCode,
  initiallyLocked,
  refreshNonce,
}: {
  slot: SlotName;
  weekday: string;
  classCode?: string;
  initiallyLocked: boolean;
  refreshNonce: number;
}) {
  const [locked, setLocked] = useState(initiallyLocked);
  const query = useQuery({
    queryKey: ["daily-plan", slot, weekday, classCode ?? null],
    queryFn: () =>
      classCode
        ? fetchClassDishes(slot, classCode, weekday, 8)
        : fetchSlotOptions(slot, { weekday, count: 8 }),
  });
  const lock = useMutation({
    mutationFn: (nextLocked: boolean) => setPlanSlotLock(weekday, slot, nextLocked),
    onSuccess: (_data, nextLocked) => setLocked(nextLocked),
  });

  useEffect(() => setLocked(initiallyLocked), [initiallyLocked]);
  useEffect(() => {
    if (refreshNonce > 0 && !locked) query.refetch();
  }, [refreshNonce]); // locked/query are deliberately sampled when the user requests refresh.

  return (
    <View style={styles.slotBlock}>
      <Text style={styles.slotTitle}>{slot}</Text>
      <Pressable
        disabled={lock.isPending || !classCode}
        onPress={() => lock.mutate(!locked)}
        style={[styles.feedbackButton, locked && styles.feedbackButtonActive, !classCode && styles.buttonDisabled]}
      >
        <Text style={styles.feedbackButtonText}>{locked ? "Locked" : "Lock this meal"}</Text>
      </Pressable>
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
        <>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.cardRow}>
            {(query.data?.options ?? []).map((d: PlanDish) => (
              <DishCard key={d.name} dish={d} requestId={query.data?.request_id} slot={slot} />
            ))}
          </ScrollView>
          {(query.data?.addons ?? []).map((addon: PlanAddon) => (
            <View key={`${addon.member_index}-${addon.class_code}`} style={styles.addonRow}>
              <Text style={styles.addonLabel}>{addon.member_role.replace("_", " ")} add-on</Text>
              <Text>{addon.dish.name}</Text>
            </View>
          ))}
        </>
      )}
    </View>
  );
}

/**
 * One dish card on the Home tab (P0-4/P1-2, 2026-08): like/dislike feedback + a minimal "why
 * this?" explanation. Feedback resolves against the recommendation_events row plan/handler.ts now
 * writes for meal_plan/class_dishes (previously only cold_start/calibration wrote one, so a tap
 * here had nothing to record against). The explanation is deliberately minimal — this surface's
 * PlanDish only carries a single numeric `score`, not the BASE/Q15/weather contribution breakdown
 * ghar_re_core.scoring.explain_dish() can produce; showing the real score plus the two tags that
 * drove the class match (meal_class_name/cuisine) is honest given what this endpoint returns,
 * rather than fabricating a richer breakdown the API doesn't supply.
 */
function DishCard({ dish, requestId, slot }: {
  dish: PlanDish; requestId?: string; slot: SlotName;
}) {
  const [sent, setSent] = useState<FeedbackEventType | null>(null);
  const [showWhy, setShowWhy] = useState(false);
  const feedback = useMutation({
    mutationFn: (eventType: FeedbackEventType) => {
      if (!requestId) return Promise.reject(new Error("no request_id on this response"));
      return postFeedback({ request_id: requestId, event_type: eventType, dish_name: dish.name });
    },
    onSuccess: (_data, eventType) => setSent(eventType),
  });

  return (
    <View style={styles.dishCard}>
      <Pressable
        onPress={() => router.push({ pathname: "/recipe/[dish]", params: { dish: dish.name } })}
      >
        {dish.image_url ? (
          <Image source={{ uri: dish.image_url }} style={styles.thumb} />
        ) : (
          <View style={[styles.thumb, styles.thumbPlaceholder]} />
        )}
        <View style={styles.dishBody}>
          <Text style={styles.dishName}>{dish.name}</Text>
          <Text style={styles.dishMeta}>{dish.meal_class_name ?? dish.cuisine}</Text>
        </View>
      </Pressable>
      <Pressable onPress={() => setShowWhy((v) => !v)}>
        <Text style={styles.whyLink}>{showWhy ? "Hide why" : "Why this?"}</Text>
      </Pressable>
      {showWhy ? (
        <View style={styles.explanationBlock}>
          <Text style={styles.whyText}>
            Match score {dish.score.toFixed(2)} — {dish.cuisine} cuisine
            {dish.meal_class_name ? `, ${dish.meal_class_name} class` : ""}.
          </Text>
          {(dish.explanation?.top_contributors ?? []).map((item) => (
            <Text key={item.module} style={styles.contributionText}>
              {item.module.replace(/^m_/, "").replaceAll("_", " ")}: {item.weighted >= 0 ? "+" : ""}{item.weighted.toFixed(2)}
            </Text>
          ))}
          {dish.explanation?.weather_contribution ? (
            <Text style={styles.contributionText}>Weather match: {dish.explanation.weather_contribution.toFixed(2)}</Text>
          ) : null}
        </View>
      ) : null}
      <View style={styles.feedbackRow}>
        <Pressable
          disabled={feedback.isPending || !requestId}
          onPress={() => feedback.mutate("like")}
          style={[styles.feedbackButton, sent === "like" && styles.feedbackButtonActive]}
        >
          <Text style={styles.feedbackButtonText}>{sent === "like" ? "Liked" : "Like"}</Text>
        </Pressable>
        <Pressable
          disabled={feedback.isPending || !requestId}
          onPress={() => feedback.mutate("dislike")}
          style={[styles.feedbackButton, sent === "dislike" && styles.feedbackButtonActive]}
        >
          <Text style={styles.feedbackButtonText}>
            {sent === "dislike" ? "Not for me ✓" : "Not for me"}
          </Text>
        </Pressable>
      </View>
      <View style={styles.feedbackRow}>
        <Pressable disabled={feedback.isPending || !requestId}
          onPress={() => feedback.mutate("not_today")} style={styles.feedbackButton}>
          <Text style={styles.feedbackButtonText}>Not today</Text>
        </Pressable>
        <Pressable disabled={feedback.isPending || !requestId}
          onPress={() => feedback.mutate("never")} style={styles.feedbackButton}>
          <Text style={styles.feedbackButtonText}>Never</Text>
        </Pressable>
      </View>
      {dish.meal_class_code ? (
        <Pressable onPress={() => router.push({
          pathname: "/add-to-date",
          params: { dish: dish.name, classCode: dish.meal_class_code, slot },
        })} style={styles.feedbackButton}>
          <Text style={styles.feedbackButtonText}>Add to date</Text>
        </Pressable>
      ) : null}
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
  whyLink: { fontSize: 11, color: "#4A6FA5", marginTop: 6 },
  whyText: { fontSize: 11, color: "#6B6B6B", marginTop: 4 },
  feedbackRow: { flexDirection: "row", gap: 8, marginTop: 8 },
  feedbackButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 6,
    paddingVertical: 6,
    alignItems: "center",
  },
  feedbackButtonActive: { borderColor: "#4A6FA5", backgroundColor: "#EEF3FA" },
  feedbackButtonText: { fontSize: 12, fontWeight: "600" },
  buttonDisabled: { opacity: 0.45 },
  refreshButton: { alignSelf: "flex-start", borderWidth: 1, borderColor: "#1F7A3F", borderRadius: 8, padding: 10 },
  refreshButtonText: { color: "#1F7A3F", fontWeight: "600" },
  explanationBlock: { gap: 2 },
  contributionText: { fontSize: 11, color: "#555", textTransform: "capitalize" },
  addonRow: { borderLeftWidth: 3, borderLeftColor: "#4A6FA5", paddingLeft: 10, paddingVertical: 6 },
  addonLabel: { fontSize: 11, color: "#4A6FA5", textTransform: "capitalize" },
});

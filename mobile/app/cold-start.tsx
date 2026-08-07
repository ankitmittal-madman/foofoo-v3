/**
 * WP-18 dish-pick calibration grid — post-onboarding "Select what you like" screen. Ported from
 * scareme21-create/NewFoo's onboarding/final-dish.tsx UI/UX ("Onboarding Style 1": a 3-slot x
 * 5-dish grid), rebuilt on this repo's own conventions (React Query for server state, useTheme()
 * tokens, existing feedback/plan API shapes) rather than copied verbatim.
 *
 * Each slot's 5 dishes come from POST /v1/calibration (ghar_re_core.calibration.calibration_grid):
 * 3 engine-predicted expected-positives + 2 safe, plausible lower-middle-ranked challengers —
 * mixed and order-shuffled so which is which is never
 * positionally guessable. `cell_role` rides along in the payload purely so a "like" can carry it
 * back to /v1/feedback; this screen never reads or renders it.
 */
import { useState } from "react";
import { View, Text, ScrollView, ActivityIndicator, Pressable, StyleSheet, Image } from "react-native";
import { useMutation, useQuery } from "@tanstack/react-query";
import { router } from "expo-router";

import { useTheme } from "@/theme";
import { fetchCalibrationGrid } from "@/api/plan";
import { postFeedback } from "@/api/feedback";
import { describeApiError } from "@/api/errorMessages";
import type { CalibrationResponse, PlanDish, Slot } from "@/api/plan";

const SLOTS: { key: Slot; label: string }[] = [
  { key: "breakfast", label: "Breakfast" },
  { key: "lunch", label: "Lunch" },
  { key: "dinner", label: "Dinner" },
];

export default function ColdStart() {
  const t = useTheme();
  const [liked, setLiked] = useState<Set<string>>(new Set());
  const query = useQuery<CalibrationResponse>({
    queryKey: ["calibration-grid"],
    queryFn: fetchCalibrationGrid,
  });

  const feedback = useMutation({
    mutationFn: (args: { dish: PlanDish; slot: Slot }) => {
      const requestId = query.data?.request_id;
      if (!requestId) return Promise.reject(new Error("no request_id on this calibration response"));
      return postFeedback({
        request_id: requestId,
        event_type: "like",
        dish_name: args.dish.name,
        slot: args.slot,
        detail: { cell_role: args.dish.cell_role, tapped: true },
      });
    },
  });

  function toggleLike(dish: PlanDish, slot: Slot) {
    const key = `${slot}:${dish.name}`;
    setLiked((prev) => {
      const next = new Set(prev);
      const wasLiked = next.has(key);
      if (wasLiked) next.delete(key);
      else next.add(key);
      if (!wasLiked) feedback.mutate({ dish, slot });
      return next;
    });
  }

  if (query.isLoading) {
    return (
      <View style={[styles.center, { backgroundColor: t.colors.background }]}>
        <ActivityIndicator color={t.colors.primary} />
      </View>
    );
  }

  if (query.isError) {
    return (
      <View style={[styles.center, { backgroundColor: t.colors.background }]}>
        <Text style={[styles.error, { color: t.colors.primary }]}>{describeApiError(query.error)}</Text>
        <Pressable
          style={[styles.button, { backgroundColor: t.colors.selected }]}
          onPress={() => query.refetch()}
        >
          <Text style={[styles.buttonText, { color: t.colors.onSelected }]}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  const slots = query.data?.slots;
  const count = liked.size;

  return (
    <View testID="cold-start-screen" style={[styles.root, { backgroundColor: t.colors.background }]}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={[styles.header, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>
          Select what you like
        </Text>
        <Text style={[styles.subheader, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>
          Tap the dishes that sound good — this helps us build your weekly plan.
        </Text>

        <View style={styles.grid}>
          {SLOTS.map(({ key, label }) => (
            <View key={key} style={styles.column}>
              <View style={[styles.slotPill, { backgroundColor: t.colors.surfaceMuted }]}>
                <Text style={[styles.slotLabel, { color: t.colors.text, fontFamily: t.fonts.bodySemiBold }]}>
                  {label}
                </Text>
              </View>
              {(slots?.[key] ?? []).map((dish: PlanDish, index: number) => (
                <DishCard
                  key={dish.name}
                  dish={dish}
                  liked={liked.has(`${key}:${dish.name}`)}
                  onToggle={() => toggleLike(dish, key)}
                  testID={`cold-start-${key}-dish-${index}`}
                  t={t}
                />
              ))}
            </View>
          ))}
        </View>
      </ScrollView>

      <View style={[styles.footer, { backgroundColor: t.colors.background, borderTopColor: t.colors.border }]}>
        <Text style={[styles.count, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>
          {count > 0 ? `${count} selected` : "No problem — skip is always fine"}
        </Text>
        <Pressable
          testID="cold-start-finish"
          style={[styles.button, { backgroundColor: t.colors.selected }]}
          onPress={() => router.push("/weekly-plan")}
        >
          <Text style={[styles.buttonText, { color: t.colors.onSelected }]}>
            {count > 0 ? "Finish →" : "Skip →"}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

function DishCard({
  dish,
  liked,
  onToggle,
  testID,
  t,
}: {
  dish: PlanDish;
  liked: boolean;
  onToggle: () => void;
  testID: string;
  t: ReturnType<typeof useTheme>;
}) {
  return (
    <Pressable testID={testID} style={styles.card} onPress={onToggle}>
      <View style={[styles.imageWrap, { backgroundColor: t.colors.surfaceMuted }]}>
        {dish.image_url ? (
          <Image source={{ uri: dish.image_url }} style={styles.image} />
        ) : (
          <View style={styles.image} />
        )}
        <Text style={styles.heart}>{liked ? "♥" : "♡"}</Text>
      </View>
      <Text
        style={[styles.dishName, { color: t.colors.text, fontFamily: t.fonts.bodyMedium }]}
        numberOfLines={2}
      >
        {dish.name}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 12 },
  scroll: { padding: 16, paddingBottom: 8 },
  header: { fontSize: 24, marginBottom: 4 },
  subheader: { fontSize: 13, marginBottom: 16 },
  grid: { flexDirection: "row", gap: 8 },
  column: { flex: 1, gap: 8 },
  slotPill: { borderRadius: 16, paddingVertical: 6, alignItems: "center", marginBottom: 4 },
  slotLabel: { fontSize: 12 },
  card: { gap: 4 },
  imageWrap: { aspectRatio: 1, borderRadius: 12, overflow: "hidden", position: "relative" },
  image: { width: "100%", height: "100%" },
  heart: { position: "absolute", top: 6, right: 6, fontSize: 18, color: "#FFFFFF" },
  dishName: { fontSize: 11, textAlign: "center" },
  footer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  count: { fontSize: 13, flexShrink: 1, marginRight: 12 },
  button: { borderRadius: 24, paddingVertical: 12, paddingHorizontal: 24 },
  buttonText: { fontWeight: "600" },
  error: { textAlign: "center" },
});

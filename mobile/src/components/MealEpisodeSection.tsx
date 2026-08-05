import { useEffect, useState } from "react";
import { ActivityIndicator, Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useMutation, useQuery } from "@tanstack/react-query";
import { router } from "expo-router";

import { describeApiError } from "@/api/errorMessages";
import { postFeedback } from "@/api/feedback";
import { fetchMealEpisodes, setPlanSlotLock } from "@/api/plan";
import type { MealEpisode, Slot } from "@/api/plan";
import type { FeedbackEventType } from "@/api/types";

interface Props {
  slot: Slot;
  weekday: string;
  slotDate: string;
  classCode?: string;
  initiallyLocked: boolean;
  refreshNonce: number;
}

/** The PRD's atomic recommendation surface: one complete meal, with bounded alternatives. */
export function MealEpisodeSection({
  slot,
  weekday,
  slotDate,
  classCode,
  initiallyLocked,
  refreshNonce,
}: Props) {
  const [locked, setLocked] = useState(initiallyLocked);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const effectiveRefresh = locked ? 0 : refreshNonce;
  const query = useQuery({
    queryKey: ["meal-episodes", slotDate, classCode ?? null, effectiveRefresh],
    queryFn: () => fetchMealEpisodes(slot, {
      weekday,
      class_code: classCode,
      count: 4,
    }),
  });
  const lock = useMutation({
    mutationFn: (nextLocked: boolean) => setPlanSlotLock(weekday, slot, nextLocked, slotDate),
    onSuccess: (_data, nextLocked) => setLocked(nextLocked),
  });

  useEffect(() => setLocked(initiallyLocked), [initiallyLocked]);

  if (query.isLoading) {
    return <View style={styles.section}><Text style={styles.slot}>{slot}</Text><ActivityIndicator /></View>;
  }
  if (query.isError) {
    return (
      <View style={styles.section}>
        <Text style={styles.slot}>{slot}</Text>
        <Text style={styles.error}>{describeApiError(query.error)}</Text>
        <Pressable style={styles.secondaryButton} onPress={() => query.refetch()}>
          <Text style={styles.secondaryText}>Try again</Text>
        </Pressable>
      </View>
    );
  }

  const episodes = query.data?.episodes ?? [];
  const primary = episodes[0];
  return (
    <View style={styles.section} testID={`episode-section-${slot}`}>
      <View style={styles.slotHeader}>
        <Text style={styles.slot}>{slot}</Text>
        <Text style={styles.confidence}>
          {primary?.predictions.calibration_status === "calibrated" ? "Strong fit" : "Safe starting point"}
        </Text>
      </View>
      {primary ? (
        <>
          <EpisodeCard
            episode={primary}
            requestId={query.data?.request_id}
            slot={slot}
            onMakeThis={() => {
              if (classCode && !locked) lock.mutate(true);
            }}
            onReasonedReplacement={() => query.refetch()}
          />
          <View style={styles.actionRow}>
            <Pressable
              style={styles.primaryButton}
              onPress={() => setShowAlternatives((value) => !value)}
              accessibilityRole="button"
            >
              <Text style={styles.primaryText}>
                {showAlternatives ? "Hide alternatives" : `Show ${Math.min(3, episodes.length - 1)} alternatives`}
              </Text>
            </Pressable>
            {classCode ? (
              <Pressable
                style={[styles.secondaryButton, locked && styles.locked]}
                disabled={lock.isPending}
                onPress={() => lock.mutate(!locked)}
              >
                <Text style={styles.secondaryText}>{locked ? "Locked" : "Lock"}</Text>
              </Pressable>
            ) : null}
          </View>
          {showAlternatives
            ? episodes.slice(1, 4).map((episode) => (
              <EpisodeCard
                compact
                key={episode.episode_hash}
                episode={episode}
                requestId={query.data?.request_id}
                slot={slot}
                onReasonedReplacement={() => query.refetch()}
              />
            ))
            : null}
        </>
      ) : <Text style={styles.error}>No safe complete meal is available for this slot.</Text>}
    </View>
  );
}

function EpisodeCard({
  episode,
  requestId,
  slot,
  compact = false,
  onMakeThis,
  onReasonedReplacement,
}: {
  episode: MealEpisode;
  requestId?: string;
  slot: Slot;
  compact?: boolean;
  onMakeThis?: () => void;
  onReasonedReplacement: () => void;
}) {
  const [askReason, setAskReason] = useState(false);
  const primaryDish = episode.components.find((component) => component.dish_id !== null);
  const feedback = useMutation({
    mutationFn: (input: { eventType: FeedbackEventType; detail?: Record<string, unknown> }) => {
      if (!requestId) return Promise.reject(new Error("no request_id on this episode slate"));
      return postFeedback({
        request_id: requestId,
        event_type: input.eventType,
        dish_name: primaryDish?.dish_name,
        slot,
        detail: { episode_hash: episode.episode_hash, ...input.detail },
      });
    },
  });

  function replace(eventType: FeedbackEventType) {
    feedback.mutate({ eventType }, { onSuccess: onReasonedReplacement });
  }

  return (
    <View style={[styles.card, compact && styles.compactCard]}>
      {primaryDish?.image_url ? <Image source={{ uri: primaryDish.image_url }} style={styles.image} /> : null}
      <Text style={styles.intent}>{episode.intent.replaceAll("_", " ")}</Text>
      <Text style={styles.mealName}>{episode.display_name}</Text>
      <Text style={styles.components}>
        {episode.components.map((component) => component.dish_name).join(" + ")}
      </Text>
      <Text style={styles.practicality}>
        {episode.practicality.active_minutes} active min · {episode.practicality.burner_peak} burner
        {episode.practicality.burner_peak === 1 ? "" : "s"} · {episode.practicality.vessel_count} vessels
      </Text>
      {episode.reasons.slice(0, compact ? 1 : 3).map((reason) => (
        <Text key={reason} style={styles.reason}>• {reason}</Text>
      ))}
      {!compact ? (
        <View style={styles.actionRow}>
          <Pressable
            style={styles.primaryButton}
            disabled={feedback.isPending || !requestId}
            onPress={() => feedback.mutate({ eventType: "make_this" }, { onSuccess: onMakeThis })}
          >
            <Text style={styles.primaryText}>Make this</Text>
          </Pressable>
          <Pressable style={styles.secondaryButton} onPress={() => setAskReason((value) => !value)}>
            <Text style={styles.secondaryText}>Not today</Text>
          </Pressable>
        </View>
      ) : null}
      {askReason ? (
        <View style={styles.reasonRow}>
          <Pressable style={styles.reasonButton} onPress={() => replace("too_much_work")}>
            <Text style={styles.reasonButtonText}>Too much work</Text>
          </Pressable>
          <Pressable style={styles.reasonButton} onPress={() => replace("missing_ingredient")}>
            <Text style={styles.reasonButtonText}>Missing item</Text>
          </Pressable>
          <Pressable style={styles.reasonButton} onPress={() => replace("member_objection")}>
            <Text style={styles.reasonButtonText}>Member objected</Text>
          </Pressable>
          <Pressable style={styles.reasonButton} onPress={() => replace("not_today")}>
            <Text style={styles.reasonButtonText}>Different mood</Text>
          </Pressable>
        </View>
      ) : null}
      {primaryDish ? (
        <Pressable onPress={() => router.push({ pathname: "/recipe/[dish]", params: { dish: primaryDish.dish_name } })}>
          <Text style={styles.recipeLink}>View cooking details</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: 10, borderTopWidth: 1, borderTopColor: "#E9E4D8", paddingTop: 14 },
  slotHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  slot: { fontSize: 19, fontWeight: "700", textTransform: "capitalize" },
  confidence: { color: "#5C6B55", fontSize: 12 },
  card: { borderWidth: 1, borderColor: "#DED8CB", borderRadius: 14, padding: 14, gap: 7, backgroundColor: "#FFFCF5" },
  compactCard: { backgroundColor: "white", padding: 11 },
  image: { width: "100%", height: 130, borderRadius: 10, backgroundColor: "#EEE" },
  intent: { color: "#8A5A21", fontSize: 12, fontWeight: "700", textTransform: "capitalize" },
  mealName: { fontSize: 18, fontWeight: "700" },
  components: { fontSize: 13, color: "#444" },
  practicality: { fontSize: 12, color: "#5C6B55", fontWeight: "600" },
  reason: { fontSize: 12, color: "#666" },
  actionRow: { flexDirection: "row", gap: 8 },
  primaryButton: { flex: 1, backgroundColor: "#1F7A3F", borderRadius: 8, padding: 10, alignItems: "center" },
  primaryText: { color: "white", fontWeight: "700", fontSize: 12 },
  secondaryButton: { borderWidth: 1, borderColor: "#1F7A3F", borderRadius: 8, padding: 10, alignItems: "center" },
  secondaryText: { color: "#1F7A3F", fontWeight: "700", fontSize: 12 },
  locked: { backgroundColor: "#EAF4ED" },
  reasonRow: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  reasonButton: { borderWidth: 1, borderColor: "#D8D1C4", borderRadius: 14, paddingVertical: 6, paddingHorizontal: 9 },
  reasonButtonText: { fontSize: 11, color: "#555" },
  recipeLink: { color: "#4A6FA5", fontSize: 12, fontWeight: "600" },
  error: { color: "#C0392B" },
});

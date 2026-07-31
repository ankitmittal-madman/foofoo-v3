/**
 * Onboarding Screen 1 — "Who lives in your home?" Ported from scareme21-create/NewFoo's
 * onboarding/step-1.tsx. Layout/copy unchanged; entering-animation wrappers dropped (see
 * splash-2.tsx); submit now calls foofoo-v3's real POST /v1/household (source's screens
 * accumulated answers and submitted once at the end against a different backend — here
 * each step submits its own slice immediately, matching this repo's other onboarding
 * screens and household/handler.ts's incremental-accumulation design).
 */
import { useMemo, useRef } from "react";
import { type LayoutChangeEvent, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";

import { useTheme } from "@/theme";
import { useOnboarding, type HouseholdType } from "@/onboarding/OnboardingContext";
import { StepHeader } from "@/onboarding/OnboardingHeader";
import { step1ToScreens } from "@/onboarding/toHouseholdWrite";
import { postHousehold } from "@/api/household";
import { ApiError } from "@/api/client";

type DotKind = "adult" | "kid" | "elder";
type HouseholdOption = { value: HouseholdType; title: string; subtitle: string; dots: DotKind[] };

const HOUSEHOLDS: HouseholdOption[] = [
  { value: "single", title: "Just Me", subtitle: "Solo", dots: ["adult"] },
  { value: "couple", title: "Couple", subtitle: "Two adults", dots: ["adult", "adult"] },
  { value: "couple_kids", title: "Couple + Kids", subtitle: "Parents & children", dots: ["adult", "adult", "kid"] },
  { value: "couple_kids_parents", title: "Couple, Kids & Parents", subtitle: "With elderly parents", dots: ["adult", "adult", "kid", "elder"] },
  { value: "flatmates", title: "Flatmates", subtitle: "Shared living", dots: ["adult", "adult", "adult"] },
  { value: "joint", title: "Full Family", subtitle: "Joint family", dots: ["adult", "adult", "adult", "kid"] },
];

type EarnerOption = { value: number; display: string; label: string };

/**
 * earnerOptionsFor — decides which "working professionals" chip choices to offer, based on
 * the household type just picked. Single-person households never ask this question at all
 * (empty array); couples cap out at 2, everyone else (families, flatmates) can go up to "3+".
 * @param household - the household type selected above, or null before any selection.
 * @returns the earner-count chip options to render, or an empty array to skip the question.
 */
function earnerOptionsFor(household: HouseholdType | null): EarnerOption[] {
  if (household === null || household === "single") return [];
  const one: EarnerOption = { value: 1, display: "1", label: "person" };
  const two: EarnerOption = { value: 2, display: "2", label: "people" };
  if (household === "couple" || household === "couple_kids") return [one, two];
  return [one, two, { value: 3, display: "3+", label: "people" }];
}

export default function OnboardingStep1() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const { answers, setAnswers } = useOnboarding();

  const household = answers.householdType;
  const earners = answers.workingProfessionals;
  const earnerOptions = useMemo(() => earnerOptionsFor(household), [household]);
  const askEarners = earnerOptions.length > 0;

  const canContinue = household !== null && (!askEarners || earners !== null);

  const scrollRef = useRef<ScrollView>(null);
  const scrollPending = useRef(false);

  const mutation = useMutation({
    mutationFn: () => postHousehold(step1ToScreens(answers), []),
    onSuccess: () => router.push("/(onboarding)/step-2"),
  });

  function selectHousehold(value: HouseholdType) {
    setAnswers({ householdType: value, workingProfessionals: null });
    scrollPending.current = value !== "single";
  }

  function onEarnerLayout(e: LayoutChangeEvent) {
    if (!scrollPending.current) return;
    scrollPending.current = false;
    const y = Math.max(e.nativeEvent.layout.y - 12, 0);
    scrollRef.current?.scrollTo({ y, animated: true });
  }

  return (
    <View style={[styles.root, { backgroundColor: t.colors.background, paddingTop: insets.top + t.spacing.md }]}>
      <StepHeader current={1} total={5} showBack={false} />

      <ScrollView ref={scrollRef} style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={[styles.eyebrow, { color: t.colors.primary, fontFamily: t.fonts.bodySemiBold }]}>STEP 1 — YOUR HOME</Text>
        <Text style={[styles.title, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>Who lives{"\n"}in your home?</Text>
        <Text style={[styles.subtitle, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>
          Every recommendation adapts to your household&apos;s size, needs, and rhythm.
        </Text>

        <Text style={[styles.sectionLabel, { color: t.colors.textSecondary, fontFamily: t.fonts.bodySemiBold }]}>SELECT YOUR HOUSEHOLD</Text>
        <View style={styles.grid}>
          {HOUSEHOLDS.map((opt) => {
            const selected = household === opt.value;
            return (
              <Pressable
                key={opt.value}
                onPress={() => selectHousehold(opt.value)}
                style={({ pressed }) => [
                  styles.card,
                  { backgroundColor: selected ? t.colors.selected : t.colors.surface, borderColor: selected ? t.colors.selected : t.colors.border, opacity: pressed ? 0.92 : 1 },
                ]}
              >
                {selected ? (
                  <View style={[styles.check, { backgroundColor: t.colors.check }]}>
                    <Text style={[styles.checkMark, { color: t.colors.onSelected }]}>✓</Text>
                  </View>
                ) : null}
                <PersonDots kinds={opt.dots} selected={selected} />
                <Text style={[styles.cardTitle, { color: selected ? t.colors.onSelected : t.colors.text, fontFamily: t.fonts.bodySemiBold }]}>{opt.title}</Text>
                <Text style={[styles.cardSubtitle, { color: selected ? t.colors.onSelected : t.colors.textSecondary, fontFamily: t.fonts.body, opacity: selected ? 0.8 : 1 }]}>
                  {opt.subtitle}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <View onLayout={onEarnerLayout}>
          {askEarners ? (
            <View>
              <Text style={[styles.sectionLabel, { color: t.colors.textSecondary, fontFamily: t.fonts.bodySemiBold }]}>WORKING PROFESSIONALS IN YOUR HOME</Text>
              <View style={styles.earnerRow}>
                {earnerOptions.map((opt) => {
                  const selected = earners === opt.value;
                  return (
                    <Pressable
                      key={opt.value}
                      onPress={() => setAnswers({ workingProfessionals: opt.value })}
                      style={({ pressed }) => [
                        styles.earnerCard,
                        { backgroundColor: selected ? t.colors.selected : t.colors.surface, borderColor: selected ? t.colors.selected : t.colors.border, opacity: pressed ? 0.92 : 1 },
                      ]}
                    >
                      <Text style={[styles.earnerNumber, { color: selected ? t.colors.onSelected : t.colors.heading, fontFamily: t.fonts.headlineBold }]}>{opt.display}</Text>
                      <Text style={[styles.earnerLabel, { color: selected ? t.colors.onSelected : t.colors.textSecondary, fontFamily: t.fonts.body, opacity: selected ? 0.8 : 1 }]}>
                        {opt.label}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
              <Text style={[styles.helper, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>We&apos;ll prioritise quick, practical meals around busy days.</Text>
            </View>
          ) : null}
        </View>

        {mutation.isError ? (
          <Text style={[styles.errorText, { color: t.colors.primary, fontFamily: t.fonts.bodyMedium }]}>
            {mutation.error instanceof ApiError ? mutation.error.message : "Something went wrong"}
          </Text>
        ) : null}
      </ScrollView>

      <View style={[styles.footer, { paddingBottom: insets.bottom + t.spacing.md }]}>
        <Pressable
          disabled={!canContinue || mutation.isPending}
          onPress={() => mutation.mutate()}
          style={({ pressed }) => [styles.button, { backgroundColor: canContinue ? t.colors.selected : t.colors.disabled, opacity: pressed && canContinue ? 0.9 : 1 }]}
        >
          <Text style={[styles.buttonLabel, { fontFamily: t.fonts.bodySemiBold, color: canContinue ? t.colors.onSelected : t.colors.onDisabled }]}>
            {mutation.isPending ? "Saving..." : "Continue →"}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

/**
 * PersonDots — the small row of colored dots on each household card (e.g. two adult dots for
 * "Couple", an extra smaller dot for a kid or elder) giving an at-a-glance visual of who's in
 * that household type, before the user reads the title text.
 * @param kinds - which dot types to draw, in order (first one is the "hero" dot, colored
 *                differently from the rest).
 * @param selected - whether this card is currently chosen — swaps the dot colors to their
 *                    on-selected variants so they stay visible against the selected background.
 */
function PersonDots({ kinds, selected }: { kinds: DotKind[]; selected: boolean }) {
  const t = useTheme();
  const sizeFor = (k: DotKind) => (k === "kid" ? 6 : k === "elder" ? 8 : 10);
  const heroColor = selected ? t.colors.accent : t.colors.primary;
  const restColor = selected ? t.colors.onSelected : t.colors.textSecondary;
  return (
    <View style={styles.dots}>
      {kinds.map((k, i) => {
        const size = sizeFor(k);
        return (
          <View
            key={i}
            style={{ width: size, height: size, borderRadius: size / 2, marginRight: 4, backgroundColor: i === 0 ? heroColor : restColor, opacity: i === 0 ? 1 : 0.55 }}
          />
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, paddingHorizontal: 24 },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 16 },
  eyebrow: { fontSize: 12, letterSpacing: 1.2, marginBottom: 10 },
  title: { fontSize: 32, lineHeight: 38 },
  subtitle: { fontSize: 15, lineHeight: 22, marginTop: 12 },
  sectionLabel: { fontSize: 12, letterSpacing: 1, marginTop: 28, marginBottom: 14 },
  grid: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between" },
  card: { width: "48%", minHeight: 84, borderRadius: 16, borderWidth: 1, paddingVertical: 14, paddingHorizontal: 14, marginBottom: 12, justifyContent: "center" },
  check: { position: "absolute", top: 10, right: 10, width: 20, height: 20, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  checkMark: { fontSize: 12, lineHeight: 14 },
  dots: { flexDirection: "row", alignItems: "center", marginBottom: 10, minHeight: 10 },
  cardTitle: { fontSize: 16, lineHeight: 20 },
  cardSubtitle: { fontSize: 13, lineHeight: 18, marginTop: 2 },
  earnerRow: { flexDirection: "row", justifyContent: "space-between" },
  earnerCard: { flex: 1, minHeight: 76, borderRadius: 16, borderWidth: 1, marginHorizontal: 4, alignItems: "center", justifyContent: "center" },
  earnerNumber: { fontSize: 26, lineHeight: 30 },
  earnerLabel: { fontSize: 13, lineHeight: 16, marginTop: 2 },
  helper: { fontSize: 14, lineHeight: 20, marginTop: 14 },
  errorText: { fontSize: 14, marginTop: 14 },
  footer: { paddingTop: 8 },
  button: { height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center" },
  buttonLabel: { fontSize: 16 },
});

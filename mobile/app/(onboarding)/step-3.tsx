/**
 * Onboarding Screen 3 — "What kind of meals do you enjoy?" Ported from
 * scareme21-create/NewFoo's onboarding/step-3.tsx (layout/copy unchanged). Submit maps
 * `diet` through toHouseholdWrite.ts's DIET_MAP ('eggetarian' -> our 'egg') rather than
 * storing the UI token directly, since foofoo-v3's profiles.diet_type CHECK constraint
 * doesn't have an 'eggetarian' value.
 */
import { useRef } from "react";
import { type LayoutChangeEvent, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";

import { useTheme } from "@/theme";
import { useOnboarding, type DietChoice } from "@/onboarding/OnboardingContext";
import { StepHeader } from "@/onboarding/OnboardingHeader";
import { ChipGroup, type ChipOption } from "@/onboarding/OnboardingChips";
import { step3ToScreens } from "@/onboarding/toHouseholdWrite";
import { postHousehold } from "@/api/household";
import { describeApiError } from "@/api/errorMessages";

type Option = ChipOption;
type DietToneKey = "plant" | "egg" | "meat";
type DietOption = { value: DietChoice; title: string; subtitle: string; tone: DietToneKey };

const DIETS: DietOption[] = [
  { value: "veg", title: "Vegetarian", subtitle: "No meat, no egg", tone: "plant" },
  { value: "eggetarian", title: "Eggetarian", subtitle: "Veg + eggs only", tone: "egg" },
  { value: "non_veg", title: "Non-Vegetarian", subtitle: "Meat & poultry", tone: "meat" },
  { value: "jain", title: "Jain", subtitle: "Strict veg, no root", tone: "plant" },
  { value: "vegan", title: "Vegan", subtitle: "No animal products", tone: "plant" },
];

const MEATS: Option[] = [
  { value: "chicken", label: "Chicken" },
  { value: "mutton", label: "Mutton" },
  { value: "fish", label: "Fish" },
  { value: "other_seafood", label: "Other Seafood" },
  { value: "pork", label: "Pork" },
  { value: "any", label: "Any" },
];

const DAYS: Option[] = [
  { value: "monday", label: "Mon" },
  { value: "tuesday", label: "Tue" },
  { value: "wednesday", label: "Wed" },
  { value: "thursday", label: "Thu" },
  { value: "friday", label: "Fri" },
  { value: "saturday", label: "Sat" },
  { value: "sunday", label: "Sun" },
];

function hasFollowUp(diet: DietChoice | null): boolean {
  return diet === "non_veg" || diet === "eggetarian";
}

export default function OnboardingStep3() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const { answers, setAnswers, setCurrentStep } = useOnboarding();

  const diet = answers.diet;
  const canContinue = diet !== null;

  const scrollRef = useRef<ScrollView>(null);
  const scrollPending = useRef(false);

  const mutation = useMutation({
    mutationFn: () => postHousehold(step3ToScreens(answers), []),
    onSuccess: () => {
      setCurrentStep(4);
      router.push("/(onboarding)/step-4");
    },
  });

  function selectDiet(value: DietChoice) {
    setAnswers({ diet: value, jainExclusions: [], meatPreferences: [], vegDays: [] });
    scrollPending.current = hasFollowUp(value);
  }

  function onFollowUpLayout(e: LayoutChangeEvent) {
    if (!scrollPending.current) return;
    scrollPending.current = false;
    const y = Math.max(e.nativeEvent.layout.y - 12, 0);
    scrollRef.current?.scrollTo({ y, animated: true });
  }

  function toggle(field: "vegDays", value: string) {
    const cur = answers[field];
    setAnswers({ [field]: cur.includes(value) ? cur.filter((v) => v !== value) : [...cur, value] });
  }

  function toggleMeat(value: string) {
    const cur = answers.meatPreferences;
    if (value === "any") {
      setAnswers({ meatPreferences: cur.includes("any") ? [] : ["any"] });
      return;
    }
    const without = cur.filter((v) => v !== "any");
    setAnswers({ meatPreferences: without.includes(value) ? without.filter((v) => v !== value) : [...without, value] });
  }

  return (
    <View style={[styles.root, { backgroundColor: t.colors.background, paddingTop: insets.top + t.spacing.md }]}>
      <StepHeader current={3} total={5} />

      <ScrollView ref={scrollRef} style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={[styles.eyebrow, { color: t.colors.primary, fontFamily: t.fonts.bodySemiBold }]}>STEP 3 — DIET</Text>
        <Text style={[styles.title, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>What kind of meals{"\n"}do you enjoy?</Text>
        <Text style={[styles.subtitle, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>Your diet type anchors every recommendation we make.</Text>

        <Text style={[styles.sectionLabel, { color: t.colors.textSecondary, fontFamily: t.fonts.bodySemiBold }]}>CHOOSE YOUR DIET</Text>
        <View style={styles.grid}>
          {DIETS.map((opt) => (
            <DietCard key={opt.value} option={opt} selected={diet === opt.value} onPress={() => selectDiet(opt.value)} />
          ))}
        </View>

        <View onLayout={onFollowUpLayout}>
          {diet === "non_veg" ? (
            <>
              <FollowUp label="MEAT PREFERENCES" hint="Pick what you enjoy, or “Any”.">
                <ChipGroup options={MEATS} selected={answers.meatPreferences} onToggle={toggleMeat} />
              </FollowUp>
              <FollowUp label="ANY VEG-ONLY DAYS?" hint="We’ll keep these days fully vegetarian.">
                <ChipGroup options={DAYS} selected={answers.vegDays} onToggle={(v) => toggle("vegDays", v)} />
              </FollowUp>
            </>
          ) : null}

          {diet === "eggetarian" ? (
            <FollowUp label="ANY VEG-ONLY DAYS?" hint="We’ll keep these days fully vegetarian.">
              <ChipGroup options={DAYS} selected={answers.vegDays} onToggle={(v) => toggle("vegDays", v)} />
            </FollowUp>
          ) : null}
        </View>

        {mutation.isError ? (
          <Text style={[styles.errorText, { color: t.colors.primary, fontFamily: t.fonts.bodyMedium }]}>
            {describeApiError(mutation.error)}
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

function DietCard({ option, selected, onPress }: { option: DietOption; selected: boolean; onPress: () => void }) {
  const t = useTheme();
  const toneColor = option.tone === "plant" ? t.colors.success : option.tone === "egg" ? t.colors.accent : t.colors.primary;
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.dietCard, { backgroundColor: selected ? t.colors.selected : t.colors.surface, borderColor: selected ? t.colors.selected : t.colors.border, opacity: pressed ? 0.94 : 1 }]}
    >
      {selected ? (
        <View style={[styles.check, { backgroundColor: t.colors.check }]}>
          <Text style={[styles.checkMark, { color: t.colors.onSelected }]}>✓</Text>
        </View>
      ) : null}
      <View style={[styles.dietDot, { backgroundColor: toneColor }]} />
      <Text style={[styles.dietTitle, { color: selected ? t.colors.onSelected : t.colors.text, fontFamily: t.fonts.bodySemiBold }]}>{option.title}</Text>
      <Text style={[styles.dietSub, { color: selected ? t.colors.onSelected : t.colors.textSecondary, fontFamily: t.fonts.body, opacity: selected ? 0.8 : 1 }]}>{option.subtitle}</Text>
    </Pressable>
  );
}

function FollowUp({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  const t = useTheme();
  return (
    <View>
      <Text style={[styles.sectionLabel, { color: t.colors.textSecondary, fontFamily: t.fonts.bodySemiBold }]}>{label}</Text>
      {hint ? <Text style={[styles.hint, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>{hint}</Text> : null}
      {children}
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
  sectionLabel: { fontSize: 12, letterSpacing: 1, marginTop: 28, marginBottom: 8 },
  hint: { fontSize: 14, lineHeight: 20, marginBottom: 12 },
  grid: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between" },
  dietCard: { width: "48%", minHeight: 92, borderRadius: 16, borderWidth: 1, paddingVertical: 14, paddingHorizontal: 14, marginBottom: 12, justifyContent: "center" },
  dietDot: { width: 10, height: 10, borderRadius: 5, marginBottom: 10 },
  dietTitle: { fontSize: 15, lineHeight: 19 },
  dietSub: { fontSize: 12, lineHeight: 16, marginTop: 3 },
  check: { position: "absolute", top: 10, right: 10, width: 20, height: 20, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  checkMark: { fontSize: 12, lineHeight: 14 },
  errorText: { fontSize: 14, marginTop: 14 },
  footer: { paddingTop: 8 },
  button: { height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center" },
  buttonLabel: { fontSize: 16 },
});

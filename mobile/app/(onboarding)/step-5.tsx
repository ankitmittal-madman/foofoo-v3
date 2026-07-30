/**
 * Onboarding Screen 5 — "Last details about your home." Adapted from
 * scareme21-create/NewFoo's onboarding/step-5.tsx. Source's screen was fully skippable;
 * a "YOUR COOKING SKILL" section was added here and made REQUIRED (unlike every other
 * question on this screen) because profiles.cook_capability is one of the five fields
 * household/handler.ts requires before it will create a profile at all — source's flow
 * never collected this field. Finishing now submits this step's answers via POST
 * /v1/household and lands on this repo's real recommendations screen, not source's
 * final-dish/plan screens (dropped — they depend on Cloudinary, not ported).
 */
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";

import { useTheme } from "@/theme";
import { useOnboarding, isSplitAgeHousehold, type CookCapability, type OnboardingAnswers } from "@/onboarding/OnboardingContext";
import { StepHeader } from "@/onboarding/OnboardingHeader";
import { ChipGroup, type ChipOption } from "@/onboarding/OnboardingChips";
import { step5ToPayload } from "@/onboarding/toHouseholdWrite";
import { postHousehold } from "@/api/household";
import { ApiError } from "@/api/client";

const AGE_RANGES: ChipOption[] = [
  { value: "18-25", label: "18–25" },
  { value: "25-35", label: "25–35" },
  { value: "35-45", label: "35–45" },
  { value: "45-60", label: "45–60" },
  { value: "60+", label: "60+" },
];

const AGE_YOUNGEST: ChipOption[] = [
  { value: "0-2", label: "0–2" },
  { value: "2-5", label: "2–5" },
  { value: "5-12", label: "5–12" },
  { value: "12-18", label: "12–18" },
  ...AGE_RANGES,
];

const WHO_COOKS: ChipOption[] = [
  { value: "self", label: "Self" },
  { value: "family", label: "Family member" },
  { value: "hired_cook", label: "Hired cook" },
  { value: "order_in", label: "Order-in / tiffin" },
];

const COOK_CAPABILITY: ChipOption[] = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const EAT_OUT: ChipOption[] = [
  { value: "rarely", label: "Rarely" },
  { value: "weekly", label: "Weekly" },
  { value: "few_weekly", label: "A few times a week" },
  { value: "daily", label: "Almost Daily" },
];

const OBJECTIVES: ChipOption[] = [
  { value: "tasty", label: "To get tasty options" },
  { value: "healthy", label: "To get healthy options" },
  { value: "discover", label: "To discover" },
  { value: "into_fitness", label: "Into Fitness" },
];

type SingleField = "ageSingle" | "ageEldest" | "ageYoungest" | "whoCooks" | "eatOutFrequency" | "cookingObjective" | "cookCapability";

export default function OnboardingStep5() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const { answers, setAnswers } = useOnboarding();
  const split = isSplitAgeHousehold(answers.householdType);

  const canContinue = answers.cookCapability !== null;

  const mutation = useMutation({
    mutationFn: () => {
      const { screens, members } = step5ToPayload(answers);
      return postHousehold(screens, members);
    },
    onSuccess: () => router.replace("/recommendations"),
  });

  function selectOne(field: SingleField, value: string) {
    setAnswers({ [field]: answers[field] === value ? null : value } as Partial<OnboardingAnswers>);
  }
  const sel = (field: SingleField) => {
    const v = answers[field];
    return v ? [v] : [];
  };

  return (
    <View style={[styles.root, { backgroundColor: t.colors.background, paddingTop: insets.top + t.spacing.md }]}>
      <StepHeader current={5} total={5} />

      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={[styles.eyebrow, { color: t.colors.primary, fontFamily: t.fonts.bodySemiBold }]}>STEP 5 — LAST DETAILS</Text>
        <Text style={[styles.title, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>Last details{"\n"}about your home</Text>
        <Text style={[styles.subtitle, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>Everything below is optional except your cooking skill.</Text>

        {split ? (
          <>
            <Section label="ELDEST IN THE HOME">
              <ChipGroup options={AGE_RANGES} selected={sel("ageEldest")} onToggle={(v) => selectOne("ageEldest", v)} />
            </Section>
            <Section label="YOUNGEST IN THE HOME" hint="Helps us keep meals gentle enough for little ones.">
              <ChipGroup options={AGE_YOUNGEST} selected={sel("ageYoungest")} onToggle={(v) => selectOne("ageYoungest", v)} />
            </Section>
          </>
        ) : (
          <Section label="AGE GROUP">
            <ChipGroup options={AGE_RANGES} selected={sel("ageSingle")} onToggle={(v) => selectOne("ageSingle", v)} />
          </Section>
        )}

        <Section label="WHO COOKS?">
          <ChipGroup options={WHO_COOKS} selected={sel("whoCooks")} onToggle={(v) => selectOne("whoCooks", v)} />
        </Section>

        <Section label="YOUR COOKING SKILL" hint="Required — helps us match recipe difficulty to your comfort level.">
          <ChipGroup options={COOK_CAPABILITY} selected={sel("cookCapability")} onToggle={(v) => selectOne("cookCapability", v as CookCapability)} />
        </Section>

        <Section label="HOW OFTEN DO YOU EAT OUT?">
          <ChipGroup options={EAT_OUT} selected={sel("eatOutFrequency")} onToggle={(v) => selectOne("eatOutFrequency", v)} />
        </Section>

        <Section label="WHAT ARE YOU COOKING FOR?" hint="Skip and we'll aim for awesome taste.">
          <ChipGroup options={OBJECTIVES} selected={sel("cookingObjective")} onToggle={(v) => selectOne("cookingObjective", v)} />
        </Section>

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
            {mutation.isPending ? "Finishing..." : "See my plan →"}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

function Section({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
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
  errorText: { fontSize: 14, marginTop: 14 },
  footer: { paddingTop: 8 },
  button: { height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center" },
  buttonLabel: { fontSize: 16 },
});

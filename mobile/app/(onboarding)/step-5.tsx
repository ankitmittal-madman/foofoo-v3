/**
 * Onboarding Screen 5 — "Last details about your home." Adapted from
 * scareme21-create/NewFoo's onboarding/step-5.tsx. Source's screen was fully skippable;
 * a "YOUR COOKING SKILL" section was added here and made REQUIRED (unlike every other
 * question on this screen) because profiles.cook_capability is one of the five fields
 * household/handler.ts requires before it will create a profile at all — source's flow
 * never collected this field. Finishing now submits this step's answers via POST
 * /v1/household and lands on this repo's real recommendations screen, not source's
 * final-dish/plan screens (dropped — they depend on Cloudinary, not ported).
 *
 * Consent dispatch (Fix 5 — see consent.tsx's header comment for the full FK-ordering rationale):
 * the actual POST /v1/consent call is fired here, immediately after postHousehold succeeds in
 * creating the profiles row, because consent_records.profile_id has a NOT NULL FK to
 * public.profiles(id) that cannot be satisfied any earlier in this flow. The consent DECISION was
 * already captured and enforced on consent.tsx, before step-1 — this is only the deferred network
 * dispatch of that already-made decision, not a second consent prompt.
 *
 * Validation-trap fix (audit-onboarding-funnel MEDIUM finding — "5 sections gated by only one
 * visibly-required field, no cue which one"): Continue is no longer silently disabled. Tapping it
 * with cookCapability unset scrolls to and highlights that section instead.
 */
import { useRef, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View, type LayoutChangeEvent } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";

import { useTheme } from "@/theme";
import { useOnboarding, isSplitAgeHousehold, type CookCapability, type OnboardingAnswers } from "@/onboarding/OnboardingContext";
import { StepHeader } from "@/onboarding/OnboardingHeader";
import { ChipGroup, type ChipOption } from "@/onboarding/OnboardingChips";
import { step5ToPayload } from "@/onboarding/toHouseholdWrite";
import { postHousehold } from "@/api/household";
import { postConsent } from "@/api/consent";
import { describeApiError } from "@/api/errorMessages";
import { useSession } from "@/auth/SessionContext";
import { PRIVACY_POLICY_VERSION } from "@/onboarding/privacyPolicy";
import type { ConsentInput } from "@/api/types";

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
  const { session } = useSession();
  const { answers, setAnswers, consent, setConsent, reset } = useOnboarding();
  const split = isSplitAgeHousehold(answers.householdType);

  const canContinue = answers.cookCapability !== null;
  const [attemptedContinue, setAttemptedContinue] = useState(false);
  const cookCapabilityRef = useRef<View>(null);
  const scrollRef = useRef<ScrollView>(null);
  const cookCapabilityY = useRef(0);

  const mutation = useMutation({
    mutationFn: async () => {
      const { screens, members } = step5ToPayload(answers);
      const result = await postHousehold(screens, members);

      // Dispatch the already-made consent decision now that a profile exists for it to reference
      // (see this file's header comment). Guarded on consent.submitted so a retry after a
      // household-write failure on THIS mutation doesn't double-submit consent if it already
      // succeeded on a prior attempt.
      if (!consent.submitted && session?.user.id) {
        const consents: ConsentInput[] = [
          { consent_type: "personalization", granted: consent.personalization ?? true },
          { consent_type: "analytics", granted: consent.analytics ?? false },
          { consent_type: "push_notifications", granted: consent.pushNotifications ?? false },
          { consent_type: "data_retention", granted: consent.dataRetention ?? false },
        ];
        await postConsent({
          profile_id: session.user.id,
          consents,
          privacy_policy_version: consent.privacyPolicyVersion ?? PRIVACY_POLICY_VERSION,
        });
        setConsent({ submitted: true });
      }

      return result;
    },
    onSuccess: () => {
      reset();
      // WP-18: land on the cold-start preference primer (top-15 diverse dishes to like), not
      // straight into the plain recommendations list — this is the new onboarding->plan flow.
      router.replace("/cold-start");
    },
  });

  function handleContinue() {
    if (!canContinue) {
      setAttemptedContinue(true);
      scrollRef.current?.scrollTo({ y: Math.max(cookCapabilityY.current - 16, 0), animated: true });
      return;
    }
    mutation.mutate();
  }

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

      <ScrollView ref={scrollRef} style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={[styles.eyebrow, { color: t.colors.primary, fontFamily: t.fonts.bodySemiBold }]}>STEP 5 — LAST DETAILS</Text>
        <Text style={[styles.title, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>Last details{"\n"}about your home</Text>
        <Text style={[styles.subtitle, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>Everything below is optional except your cooking skill.</Text>

        {split ? (
          <>
            <Section label="ELDEST IN THE HOME">
              <ChipGroup options={AGE_RANGES} selected={sel("ageEldest")} onToggle={(v) => selectOne("ageEldest", v)} testIDPrefix="onboarding-step5-age-eldest" />
            </Section>
            <Section label="YOUNGEST IN THE HOME" hint="Helps us keep meals gentle enough for little ones.">
              <ChipGroup options={AGE_YOUNGEST} selected={sel("ageYoungest")} onToggle={(v) => selectOne("ageYoungest", v)} testIDPrefix="onboarding-step5-age-youngest" />
            </Section>
          </>
        ) : (
          <Section label="AGE GROUP">
            <ChipGroup options={AGE_RANGES} selected={sel("ageSingle")} onToggle={(v) => selectOne("ageSingle", v)} testIDPrefix="onboarding-step5-age-single" />
          </Section>
        )}

        <Section label="WHO COOKS?">
          <ChipGroup options={WHO_COOKS} selected={sel("whoCooks")} onToggle={(v) => selectOne("whoCooks", v)} testIDPrefix="onboarding-step5-whocooks" />
        </Section>

        <View
          ref={cookCapabilityRef}
          onLayout={(e: LayoutChangeEvent) => {
            cookCapabilityY.current = e.nativeEvent.layout.y;
          }}
        >
          <Section
            label="YOUR COOKING SKILL"
            hint="Required — helps us match recipe difficulty to your comfort level."
            error={attemptedContinue && !canContinue}
            errorText="Please select your cooking skill to continue."
          >
            <ChipGroup options={COOK_CAPABILITY} selected={sel("cookCapability")} onToggle={(v) => selectOne("cookCapability", v as CookCapability)} testIDPrefix="onboarding-step5-cookcapability" />
          </Section>
        </View>

        <Section label="HOW OFTEN DO YOU EAT OUT?">
          <ChipGroup options={EAT_OUT} selected={sel("eatOutFrequency")} onToggle={(v) => selectOne("eatOutFrequency", v)} testIDPrefix="onboarding-step5-eatout" />
        </Section>

        <Section label="WHAT ARE YOU COOKING FOR?" hint="Skip and we'll aim for awesome taste.">
          <ChipGroup options={OBJECTIVES} selected={sel("cookingObjective")} onToggle={(v) => selectOne("cookingObjective", v)} testIDPrefix="onboarding-step5-objective" />
        </Section>

        {mutation.isError ? (
          <Text style={[styles.errorText, { color: t.colors.primary, fontFamily: t.fonts.bodyMedium }]}>
            {describeApiError(mutation.error)}
          </Text>
        ) : null}
      </ScrollView>

      <View style={[styles.footer, { paddingBottom: insets.bottom + t.spacing.md }]}>
        <Pressable
          testID="onboarding-step5-continue"
          disabled={mutation.isPending}
          onPress={handleContinue}
          style={({ pressed }) => [styles.button, { backgroundColor: t.colors.selected, opacity: pressed ? 0.9 : 1 }]}
        >
          <Text style={[styles.buttonLabel, { fontFamily: t.fonts.bodySemiBold, color: t.colors.onSelected }]}>
            {mutation.isPending ? "Finishing..." : "See my plan →"}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

/**
 * Section — a labeled block wrapping one of Screen 5's optional questions (age group, who
 * cooks, cooking skill, eat-out frequency, cooking objective), each with its own heading and
 * an optional helper line.
 * @param label - the section's all-caps heading (e.g. "YOUR COOKING SKILL").
 * @param hint - optional helper copy shown under the label (e.g. noting a field is required).
 * @param error - true when this section is the one Continue is blocked on, highlights the label.
 * @param errorText - the message shown under the label when `error` is true.
 * @param children - the chip group this section wraps.
 */
function Section({
  label,
  hint,
  error,
  errorText,
  children,
}: {
  label: string;
  hint?: string;
  error?: boolean;
  errorText?: string;
  children: React.ReactNode;
}) {
  const t = useTheme();
  return (
    <View>
      <Text style={[styles.sectionLabel, { color: error ? t.colors.primary : t.colors.textSecondary, fontFamily: t.fonts.bodySemiBold }]}>{label}</Text>
      {hint ? <Text style={[styles.hint, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>{hint}</Text> : null}
      {error && errorText ? (
        <Text style={[styles.hint, { color: t.colors.primary, fontFamily: t.fonts.bodyMedium, marginTop: -8 }]}>{errorText}</Text>
      ) : null}
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

/**
 * Onboarding Screen 4 — "Any health-related things I should know?" Ported from
 * scareme21-create/NewFoo's onboarding/step-4.tsx (layout/copy unchanged). Allergen chips
 * submit as profiles.allergen_flags (the frozen 7-bit model, compose.ts's ALLERGEN_BITS)
 * via toHouseholdWrite.ts's allergenFlags() — source stored these as an array under a
 * different backend's own allergen-slug model, which does not exist here.
 */
import { useRef, useState } from "react";
import { Keyboard, KeyboardAvoidingView, type LayoutChangeEvent, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";

import { useTheme } from "@/theme";
import { useOnboarding } from "@/onboarding/OnboardingContext";
import { StepHeader } from "@/onboarding/OnboardingHeader";
import { ChipGroup, type ChipOption } from "@/onboarding/OnboardingChips";
import { step4ToScreens } from "@/onboarding/toHouseholdWrite";
import { postHousehold } from "@/api/household";
import { describeApiError } from "@/api/errorMessages";

const ALLERGENS: ChipOption[] = [
  { value: "peanuts", label: "Peanut" },
  { value: "dairy", label: "Dairy" },
  { value: "gluten", label: "Gluten" },
  { value: "soy", label: "Soy" },
  { value: "sesame", label: "Sesame" },
  { value: "shellfish", label: "Shellfish" },
  { value: "fish", label: "Fish" },
  { value: "mustard", label: "Mustard" },
  { value: "others", label: "Others" },
];

const MEDICAL_CONDITIONS: ChipOption[] = [
  { value: "diabetes", label: "Diabetes" },
  { value: "hypertension", label: "High blood pressure" },
  { value: "high_cholesterol", label: "High cholesterol" },
  { value: "thyroid", label: "Thyroid" },
  { value: "pcos", label: "PCOS / PCOD" },
  { value: "acidity", label: "Acidity / GERD" },
  { value: "heart", label: "Heart condition" },
  { value: "kidney", label: "Kidney condition" },
  { value: "others", label: "Others" },
];

export default function OnboardingStep4() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const { answers, setAnswers, setCurrentStep } = useOnboarding();

  const scrollRef = useRef<ScrollView>(null);
  const pendingScroll = useRef<string | null>(null);
  const [attemptedContinue, setAttemptedContinue] = useState(false);

  const mutation = useMutation({
    mutationFn: () => postHousehold(step4ToScreens(answers), []),
    onSuccess: () => {
      setCurrentStep(5);
      router.push("/(onboarding)/step-5");
    },
  });

  function toggleOption(field: "allergens" | "medicalConditions", otherField: "allergensOther" | "medicalConditionsOther", value: string) {
    const cur = answers[field];
    const on = cur.includes(value);
    const next = on ? cur.filter((v) => v !== value) : [...cur, value];
    if (value === "others" && !on) pendingScroll.current = field;
    setAnswers({ [field]: next, ...(value === "others" && on ? { [otherField]: "" } : {}) });
  }

  function onOtherLayout(field: string, e: LayoutChangeEvent) {
    if (pendingScroll.current !== field) return;
    pendingScroll.current = null;
    const y = Math.max(e.nativeEvent.layout.y - 120, 0);
    scrollRef.current?.scrollTo({ y, animated: true });
  }

  const allergensOtherMissing = answers.allergens.includes("others") && !answers.allergensOther.trim();
  const medicalOtherMissing = answers.medicalConditions.includes("others") && !answers.medicalConditionsOther.trim();

  function handleContinue() {
    if (allergensOtherMissing || medicalOtherMissing) {
      setAttemptedContinue(true);
      Keyboard.dismiss();
      scrollRef.current?.scrollToEnd({ animated: true });
      return;
    }
    mutation.mutate();
  }

  return (
    <KeyboardAvoidingView style={[styles.root, { backgroundColor: t.colors.background, paddingTop: insets.top + t.spacing.md }]} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <StepHeader current={4} total={5} />

      <ScrollView ref={scrollRef} style={styles.scroll} contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" showsVerticalScrollIndicator={false}>
        <Text style={[styles.eyebrow, { color: t.colors.primary, fontFamily: t.fonts.bodySemiBold }]}>STEP 4 — HEALTH</Text>
        <Text style={[styles.title, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>Any health-related{"\n"}things I should know?</Text>
        <Text style={[styles.subtitle, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>A couple of safety details before we finish. Leave anything blank if it doesn&apos;t apply.</Text>

        <Text style={[styles.sectionLabel, { color: t.colors.textSecondary, fontFamily: t.fonts.bodySemiBold }]}>ALLERGIES</Text>
        <Text style={[styles.hint, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>We&apos;ll never recommend a dish containing these.</Text>
        <ChipGroup options={ALLERGENS} selected={answers.allergens} onToggle={(v) => toggleOption("allergens", "allergensOther", v)} testIDPrefix="onboarding-step4-allergen" />
        {answers.allergens.includes("others") ? (
          <OtherInput
            testID="onboarding-step4-allergen-other-input"
            value={answers.allergensOther}
            onChangeText={(v) => setAnswers({ allergensOther: v })}
            placeholder="Tell us what you're allergic to"
            onLayout={(e) => onOtherLayout("allergens", e)}
            onFocus={() => scrollRef.current?.scrollToEnd({ animated: true })}
            error={attemptedContinue && allergensOtherMissing}
            errorText="Please tell us, or unselect “Others”."
          />
        ) : null}

        <Text style={[styles.sectionLabel, { color: t.colors.textSecondary, fontFamily: t.fonts.bodySemiBold }]}>MEDICAL CONDITIONS</Text>
        <Text style={[styles.hint, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>Optional — you can skip this.</Text>
        <ChipGroup options={MEDICAL_CONDITIONS} selected={answers.medicalConditions} onToggle={(v) => toggleOption("medicalConditions", "medicalConditionsOther", v)} testIDPrefix="onboarding-step4-condition" />
        {answers.medicalConditions.includes("others") ? (
          <OtherInput
            testID="onboarding-step4-condition-other-input"
            value={answers.medicalConditionsOther}
            onChangeText={(v) => setAnswers({ medicalConditionsOther: v })}
            placeholder="Tell us about your condition"
            onLayout={(e) => onOtherLayout("medicalConditions", e)}
            onFocus={() => scrollRef.current?.scrollToEnd({ animated: true })}
            error={attemptedContinue && medicalOtherMissing}
            errorText="Please tell us, or unselect “Others”."
          />
        ) : null}

        {mutation.isError ? (
          <Text style={[styles.errorText, { color: t.colors.primary, fontFamily: t.fonts.bodyMedium }]}>
            {describeApiError(mutation.error)}
          </Text>
        ) : null}
      </ScrollView>

      <View style={[styles.footer, { paddingBottom: insets.bottom + t.spacing.md }]}>
        <Pressable testID="onboarding-step4-continue" disabled={mutation.isPending} onPress={handleContinue} style={({ pressed }) => [styles.button, { backgroundColor: t.colors.selected, opacity: pressed ? 0.9 : 1 }]}>
          <Text style={[styles.buttonLabel, { fontFamily: t.fonts.bodySemiBold, color: t.colors.onSelected }]}>{mutation.isPending ? "Saving..." : "Continue →"}</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

/**
 * OtherInput — the free-text box that appears under Allergies or Medical Conditions once the
 * user selects the "Others" chip, letting them describe what wasn't in the preset list.
 * @param value - the current free-text entry (allergensOther or medicalConditionsOther).
 * @param onChangeText - called as the user types, to update the corresponding answer field.
 * @param placeholder - hint text shown in the empty box (differs per section).
 * @param onLayout - reports this box's position so the screen can auto-scroll it into view
 *                    right after "Others" is selected.
 * @param onFocus - scrolls the screen to the end when the user taps into the box, so the
 *                   keyboard doesn't cover it.
 * @param error - whether to show the box in its error state (user tried to continue with
 *                "Others" selected but this field left blank).
 * @param errorText - the message shown under the box when `error` is true.
 */
function OtherInput({ value, onChangeText, placeholder, onLayout, onFocus, error, errorText, testID }: {
  value: string; onChangeText: (v: string) => void; placeholder: string;
  onLayout?: (e: LayoutChangeEvent) => void; onFocus?: () => void;
  error?: boolean; errorText?: string; testID?: string;
}) {
  const t = useTheme();
  return (
    <View onLayout={onLayout}>
      <TextInput
        testID={testID}
        value={value}
        onChangeText={onChangeText}
        onFocus={onFocus}
        placeholder={placeholder}
        placeholderTextColor={t.colors.textSecondary}
        multiline
        style={[styles.otherInput, { backgroundColor: t.colors.surface, borderColor: error ? t.colors.primary : t.colors.border, color: t.colors.text, fontFamily: t.fonts.body }]}
      />
      {error && errorText ? <Text style={[styles.errorLabel, { color: t.colors.primary, fontFamily: t.fonts.bodyMedium }]}>{errorText}</Text> : null}
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
  otherInput: { minHeight: 52, borderRadius: 14, borderWidth: 1, paddingHorizontal: 16, paddingTop: 14, paddingBottom: 14, fontSize: 16, marginTop: 4 },
  errorLabel: { fontSize: 13, lineHeight: 18, marginTop: 6 },
  errorText: { fontSize: 14, marginTop: 14 },
  footer: { paddingTop: 8 },
  button: { height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center" },
  buttonLabel: { fontSize: 16 },
});

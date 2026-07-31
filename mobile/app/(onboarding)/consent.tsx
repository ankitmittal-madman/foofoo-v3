/**
 * Onboarding Screen 0 — Consent. NEW screen (api-contract-audit-2026-07-30.md HIGH finding:
 * POST /v1/consent was fully built and tested server-side with zero mobile callers). Per
 * DOC-P3-06 §06.1 / DOC-09 §03, personalization consent must be captured BEFORE any
 * dietary/preference data collection begins — this screen is therefore the entry point of the
 * onboarding stack, ahead of step-1 (household composition), not a step appended at the end.
 *
 * Not numbered "1 of 5" alongside the household screens (same convention as create-id.tsx, which
 * also precedes step-1 without being counted) — it is a one-time compliance gate, not a household
 * question.
 *
 * JUDGMENT CALL (flagged per task instruction): consent_records.profile_id has a NOT NULL FK to
 * public.profiles(id) (migration 006), and profiles is only created once ALL FIVE required fields
 * are known — which, in this flow, doesn't happen until step-5 submits successfully. Calling
 * POST /v1/consent from this screen would therefore always fail with a foreign-key violation
 * before any profile exists. Rather than silently doing nothing, or working around the DB
 * constraint (out of scope — database/ and supabase/functions/ are do-not-touch for this fix),
 * the consent DECISION is captured and enforced here (gates progress into step-1, exactly as the
 * contract intends), persisted locally (OnboardingContext), and the actual POST /v1/consent call
 * is fired once a profile can legally exist for it to reference — see step-5.tsx's mutationFn.
 */
import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";

import { useTheme } from "@/theme";
import { useOnboarding } from "@/onboarding/OnboardingContext";
import { PRIVACY_POLICY_VERSION } from "@/onboarding/privacyPolicy";

export default function OnboardingConsent() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const { consent, setConsent, currentStep, restored } = useOnboarding();
  const [attemptedContinue, setAttemptedContinue] = useState(false);

  // Already decided in a prior session on this device (resume logic, Fix 2) — don't re-ask.
  useEffect(() => {
    if (restored && consent.decided) {
      router.replace(`/(onboarding)/step-${Math.min(Math.max(currentStep, 1), 5)}` as never);
    }
  }, [restored, consent.decided, currentStep]);

  if (!restored || consent.decided) {
    return <View style={[styles.root, { backgroundColor: t.colors.background }]} />;
  }

  function handleContinue() {
    if (!consent.personalization) {
      setAttemptedContinue(true);
      return;
    }
    setConsent({ privacyPolicyVersion: PRIVACY_POLICY_VERSION, decided: true });
    router.push("/(onboarding)/step-1");
  }

  return (
    <View style={[styles.root, { backgroundColor: t.colors.background, paddingTop: insets.top + t.spacing.md }]}>
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={[styles.eyebrow, { color: t.colors.primary, fontFamily: t.fonts.bodySemiBold }]}>BEFORE WE START</Text>
        <Text style={[styles.title, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>Your data,{"\n"}your choice</Text>
        <Text style={[styles.subtitle, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>
          We use what you tell us to personalise every recommendation. Here&apos;s what we&apos;d like to do with it.
        </Text>

        <ConsentRow
          label="Personalize my recommendations"
          hint="Required — without this we can't build meal plans around your household."
          value={consent.personalization ?? true}
          onChange={(v) => setConsent({ personalization: v })}
        />
        <ConsentRow
          label="Help improve FooFoo with usage analytics"
          hint="Optional."
          value={consent.analytics ?? true}
          onChange={(v) => setConsent({ analytics: v })}
        />
        <ConsentRow
          label="Send me push notifications"
          hint="Optional — meal reminders and plan updates."
          value={consent.pushNotifications ?? false}
          onChange={(v) => setConsent({ pushNotifications: v })}
        />
        <ConsentRow
          label="Retain my data to improve future plans"
          hint="Optional."
          value={consent.dataRetention ?? true}
          onChange={(v) => setConsent({ dataRetention: v })}
        />

        {attemptedContinue && !consent.personalization ? (
          <Text style={[styles.errorText, { color: t.colors.primary, fontFamily: t.fonts.bodyMedium }]}>
            Personalization consent is required to continue.
          </Text>
        ) : null}
      </ScrollView>

      <View style={[styles.footer, { paddingBottom: insets.bottom + t.spacing.md }]}>
        <Pressable
          onPress={handleContinue}
          style={({ pressed }) => [styles.button, { backgroundColor: t.colors.selected, opacity: pressed ? 0.9 : 1 }]}
        >
          <Text style={[styles.buttonLabel, { fontFamily: t.fonts.bodySemiBold, color: t.colors.onSelected }]}>Continue →</Text>
        </Pressable>
      </View>
    </View>
  );
}

function ConsentRow({
  label,
  hint,
  value,
  onChange,
}: {
  label: string;
  hint: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  const t = useTheme();
  return (
    <View style={[styles.row, { borderColor: t.colors.border }]}>
      <View style={styles.rowText}>
        <Text style={[styles.rowLabel, { color: t.colors.text, fontFamily: t.fonts.bodySemiBold }]}>{label}</Text>
        <Text style={[styles.rowHint, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>{hint}</Text>
      </View>
      <Switch value={value} onValueChange={onChange} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, paddingHorizontal: 24 },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 16 },
  eyebrow: { fontSize: 12, letterSpacing: 1.2, marginBottom: 10 },
  title: { fontSize: 32, lineHeight: 38 },
  subtitle: { fontSize: 15, lineHeight: 22, marginTop: 12, marginBottom: 20 },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderBottomWidth: 1, paddingVertical: 16, gap: 12 },
  rowText: { flex: 1, paddingRight: 12 },
  rowLabel: { fontSize: 15, lineHeight: 20 },
  rowHint: { fontSize: 13, lineHeight: 18, marginTop: 2 },
  errorText: { fontSize: 14, marginTop: 14 },
  footer: { paddingTop: 8 },
  button: { height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center" },
  buttonLabel: { fontSize: 16 },
});

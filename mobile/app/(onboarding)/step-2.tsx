/**
 * Onboarding Screen 2 — "Where are you based?" Adapted from scareme21-create/NewFoo's
 * onboarding/step-2.tsx. Source's "Share my location" GPS card (expo-location, reverse
 * geocoding) was DROPPED per the agreed scope — foofoo-v3 has no GPS integration and no
 * backend field it would feed beyond what a direct city text field already covers.
 * current_city is asked directly instead, as its own required field alongside home
 * state (household/schema.ts's PROFILE_REQUIRED_FIELDS needs both).
 */
import { useMemo, useState } from "react";
import { FlatList, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";

import { useTheme } from "@/theme";
import { useOnboarding } from "@/onboarding/OnboardingContext";
import { StepHeader } from "@/onboarding/OnboardingHeader";
import { INDIAN_STATES } from "@/onboarding/indianStates";
import { step2ToScreens } from "@/onboarding/toHouseholdWrite";
import { postHousehold } from "@/api/household";
import { describeApiError } from "@/api/errorMessages";

export default function OnboardingStep2() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const { answers, setAnswers, setCurrentStep } = useOnboarding();

  const [pickerOpen, setPickerOpen] = useState(false);
  const [query, setQuery] = useState("");

  const homeState = answers.homeState;
  const currentCity = answers.currentCity;
  const canContinue = homeState !== null && !!currentCity?.trim();

  const mutation = useMutation({
    mutationFn: () => postHousehold(step2ToScreens(answers), []),
    onSuccess: () => {
      setCurrentStep(3);
      router.push("/(onboarding)/step-3");
    },
  });

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return INDIAN_STATES;
    return INDIAN_STATES.filter((s) => s.toLowerCase().includes(q));
  }, [query]);

  function selectState(state: string) {
    setAnswers({ homeState: state });
    setPickerOpen(false);
    setQuery("");
  }

  return (
    <View style={[styles.root, { backgroundColor: t.colors.background, paddingTop: insets.top + t.spacing.md }]}>
      <StepHeader current={2} total={5} />

      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={[styles.eyebrow, { color: t.colors.primary, fontFamily: t.fonts.bodySemiBold }]}>STEP 2 — LOCATION</Text>
        <Text style={[styles.title, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>Where are{"\n"}you based?</Text>
        <Text style={[styles.subtitle, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>
          Your home state shapes cuisine identity. Your city helps surface locally available ingredients.
        </Text>

        <Text style={[styles.sectionLabel, { color: t.colors.textSecondary, fontFamily: t.fonts.bodySemiBold }]}>HOME STATE</Text>
        <Text style={[styles.helper, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>
          Determines your regional cuisine affinity — independent of where you currently live.
        </Text>
        <Pressable
          onPress={() => setPickerOpen(true)}
          style={({ pressed }) => [styles.field, { backgroundColor: t.colors.surface, borderColor: t.colors.border, opacity: pressed ? 0.95 : 1 }]}
        >
          <Text style={[styles.fieldText, { color: homeState ? t.colors.text : t.colors.textSecondary, fontFamily: t.fonts.body }]}>
            {homeState ?? "Select your home state"}
          </Text>
          <Text style={[styles.chevron, { color: t.colors.textSecondary }]}>⌄</Text>
        </Pressable>

        <Text style={[styles.sectionLabel, { color: t.colors.textSecondary, fontFamily: t.fonts.bodySemiBold }]}>CURRENT CITY</Text>
        <Text style={[styles.helper, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>Where you live day to day.</Text>
        <TextInput
          value={currentCity ?? ""}
          onChangeText={(v) => setAnswers({ currentCity: v })}
          placeholder="e.g. Pune"
          placeholderTextColor={t.colors.textSecondary}
          style={[styles.input, { backgroundColor: t.colors.surface, borderColor: t.colors.border, color: t.colors.text, fontFamily: t.fonts.body }]}
        />

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

      <Modal visible={pickerOpen} animationType="slide" transparent onRequestClose={() => setPickerOpen(false)}>
        <View style={styles.modalBackdrop}>
          <View style={[styles.modalSheet, { backgroundColor: t.colors.background, paddingBottom: insets.bottom + t.spacing.lg }]}>
            <View style={styles.modalHandleRow}>
              <Text style={[styles.modalTitle, { color: t.colors.heading, fontFamily: t.fonts.headline }]}>Select your home state</Text>
              <Pressable onPress={() => setPickerOpen(false)} hitSlop={8}>
                <Text style={[styles.modalClose, { color: t.colors.textSecondary, fontFamily: t.fonts.bodyMedium }]}>Close</Text>
              </Pressable>
            </View>
            <TextInput
              value={query}
              onChangeText={setQuery}
              placeholder="Search state…"
              placeholderTextColor={t.colors.textSecondary}
              autoCorrect={false}
              style={[styles.search, { backgroundColor: t.colors.surfaceMuted, color: t.colors.text, fontFamily: t.fonts.body }]}
            />
            <FlatList
              data={filtered}
              keyExtractor={(item) => item}
              keyboardShouldPersistTaps="handled"
              style={styles.list}
              renderItem={({ item }) => {
                const selected = item === homeState;
                return (
                  <Pressable onPress={() => selectState(item)} style={({ pressed }) => [styles.row, { opacity: pressed ? 0.6 : 1 }]}>
                    <Text style={[styles.rowText, { color: selected ? t.colors.primary : t.colors.text, fontFamily: selected ? t.fonts.bodySemiBold : t.fonts.body }]}>{item}</Text>
                    {selected ? <Text style={[styles.rowCheck, { color: t.colors.primary }]}>✓</Text> : null}
                  </Pressable>
                );
              }}
              ListEmptyComponent={<Text style={[styles.empty, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>No states match "{query}".</Text>}
            />
          </View>
        </View>
      </Modal>
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
  helper: { fontSize: 14, lineHeight: 20, marginBottom: 12 },
  field: { height: 54, borderRadius: 14, borderWidth: 1, paddingHorizontal: 16, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  fieldText: { fontSize: 16 },
  chevron: { fontSize: 18, marginTop: -4 },
  input: { height: 54, borderRadius: 14, borderWidth: 1, paddingHorizontal: 16, fontSize: 16 },
  errorText: { fontSize: 14, marginTop: 14 },
  footer: { paddingTop: 8 },
  button: { height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center" },
  buttonLabel: { fontSize: 16 },
  modalBackdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.35)", justifyContent: "flex-end" },
  modalSheet: { maxHeight: "80%", borderTopLeftRadius: 24, borderTopRightRadius: 24, paddingHorizontal: 20, paddingTop: 16 },
  modalHandleRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 14 },
  modalTitle: { fontSize: 20, lineHeight: 24 },
  modalClose: { fontSize: 15 },
  search: { height: 48, borderRadius: 12, paddingHorizontal: 14, fontSize: 16, marginBottom: 8 },
  list: { flexGrow: 0 },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingVertical: 14 },
  rowText: { fontSize: 16 },
  rowCheck: { fontSize: 15 },
  empty: { fontSize: 15, textAlign: "center", paddingVertical: 24 },
});

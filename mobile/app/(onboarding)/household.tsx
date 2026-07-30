import { useState } from "react";
import { View, Text, TextInput, Pressable, ScrollView, StyleSheet } from "react-native";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { postHousehold } from "@/api/household";
import type { MemberWrite, ScreenAnswer } from "@/api/types";
import { ApiError } from "@/api/client";

const HOUSEHOLD_TYPES = [
  "single",
  "couple",
  "couple_kids",
  "couple_kids_parents",
  "joint",
  "flatmates",
] as const;

// Migration 033's exact vocabulary (household/schema.ts's MEMBER_CONDITIONS) — this is also what
// compose.ts's memberRole() reads to derive each member's RE role/age-band, so it doubles as the
// Q12 age-band signal (see DOC-P4-03 §3/§4).
const MEMBER_CONDITIONS = [
  "toddler",
  "school_child",
  "teen_high_appetite",
  "elderly_member",
  "baby_6_18m",
  "picky_child",
  "pregnant_member",
  "lactating_or_postpartum_mother",
  "diabetic_member",
  "hypertension_heart_member",
  "gym_high_protein_member",
  "weight_loss_member",
  "fasting_member",
  "jain_member",
  "recovery_member",
] as const;

interface DraftMember {
  memberName: string;
  conditions: string[];
}

export default function Household() {
  const [householdType, setHouseholdType] = useState<(typeof HOUSEHOLD_TYPES)[number] | null>(null);
  const [workingProfessionals, setWorkingProfessionals] = useState("1");
  const [members, setMembers] = useState<DraftMember[]>([]);

  const mutation = useMutation({
    mutationFn: () => {
      const screens: ScreenAnswer[] = [
        { screen_id: "household", question_key: "q1_household_type", answer_value: householdType },
        {
          screen_id: "household",
          question_key: "q2_working_professionals",
          answer_value: Number(workingProfessionals) || 0,
        },
      ];
      const memberWrites: MemberWrite[] = members
        .filter((m) => m.memberName.trim().length > 0)
        .map((m) => ({ member_name: m.memberName, conditions: m.conditions }));
      return postHousehold(screens, memberWrites);
    },
    onSuccess: () => router.push("/(onboarding)/food-and-health"),
  });

  function addMember() {
    setMembers((prev) => [...prev, { memberName: "", conditions: [] }]);
  }

  function updateMember(index: number, patch: Partial<DraftMember>) {
    setMembers((prev) => prev.map((m, i) => (i === index ? { ...m, ...patch } : m)));
  }

  function toggleCondition(index: number, condition: string) {
    setMembers((prev) =>
      prev.map((m, i) => {
        if (i !== index) return m;
        const has = m.conditions.includes(condition);
        return { ...m, conditions: has ? m.conditions.filter((c) => c !== condition) : [...m.conditions, condition] };
      }),
    );
  }

  const canSubmit = householdType !== null;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.progress}>Step 2 of 4</Text>
      <Text style={styles.header}>Who's in your household?</Text>

      <View style={styles.field}>
        <Text style={styles.label}>Household type</Text>
        <View style={styles.chipRow}>
          {HOUSEHOLD_TYPES.map((opt) => (
            <Pressable
              key={opt}
              style={[styles.chip, householdType === opt && styles.chipSelected]}
              onPress={() => setHouseholdType(opt)}
            >
              <Text style={[styles.chipText, householdType === opt && styles.chipTextSelected]}>{opt}</Text>
            </Pressable>
          ))}
        </View>
      </View>

      <View style={styles.field}>
        <Text style={styles.label}>Working professionals in the household</Text>
        <TextInput
          style={styles.input}
          keyboardType="number-pad"
          value={workingProfessionals}
          onChangeText={setWorkingProfessionals}
        />
      </View>

      <View style={styles.field}>
        <Text style={styles.label}>Household members (optional)</Text>
        {members.map((m, i) => (
          <View key={i} style={styles.memberCard}>
            <TextInput
              style={styles.input}
              placeholder="Name"
              value={m.memberName}
              onChangeText={(v) => updateMember(i, { memberName: v })}
            />
            <View style={styles.chipRow}>
              {MEMBER_CONDITIONS.map((c) => (
                <Pressable
                  key={c}
                  style={[styles.chipSmall, m.conditions.includes(c) && styles.chipSelected]}
                  onPress={() => toggleCondition(i, c)}
                >
                  <Text style={[styles.chipText, m.conditions.includes(c) && styles.chipTextSelected]}>{c}</Text>
                </Pressable>
              ))}
            </View>
          </View>
        ))}
        <Pressable style={styles.secondaryButton} onPress={addMember}>
          <Text style={styles.secondaryButtonText}>+ Add member</Text>
        </Pressable>
      </View>

      {mutation.isError ? (
        <Text style={styles.error}>
          {mutation.error instanceof ApiError ? mutation.error.message : "Something went wrong"}
        </Text>
      ) : null}

      <Pressable
        style={[styles.button, !canSubmit && styles.buttonDisabled]}
        disabled={!canSubmit || mutation.isPending}
        onPress={() => mutation.mutate()}
      >
        <Text style={styles.buttonText}>{mutation.isPending ? "Saving..." : "Continue"}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 16 },
  progress: { color: "#6B6B6B", fontSize: 12, textTransform: "uppercase" },
  header: { fontSize: 24, fontWeight: "600", marginBottom: 8 },
  field: { gap: 6 },
  label: { fontSize: 14, color: "#3A3A3A" },
  input: { borderWidth: 1, borderColor: "#D1D1D1", borderRadius: 8, padding: 12 },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: { borderWidth: 1, borderColor: "#D1D1D1", borderRadius: 20, paddingVertical: 8, paddingHorizontal: 14 },
  chipSmall: { borderWidth: 1, borderColor: "#D1D1D1", borderRadius: 20, paddingVertical: 6, paddingHorizontal: 10 },
  chipSelected: { backgroundColor: "#1F7A3F", borderColor: "#1F7A3F" },
  chipText: { color: "#1C1C1E", fontSize: 13 },
  chipTextSelected: { color: "white" },
  memberCard: { borderWidth: 1, borderColor: "#E5E5E5", borderRadius: 8, padding: 12, gap: 8 },
  secondaryButton: { alignSelf: "flex-start" },
  secondaryButtonText: { color: "#1F7A3F", fontWeight: "600" },
  button: { backgroundColor: "#1F7A3F", borderRadius: 8, padding: 14, alignItems: "center", marginTop: 8 },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: "white", fontWeight: "600" },
  error: { color: "#C0392B" },
});

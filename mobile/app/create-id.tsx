/**
 * Create ID — capture the display name after sign-up, before onboarding. Ported from
 * scareme21-create/NewFoo's create-id.tsx. Source only saved this to Supabase Auth
 * user_metadata (its onboarding profile had no name field at all); here it is ALSO
 * submitted as profiles.primary_cook_name via POST /v1/household — one of the five
 * fields household/handler.ts requires before it will create a profile.
 */
import { useEffect, useState } from "react";
import { ActivityIndicator, Keyboard, KeyboardAvoidingView, Platform, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { router } from "expo-router";
import { useMutation } from "@tanstack/react-query";

import { supabase } from "@/auth/supabaseClient";
import { useTheme } from "@/theme";
import { postHousehold } from "@/api/household";
import { describeApiError } from "@/api/errorMessages";

export default function CreateId() {
  const t = useTheme();
  const [name, setName] = useState("");

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      const m = data.user?.user_metadata ?? {};
      const guess = m.display_name || m.full_name || m.name;
      if (guess) setName(String(guess));
    });
  }, []);

  const mutation = useMutation({
    mutationFn: async () => {
      await supabase.auth.updateUser({ data: { display_name: name.trim() } });
      return postHousehold(
        [{ screen_id: "create-id", question_key: "primary_cook_name", answer_value: name.trim() }],
        [],
      );
    },
    // Consent (DOC-P3-06 §06.1) must be captured before step-1's dietary/preference collection
    // begins (Fix 5) — create-id now routes into the consent screen first, not straight to step-1.
    onSuccess: () => router.replace("/(onboarding)/consent"),
  });

  const canContinue = name.trim().length > 0 && !mutation.isPending;

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: t.colors.background }]}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <Pressable style={styles.flex} onPress={() => Platform.OS !== "web" && Keyboard.dismiss()} accessible={false}>
        <View style={styles.content}>
          <Text style={[styles.title, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>
            What should we{"\n"}call you?
          </Text>
          <Text style={[styles.subtitle, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>
            This is the name FooFoo will greet you with.
          </Text>

          <Text style={[styles.label, { color: t.colors.textSecondary, fontFamily: t.fonts.bodyMedium }]}>YOUR NAME</Text>
          <TextInput
            testID="create-id-name"
            value={name}
            onChangeText={setName}
            placeholder="e.g. Pratikshit"
            placeholderTextColor={t.colors.textSecondary}
            autoCapitalize="words"
            autoCorrect={false}
            returnKeyType="done"
            editable={!mutation.isPending}
            style={[styles.input, { backgroundColor: t.colors.surface, borderColor: t.colors.border, color: t.colors.text, fontFamily: t.fonts.body }]}
          />

          {mutation.isError ? (
            <Text style={[styles.msg, { color: t.colors.primary, fontFamily: t.fonts.bodyMedium }]}>
              {describeApiError(mutation.error)}
            </Text>
          ) : null}

          <View style={styles.actions}>
            <Pressable
              testID="create-id-continue"
              disabled={!canContinue}
              onPress={() => mutation.mutate()}
              style={[styles.button, { backgroundColor: canContinue ? t.colors.selected : t.colors.disabled }]}
            >
              {mutation.isPending ? (
                <ActivityIndicator color={t.colors.onSelected} />
              ) : (
                <Text style={[styles.buttonLabel, { fontFamily: t.fonts.bodySemiBold, color: canContinue ? t.colors.onSelected : t.colors.onDisabled }]}>
                  Continue →
                </Text>
              )}
            </Pressable>
          </View>
        </View>
      </Pressable>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", paddingHorizontal: 28 },
  flex: { flex: 1, justifyContent: "center" },
  content: { alignSelf: "stretch" },
  title: { fontSize: 32, lineHeight: 38 },
  subtitle: { fontSize: 15, lineHeight: 22, marginTop: 12, marginBottom: 28 },
  label: { fontSize: 12, letterSpacing: 1, marginBottom: 8 },
  input: { height: 52, borderRadius: 14, borderWidth: 1, paddingHorizontal: 16, fontSize: 16 },
  msg: { fontSize: 14, marginTop: 12 },
  actions: { marginTop: 28 },
  button: { height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center" },
  buttonLabel: { fontSize: 16 },
});

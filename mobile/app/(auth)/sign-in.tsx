/**
 * Sign in / Create account (email + password) — ported from scareme21-create/NewFoo's
 * sign-in.tsx. Uses supabase directly (not SessionContext's thinner wrapper) so the
 * signup-without-session case (email confirmation required) can be handled explicitly,
 * same as source; SessionContext's own onAuthStateChange listener still picks up the
 * resulting session automatically for the rest of the app. Post sign-up now routes to
 * /create-id and post sign-in to "/today" (the (tabs) group's Home tab) — this repo's real
 * screens, not source's /plan (which was never built here) or /authed (a throwaway
 * source screen, not ported). Home previously was /recommendations' plate-feed; the
 * frontend restructuring retired that as the landing surface in favor of today's
 * breakfast/lunch/dinner selection. Goes straight to "/today", not "/" — "/" is
 * app/index.tsx's own auth/onboarding gate, which would just redirect here again.
 */
import { useState } from "react";
import { ActivityIndicator, Keyboard, KeyboardAvoidingView, Platform, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";

import { supabase } from "@/auth/supabaseClient";
import { useTheme } from "@/theme";
import { fetchOnboardingStatus } from "@/api/household";
import { logger } from "@/lib/logger";

type Mode = "signin" | "signup";

export default function SignIn() {
  const t = useTheme();
  const params = useLocalSearchParams<{ mode?: string }>();
  const [mode, setMode] = useState<Mode>(params.mode === "signup" ? "signup" : "signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const canSubmit = email.trim().length > 0 && password.length >= 6 && !loading;
  const title = mode === "signin" ? "Welcome back" : "Create your account";
  const cta = mode === "signin" ? "Sign In" : "Create Account";

  function switchMode(m: Mode) {
    setMode(m);
    setErrorMsg(null);
    setNotice(null);
  }

  async function handleSubmit() {
    setLoading(true);
    setErrorMsg(null);
    setNotice(null);
    try {
      if (mode === "signup") {
        const { data, error } = await supabase.auth.signUp({ email: email.trim(), password });
        if (error) {
          setErrorMsg(error.message);
          return;
        }
        if (!data.session) {
          setNotice("Account created. Check your email to confirm, then sign in.");
          setMode("signin");
          return;
        }
        router.replace("/create-id");
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
        if (error) {
          setErrorMsg(error.message);
          return;
        }
        // Fix (audit-onboarding-funnel HIGH finding): this used to route straight to
        // /recommendations regardless of whether onboarding had ever been completed, bypassing it
        // entirely and contradicting index.tsx's own routing rule. Both now share the same source
        // of truth (household.ts's fetchOnboardingStatus — see its header comment). If the status
        // check itself fails (e.g. network), fail toward onboarding rather than assuming
        // completion — same reasoning as index.tsx's fallback, and it's idempotent to revisit.
        const status = await fetchOnboardingStatus().catch((e) => {
          logger.warn("sign_in.onboarding_status_check_failed", {
            detail: e instanceof Error ? e.message : String(e),
          });
          return null;
        });
        router.replace(status?.complete ? "/today" : "/(onboarding)/consent");
      }
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: t.colors.background }]}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <Pressable style={styles.flex} onPress={() => Platform.OS !== "web" && Keyboard.dismiss()} accessible={false}>
        <View style={styles.content}>
          <View style={[styles.toggle, { backgroundColor: t.colors.surfaceMuted, borderColor: t.colors.border }]}>
            {(["signin", "signup"] as Mode[]).map((m) => {
              const active = mode === m;
              return (
                <Pressable
                  key={m}
                  onPress={() => switchMode(m)}
                  style={[styles.toggleItem, active && { backgroundColor: t.colors.selected }]}
                >
                  <Text
                    style={[
                      styles.toggleLabel,
                      { fontFamily: t.fonts.bodySemiBold, color: active ? t.colors.onSelected : t.colors.textSecondary },
                    ]}
                  >
                    {m === "signin" ? "Sign In" : "Sign Up"}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <Text style={[styles.title, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>{title}</Text>

          <Text style={[styles.label, { color: t.colors.textSecondary, fontFamily: t.fonts.bodyMedium }]}>EMAIL</Text>
          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="you@example.com"
            placeholderTextColor={t.colors.textSecondary}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            editable={!loading}
            style={[styles.input, { backgroundColor: t.colors.surface, borderColor: t.colors.border, color: t.colors.text, fontFamily: t.fonts.body }]}
          />

          <Text style={[styles.label, { color: t.colors.textSecondary, fontFamily: t.fonts.bodyMedium }]}>PASSWORD</Text>
          <TextInput
            value={password}
            onChangeText={setPassword}
            placeholder="At least 6 characters"
            placeholderTextColor={t.colors.textSecondary}
            secureTextEntry
            autoCapitalize="none"
            editable={!loading}
            style={[styles.input, { backgroundColor: t.colors.surface, borderColor: t.colors.border, color: t.colors.text, fontFamily: t.fonts.body }]}
          />

          {errorMsg ? <Text style={[styles.msg, { color: t.colors.primary, fontFamily: t.fonts.bodyMedium }]}>{errorMsg}</Text> : null}
          {notice ? <Text style={[styles.msg, { color: t.colors.success, fontFamily: t.fonts.bodyMedium }]}>{notice}</Text> : null}

          <Pressable
            disabled={!canSubmit}
            onPress={handleSubmit}
            style={[styles.button, { backgroundColor: canSubmit ? t.colors.selected : t.colors.disabled }]}
          >
            {loading ? (
              <ActivityIndicator color={t.colors.onSelected} />
            ) : (
              <Text style={[styles.buttonLabel, { fontFamily: t.fonts.bodySemiBold, color: canSubmit ? t.colors.onSelected : t.colors.onDisabled }]}>
                {cta} →
              </Text>
            )}
          </Pressable>
        </View>
      </Pressable>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", paddingHorizontal: 28 },
  flex: { flex: 1, justifyContent: "center" },
  content: { alignSelf: "stretch" },
  toggle: { flexDirection: "row", borderRadius: 28, borderWidth: 1, padding: 4, marginBottom: 28 },
  toggleItem: { flex: 1, height: 44, borderRadius: 24, alignItems: "center", justifyContent: "center" },
  toggleLabel: { fontSize: 14 },
  title: { fontSize: 30, lineHeight: 36, marginBottom: 24 },
  label: { fontSize: 12, letterSpacing: 1, marginBottom: 8, marginTop: 8 },
  input: { height: 52, borderRadius: 14, borderWidth: 1, paddingHorizontal: 16, fontSize: 16, marginBottom: 8 },
  msg: { fontSize: 14, marginTop: 8, marginBottom: 4 },
  button: { height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center", marginTop: 24 },
  buttonLabel: { fontSize: 16 },
});

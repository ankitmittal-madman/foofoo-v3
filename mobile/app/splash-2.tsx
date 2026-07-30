/**
 * Welcome / value screen — ported from scareme21-create/NewFoo's splash-2.tsx (backend-
 * independent, pure marketing copy). Entering-animation wrappers (react-native-reanimated)
 * were dropped to avoid adding that dependency for a Phase-1 scaffold; layout/copy/theme
 * are otherwise unchanged.
 */
import { router } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useTheme } from "@/theme";

export default function SplashTwo() {
  const t = useTheme();
  return (
    <View style={[styles.container, { backgroundColor: t.colors.background }]}>
      <View style={styles.content}>
        <Text style={[styles.headline, { color: t.colors.heading, fontFamily: t.fonts.headlineBold }]}>
          Never wonder{"\n"}what&apos;s for dinner.
        </Text>
        <Text style={[styles.subtext, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>
          FooFoo plans your breakfast, lunch, and dinner around your home, your taste, and your day
          — so you don&apos;t have to.
        </Text>

        <View style={styles.actions}>
          <Pressable
            onPress={() => router.push("/(auth)/sign-in?mode=signup")}
            style={({ pressed }) => [styles.button, { backgroundColor: t.colors.selected, opacity: pressed ? 0.9 : 1 }]}
          >
            <Text style={[styles.buttonLabel, { color: t.colors.onSelected, fontFamily: t.fonts.bodySemiBold }]}>
              Get Started →
            </Text>
          </Pressable>

          <Pressable onPress={() => router.push("/(auth)/sign-in?mode=signin")} style={styles.linkWrap}>
            <Text style={[styles.link, { color: t.colors.textSecondary, fontFamily: t.fonts.bodyMedium }]}>
              I already have an account
            </Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", paddingHorizontal: 28 },
  content: { alignItems: "flex-start" },
  headline: { fontSize: 34, lineHeight: 40 },
  subtext: { fontSize: 15, lineHeight: 22, marginTop: 16 },
  actions: { alignSelf: "stretch", marginTop: 40 },
  button: { height: 56, borderRadius: 28, alignItems: "center", justifyContent: "center" },
  buttonLabel: { fontSize: 16 },
  linkWrap: { alignItems: "center", marginTop: 16, paddingVertical: 8 },
  link: { fontSize: 14 },
});

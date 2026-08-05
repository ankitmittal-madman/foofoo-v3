import { Tabs } from "expo-router";
import { Text } from "react-native";
import { palette } from "@/ui/foofoo";
import { useI18n } from "@/i18n";

/**
 * TabsLayout — the persistent bottom-nav for the app's two main day-to-day surfaces. Home (today's
 * meal selection, "today.tsx") is listed first / lands first; Week Plan (the 7-day class picker,
 * formerly a mid-flow cold-start step) is second, per the Founder's requested ordering.
 *
 * Home is deliberately NOT named "index" here: the top-level app/index.tsx (outside this group)
 * is the real auth/onboarding-status gate for "/" and redirects completed users into this tab —
 * naming this screen "index" too would make BOTH files resolve to the same "/" route (an actual
 * route collision / self-redirect loop, not just an unlikely edge case), so this screen lives at
 * "/today" instead and app/index.tsx's redirect targets that path.
 */
export default function TabsLayout() {
  const { t } = useI18n();
  return (
    <Tabs initialRouteName="today" screenOptions={{ headerShown: false, tabBarActiveTintColor: palette.purple, tabBarInactiveTintColor: "#777078", tabBarStyle: { height: 76, paddingTop: 7, paddingBottom: 10, borderTopColor: palette.line, backgroundColor: "#FFFCF8" }, tabBarLabelStyle: { fontSize: 10, fontWeight: "600" } }}>
      <Tabs.Screen name="today" options={{ title: t("home"), tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>⌂</Text> }} />
      <Tabs.Screen name="weekly-plan" options={{ title: t("weekly"), tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>▦</Text> }} />
      <Tabs.Screen name="pantry" options={{ title: t("pantry"), tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>♙</Text> }} />
      <Tabs.Screen name="chat" options={{ title: t("chat"), tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>◌</Text> }} />
      <Tabs.Screen name="profile" options={{ title: t("profile"), tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 18 }}>♙</Text> }} />
      <Tabs.Screen name="search" options={{ href: null }} />
      <Tabs.Screen name="settings" options={{ href: null }} />
    </Tabs>
  );
}

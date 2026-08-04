import { Tabs } from "expo-router";

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
  return (
    <Tabs initialRouteName="today" screenOptions={{ headerShown: false }}>
      <Tabs.Screen name="today" options={{ title: "Home" }} />
      <Tabs.Screen name="weekly-plan" options={{ title: "Week Plan" }} />
    </Tabs>
  );
}

/**
 * Shared onboarding chrome — the "N of total" progress bar and Back control that top
 * every onboarding screen. Ported from scareme21-create/NewFoo's OnboardingHeader.tsx.
 */
import { Pressable, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";

import { useTheme } from "@/theme";

export function StepHeader({
  current,
  total,
  showBack = true,
}: {
  current: number;
  total: number;
  showBack?: boolean;
}) {
  const t = useTheme();
  return (
    <View>
      <View style={styles.progressRow}>
        {Array.from({ length: total }).map((_, i) => {
          const done = i < current;
          const isCurrent = i === current - 1;
          return (
            <View
              key={i}
              style={[
                styles.progressSeg,
                { width: isCurrent ? 24 : 14, backgroundColor: done ? t.colors.selected : t.colors.border },
              ]}
            />
          );
        })}
        <Text style={[styles.progressText, { color: t.colors.textSecondary, fontFamily: t.fonts.body }]}>
          {current} of {total}
        </Text>
      </View>

      {showBack ? (
        <Pressable onPress={() => router.back()} style={styles.backRow} hitSlop={8}>
          <Text style={[styles.back, { color: t.colors.text, fontFamily: t.fonts.bodyMedium }]}>← Back</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  progressRow: { flexDirection: "row", alignItems: "center", marginBottom: 20 },
  progressSeg: { height: 4, borderRadius: 2, marginRight: 6 },
  progressText: { fontSize: 13, marginLeft: 4 },
  backRow: { marginBottom: 12, paddingVertical: 2, alignSelf: "flex-start" },
  back: { fontSize: 15 },
});

/**
 * Shared multi-select pill group for onboarding follow-ups — ported from
 * scareme21-create/NewFoo's foofoo/src/onboarding/OnboardingChips.tsx verbatim (generic,
 * no backend coupling). Exclusivity (e.g. a "None"/"Any" option) is the caller's concern.
 */
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useTheme } from "@/theme";

export type ChipOption = { value: string; label: string };

export function ChipGroup({
  options,
  selected,
  onToggle,
  testIDPrefix,
}: {
  options: ChipOption[];
  selected: string[];
  onToggle: (value: string) => void;
  // Additive, optional: lets each onboarding screen give its chip instances a stable,
  // screen-scoped testID (e.g. "onboarding-step3-meat-chicken") for the WP-22 UI journey
  // driver, without every call site needing its own bespoke chip component.
  testIDPrefix?: string;
}) {
  const t = useTheme();
  return (
    <View style={styles.chips}>
      {options.map((opt) => {
        const on = selected.includes(opt.value);
        return (
          <Pressable
            key={opt.value}
            testID={testIDPrefix ? `${testIDPrefix}-${opt.value}` : undefined}
            onPress={() => onToggle(opt.value)}
            style={({ pressed }) => [
              styles.chip,
              {
                backgroundColor: on ? t.colors.selected : t.colors.surface,
                borderColor: on ? t.colors.selected : t.colors.border,
                opacity: pressed ? 0.9 : 1,
              },
            ]}
          >
            <Text
              numberOfLines={1}
              style={[
                styles.chipLabel,
                { color: on ? t.colors.onSelected : t.colors.text, fontFamily: on ? t.fonts.bodySemiBold : t.fonts.body },
              ]}
            >
              {opt.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  chips: { flexDirection: "row", flexWrap: "wrap" },
  chip: { borderRadius: 22, borderWidth: 1, paddingVertical: 10, paddingHorizontal: 16, marginRight: 10, marginBottom: 10 },
  chipLabel: { fontSize: 14, lineHeight: 18 },
});

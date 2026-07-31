import { View, type ViewProps } from "react-native";

import { ThemeColor } from "@/theme/theme";
import { useTheme } from "@/hooks/useTheme";

export type ThemedViewProps = ViewProps & {
  lightColor?: string;
  darkColor?: string;
  type?: ThemeColor;
};

/**
 * ThemedView — a plain React Native `View` that fills its background from the active
 * light/dark theme (via useTheme) instead of a hardcoded color, so screens built on the
 * older theme system stay correct in both appearance modes.
 * @param type - which theme color token to use for the background (defaults to "background");
 *               matches one of theme/theme.ts's `Colors` keys (e.g. "backgroundElement").
 * @param lightColor - currently accepted but unused; the color always comes from the active
 *                      theme's `type` token rather than a per-instance override.
 * @param darkColor - same as lightColor — accepted for prop-shape compatibility, unused.
 */
export function ThemedView({ style, lightColor, darkColor, type, ...otherProps }: ThemedViewProps) {
  const theme = useTheme();

  return <View style={[{ backgroundColor: theme[type ?? "background"] }, style]} {...otherProps} />;
}

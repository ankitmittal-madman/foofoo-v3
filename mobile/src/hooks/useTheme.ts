import { Colors } from "@/theme/theme";
import { useColorScheme } from "@/hooks/useColorScheme";

/**
 * useTheme — returns the plain light/dark color token set (theme/theme.ts's `Colors`) matching
 * the device's current appearance setting, defaulting to "light" if the OS reports none.
 * Used by the older ThemedText/ThemedView components. Distinct from `@/theme`'s useTheme, which
 * returns the richer "ghar" brand theme (colors/spacing/fonts) that the real onboarding/auth
 * screens are built on — see theme/index.tsx's header note for why both exist side by side.
 * @returns the color token object for the active scheme (e.g. `{ text, background, ... }`).
 */
export function useTheme() {
  const scheme = useColorScheme();
  const theme = scheme ?? "light";

  return Colors[theme];
}

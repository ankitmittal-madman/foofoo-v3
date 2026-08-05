/**
 * Ghar theme system — ported from scareme21-create/NewFoo's foofoo/src/theme/index.tsx
 * (the warm terracotta/cream visual identity behind its real onboarding screens). Kept
 * separate from ../theme/theme.ts (the earlier, plainer light/dark tokens ported previously)
 * on the same rationale the source repo gives: existing code keeps working while screens
 * built on this richer system sit alongside it.
 */
import React, { createContext, useContext, useMemo, useState } from "react";

const ghar = {
  name: "ghar",
  colors: {
    background: "#FAF7F2",
    surface: "#FFFFFF",
    surfaceMuted: "#F5EFE6",
    primary: "#7C4DFF",
    accent: "#F4B740",
    heading: "#1F1F24",
    text: "#1F1F24",
    textSecondary: "#6B6B76",
    border: "#E8E1D8",
    selected: "#7C4DFF",
    onSelected: "#FFFFFF",
    check: "#7C4DFF",
    success: "#2FBF71",
    disabled: "#E8E1D8",
    onDisabled: "#9B959D",
  },
  spacing: { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 },
  radius: { sm: 12, card: 16, pill: 28 },
  fonts: {
    headline: "Fraunces_600SemiBold",
    headlineBold: "Fraunces_700Bold",
    body: "Mukta_400Regular",
    bodyMedium: "Mukta_500Medium",
    bodySemiBold: "Mukta_600SemiBold",
  },
} as const;

export const themes = { ghar } as const;
export type ThemeName = keyof typeof themes;
export type Theme = typeof ghar;

type ThemeContextValue = {
  theme: Theme;
  themeName: ThemeName;
  setThemeName: (name: ThemeName) => void;
};

const ThemeContext = createContext<ThemeContextValue>({
  theme: themes.ghar,
  themeName: "ghar",
  setThemeName: () => {},
});

/**
 * ThemeProvider — wraps the whole app (mounted once in app/_layout.tsx, nested inside
 * SessionProvider) and makes the "ghar" brand theme (colors, spacing, radius, fonts) available
 * to every screen via useTheme(). Only one theme currently exists, so `setThemeName` is
 * forward-looking scaffolding rather than something any screen calls today.
 * @param children - the rest of the app tree, themed once this provider is mounted.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [themeName, setThemeName] = useState<ThemeName>("ghar");
  const value = useMemo(() => ({ theme: themes[themeName], themeName, setThemeName }), [themeName]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * useTheme — reads the active brand theme object (colors/spacing/radius/fonts) that every
 * real onboarding, sign-in, and splash screen renders with. This is the "ghar" theme system,
 * not the older light/dark `@/hooks/useTheme` used by ThemedText/ThemedView.
 * @returns the current Theme object, e.g. `t.colors.background`, `t.fonts.headlineBold`.
 */
export function useTheme(): Theme {
  return useContext(ThemeContext).theme;
}

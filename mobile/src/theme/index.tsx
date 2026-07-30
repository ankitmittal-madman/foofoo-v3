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
    background: "#FBF3E4",
    surface: "#FFFFFF",
    surfaceMuted: "#F5EDDD",
    primary: "#C75B39",
    accent: "#E8A33D",
    heading: "#2A211C",
    text: "#2A211C",
    textSecondary: "#8B8177",
    border: "#E8DEC8",
    selected: "#1C1A18",
    onSelected: "#FFFFFF",
    check: "#C75B39",
    success: "#3F7A5A",
    disabled: "#E4DBC9",
    onDisabled: "#A99F8D",
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

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [themeName, setThemeName] = useState<ThemeName>("ghar");
  const value = useMemo(() => ({ theme: themes[themeName], themeName, setThemeName }), [themeName]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): Theme {
  return useContext(ThemeContext).theme;
}

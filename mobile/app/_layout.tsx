import { Stack } from "expo-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { StatusBar } from "expo-status-bar";
import { useFonts } from "expo-font";
import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";
import { Fraunces_600SemiBold, Fraunces_700Bold } from "@expo-google-fonts/fraunces";
import { Mukta_400Regular, Mukta_500Medium, Mukta_600SemiBold } from "@expo-google-fonts/mukta";

import { SessionProvider } from "@/auth/SessionContext";
import { queryClient } from "@/lib/queryClient";
import { ThemeProvider, useTheme } from "@/theme";

// Ghar theme + brand fonts (Fraunces/Mukta) ported from scareme21-create/NewFoo's root
// layout — held the native splash until fonts are ready, so the first frame never
// flashes a system font before Fraunces/Mukta load.
SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout() {
  const [loaded, error] = useFonts({
    Fraunces_600SemiBold,
    Fraunces_700Bold,
    Mukta_400Regular,
    Mukta_500Medium,
    Mukta_600SemiBold,
  });

  useEffect(() => {
    if (loaded || error) {
      SplashScreen.hideAsync().catch(() => {});
    }
  }, [loaded, error]);

  if (!loaded && !error) {
    return null;
  }

  return (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <ThemeProvider>
          <RootNavigator />
        </ThemeProvider>
      </SessionProvider>
    </QueryClientProvider>
  );
}

function RootNavigator() {
  const t = useTheme();
  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: t.colors.background } }} />
    </>
  );
}

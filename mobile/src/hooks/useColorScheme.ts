/**
 * useColorScheme — re-exports React Native's own device color-scheme hook (returns
 * "light" | "dark" | null based on the OS setting) so app code imports it from a single
 * `@/hooks/useColorScheme` path. The web build overrides this with useColorScheme.web.ts
 * instead, since a static web export has no OS-level scheme to read until after hydration.
 */
export { useColorScheme } from "react-native";

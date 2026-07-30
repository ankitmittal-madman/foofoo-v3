import { Colors } from "@/theme/theme";
import { useColorScheme } from "@/hooks/useColorScheme";

export function useTheme() {
  const scheme = useColorScheme();
  const theme = scheme ?? "light";

  return Colors[theme];
}

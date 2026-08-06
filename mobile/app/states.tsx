import { ScrollView, StyleSheet, View } from "react-native";

import { useI18n } from "@/i18n";
import { Skeleton, StateCard, palette } from "@/ui/foofoo";

export default function States() {
  const { t } = useI18n();

  return (
    <ScrollView style={s.screen} contentContainerStyle={s.page}>
      <StateCard
        icon="🍽️"
        title="No meals planned yet" // NOTE: Using a placeholder title. Consider adding a specific key to i18n.
        body="Build your first weekly plan and make today easier."
        action="Create a plan"
      />
      <StateCard
        icon="⌁"
        title={t("noSafeMeal")} // Re-using an existing key that fits the context.
        body={t("savedMealFallback")}
      />
      <StateCard
        icon="!"
        title="Something went wrong" // NOTE: Using a placeholder title.
        body="We couldn’t load your meals. Please try again."
        action={t("tryAgain")}
      />
      <View style={s.loading}>
        <Skeleton height={180} />
        <Skeleton />
        <Skeleton />
        <Skeleton height={52} />
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.bg },
  page: { padding: 18, gap: 18 },
  loading: { gap: 10, padding: 16, backgroundColor: "white", borderRadius: 16 },
});

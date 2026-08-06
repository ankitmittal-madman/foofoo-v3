import { useState } from "react";
import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { fetchMealEpisodes, type Slot } from "@/api/plan";
import { FButton, palette } from "@/ui/foofoo";

const FOOD = require("../assets/images/poha-idli-fruit.png");

export default function Alternatives() {
  const params = useLocalSearchParams<{ slot?: string; weekday?: string; classCode?: string }>();
  const slot: Slot = params.slot === "lunch" || params.slot === "dinner" ? params.slot : "breakfast";
  const [generation, setGeneration] = useState(1);
  const query = useQuery({
    queryKey: ["meal-alternatives", slot, params.weekday, params.classCode, generation],
    queryFn: () => fetchMealEpisodes(slot, {
      weekday: params.weekday,
      class_code: params.classCode,
      count: 4,
      refresh_generation: generation,
    }),
    staleTime: 0,
    gcTime: 0,
  });

  return <ScrollView style={s.screen} contentContainerStyle={s.page}>
    <View style={s.header}><Pressable onPress={() => router.back()}><Text style={s.back}>‹</Text></Pressable><Text style={s.title}>{slot[0].toUpperCase() + slot.slice(1)} alternatives</Text><View /></View>
    <Text style={s.body}>Fresh alternatives stay within your safety and meal constraints.</Text>
    {query.isLoading ? <ActivityIndicator color={palette.purple} /> : null}
    {(query.data?.episodes ?? []).map((episode, index) => {
      const imageUrl = episode.components.find((component) => component.image_url)?.image_url;
      return <Pressable key={episode.episode_hash} style={[s.card, index === 0 && s.active]} onPress={() => router.replace({ pathname: "/meal-detail", params: { meal: episode.display_name, slot } })}>
        <Image source={imageUrl ? { uri: imageUrl } : FOOD} style={s.image} />
        <View style={s.copy}><Text style={s.name}>{episode.display_name}</Text><Text style={s.meta}>{episode.practicality.active_minutes} active min</Text></View>
        <Text style={s.radio}>{index === 0 ? "●" : "○"}</Text>
      </Pressable>;
    })}
    {query.isError ? <Text style={s.error}>Could not load alternatives. Please try again.</Text> : null}
    <FButton label="Regenerate alternatives" kind="secondary" onPress={() => setGeneration((value) => value + 1)} />
  </ScrollView>;
}

const s = StyleSheet.create({ screen: { flex: 1, backgroundColor: palette.bg }, page: { padding: 18, gap: 12 }, header: { height: 50, flexDirection: "row", alignItems: "center", justifyContent: "space-between" }, back: { fontSize: 34 }, title: { fontSize: 17, fontWeight: "800" }, body: { color: palette.muted, lineHeight: 19, marginBottom: 6 }, card: { flexDirection: "row", alignItems: "center", gap: 12, padding: 10, borderRadius: 15, backgroundColor: "white", borderWidth: 1, borderColor: palette.line }, active: { borderColor: palette.green }, image: { width: 70, height: 62, borderRadius: 11 }, copy: { flex: 1 }, name: { fontWeight: "800", color: palette.ink }, meta: { fontSize: 11, color: palette.muted, marginTop: 4 }, radio: { fontSize: 20, color: palette.green }, error: { color: palette.red } });

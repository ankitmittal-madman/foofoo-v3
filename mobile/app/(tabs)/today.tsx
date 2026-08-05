import { useState } from "react";
import { Image, ImageBackground, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { fetchClassDishes, fetchSlotOptions, setPlanSlotLock } from "@/api/plan";
import { postFeedback } from "@/api/feedback";
import type { PlanDish } from "@/api/plan";
import type { FeedbackEventType } from "@/api/types";
import type { SlotName } from "@/lib/weeklyPlanStore";
import { palette, Toast } from "@/ui/foofoo";
import { useI18n } from "@/i18n";

const HERO = require("../../assets/images/poha-idli-fruit.png");
const meals = [
  { key: "breakfast", title: "Poha, Idli & Fruit Bowl", time: "7:30 AM", caption: "Light · Balanced · Quick to make" },
  { key: "lunch", title: "Dal, Rice, Sabzi & Salad", time: "1:30 PM", caption: "Wholesome · Homely · Protein-rich" },
  { key: "dinner", title: "Veg Khichdi & Kadhi", time: "8:00 PM", caption: "Comforting · Light · Family favourite" },
] as const;

export default function Home() {
  const { t } = useI18n();
  const [active, setActive] = useState(0);
  const [liked, setLiked] = useState(false);
  const [toast, setToast] = useState("");
  const meal = meals[active];
  const flash = (message: string) => { setToast(message); setTimeout(() => setToast(""), 1800); };
  const next = () => setActive((active + 1) % meals.length);

  return (
    <View style={styles.screen} testID="home-screen">
      <ScrollView contentContainerStyle={styles.page} showsVerticalScrollIndicator={false}>
        <View style={styles.brandRow}><View><Text style={styles.brand}>FooFoo<Text style={styles.brandMark}>♡</Text></Text><Text style={styles.tagline}>AI Meal Decision Platform{`\n`}for your household</Text></View><Pressable onPress={() => router.push("/notifications")} style={styles.topIcon}><Text>♧</Text><View style={styles.dot} /></Pressable></View>
        <Text style={styles.greeting}>{t("greeting")}</Text><Text style={styles.question}>{t("question")}</Text>
        <View style={styles.insight}><Text style={styles.insightIcon}>✦</Text><Text style={styles.insightText}>{t("insight")}</Text></View>

        <View style={styles.heroCard}>
          <ImageBackground source={HERO} style={styles.hero} imageStyle={styles.heroImage}>
            <View style={styles.heroShade} />
            <View style={styles.mealBadge}><Text style={styles.mealBadgeText}>{t(meal.key)}</Text></View>
            <View style={styles.heroCopy}><Text style={styles.heroTitle}>{meal.title}</Text><Text style={styles.heroCaption}>{meal.caption}</Text></View>
            <View style={styles.counter}><Text style={styles.counterText}>{active + 1} / 3</Text><View style={styles.counterBar}><View style={[styles.counterFill, { width: `${((active + 1) / 3) * 100}%` }]} /></View></View>
          </ImageBackground>
          <View style={styles.socialRail}>
            <Action icon={liked ? "♥" : "♡"} label={t("like")} active={liked} onPress={() => setLiked(!liked)} />
            <Action icon="×" label={t("skip")} onPress={next} />
            <Action icon="↗" label={t("share")} onPress={() => flash("Plan shared with your household")} />
            <Action icon="ⓘ" label={t("details")} onPress={() => router.push({ pathname: "/meal-detail", params: { meal: meal.title } })} />
          </View>
        </View>
        <Pressable style={styles.addButton} onPress={() => flash(t("added"))}><Text style={styles.addButtonText}>＋ {t("addPlan")}</Text></Pressable>

        <View style={styles.sectionHead}><Text style={styles.sectionTitle}>{t("todayPlan")}</Text><Pressable onPress={() => router.push("/weekly-plan")}><Text style={styles.viewAll}>{t("viewAll")}  ›</Text></Pressable></View>
        <View style={styles.summaryRow}>{meals.map((item, index) => <Pressable key={item.key} style={[styles.summaryCard, active === index && styles.summaryActive]} onPress={() => setActive(index)}><Image source={HERO} style={styles.summaryImage} /><Text style={styles.summarySlot}>{t(item.key)}</Text><Text style={styles.summaryTime}>{item.time}</Text></Pressable>)}</View>
      </ScrollView>
      <Toast visible={!!toast} text={toast} />
    </View>
  );
}

function Action({ icon, label, onPress, active }: { icon: string; label: string; onPress: () => void; active?: boolean }) {
  return <View style={styles.actionWrap}><Pressable onPress={onPress} style={[styles.action, active && styles.actionActive]}><Text style={[styles.actionIcon, active && { color: palette.red }]}>{icon}</Text></Pressable><Text style={styles.actionLabel}>{label}</Text></View>;
}

/** Compatibility surface for API-backed recommendation tests and progressive rollout. */
export function SlotSection({ slot, weekday, slotDate, classCode, initiallyLocked, refreshNonce }: { slot: SlotName; weekday: string; slotDate?: string; classCode?: string; initiallyLocked: boolean; refreshNonce: number }) {
  const [locked, setLocked] = useState(initiallyLocked);
  const [why, setWhy] = useState(false);
  const [sent, setSent] = useState<FeedbackEventType | null>(null);
  const query = useQuery({ queryKey: ["daily-plan", slotDate ?? weekday, classCode, refreshNonce], queryFn: () => classCode ? fetchClassDishes(slot, classCode, weekday, 8) : fetchSlotOptions(slot, { weekday, count: 8 }) });
  const lock = useMutation({ mutationFn: (value: boolean) => setPlanSlotLock(weekday, slot, value, slotDate), onSuccess: (_v, value) => setLocked(value) });
  const feedback = useMutation({ mutationFn: (event: FeedbackEventType) => postFeedback({ request_id: query.data?.request_id ?? "", event_type: event, dish_name: query.data?.options?.[0]?.name ?? "" }), onSuccess: (_v, event) => setSent(event) });
  const dish = query.data?.options?.[0] as PlanDish | undefined;
  return <View style={styles.legacy}><View style={styles.sectionHead}><Text style={styles.sectionTitle}>{slot}</Text><Pressable disabled={lock.isPending} onPress={() => lock.mutate(!locked)}><Text>{locked ? "Locked" : "Lock this meal"}</Text></Pressable></View>{dish ? <><Text style={styles.legacyDish}>{dish.name}</Text><Pressable onPress={() => setWhy(!why)}><Text style={styles.viewAll}>{why ? "Hide why" : "Why this?"}</Text></Pressable>{why ? <View><Text>Match score {dish.score.toFixed(2)}</Text>{(dish.explanation?.top_contributors ?? []).map((x) => <Text key={x.module}>{x.module.replace(/^m_/, "").replaceAll("_", " ")}: {x.weighted >= 0 ? "+" : ""}{x.weighted.toFixed(2)}</Text>)}</View> : null}<Pressable onPress={() => feedback.mutate("like")}><Text>{sent === "like" ? "Liked" : "Like"}</Text></Pressable></> : null}</View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.bg }, page: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 112 }, brandRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }, brand: { fontFamily: "Fraunces_600SemiBold", fontSize: 30, color: "#EC315A" }, brandMark: { fontSize: 17 }, tagline: { fontSize: 11, lineHeight: 15, color: palette.ink, marginTop: 3 }, topIcon: { width: 42, height: 42, borderRadius: 21, backgroundColor: "white", borderWidth: 1, borderColor: palette.line, alignItems: "center", justifyContent: "center" }, dot: { position: "absolute", right: 7, top: 6, width: 7, height: 7, borderRadius: 4, backgroundColor: palette.red }, greeting: { fontFamily: "Mukta_600SemiBold", fontSize: 22, color: palette.ink }, question: { color: palette.muted, fontSize: 15, marginTop: -2 }, insight: { flexDirection: "row", gap: 8, backgroundColor: palette.purpleSoft, borderRadius: 12, padding: 11, marginTop: 13, marginBottom: 16 }, insightIcon: { color: palette.purple }, insightText: { color: "#603190", flex: 1, fontSize: 12 }, heroCard: { height: 370, marginRight: 34, borderRadius: 21, backgroundColor: "white", shadowColor: "#3D2C1F", shadowOpacity: .18, shadowRadius: 18, shadowOffset: { width: 0, height: 8 }, elevation: 6 }, hero: { flex: 1 }, heroImage: { borderRadius: 21 }, heroShade: { ...StyleSheet.absoluteFillObject, borderRadius: 21, backgroundColor: "rgba(26,17,14,.33)" }, mealBadge: { position: "absolute", top: 18, left: 16, backgroundColor: palette.amber, borderRadius: 6, paddingHorizontal: 9, paddingVertical: 5 }, mealBadgeText: { color: "white", fontSize: 11, fontWeight: "700" }, heroCopy: { position: "absolute", left: 18, right: 18, top: 80 }, heroTitle: { color: "white", fontSize: 24, lineHeight: 27, fontWeight: "800", width: "72%" }, heroCaption: { color: "white", fontSize: 13, lineHeight: 18, marginTop: 12, width: "65%" }, counter: { position: "absolute", left: 18, bottom: 18 }, counterText: { color: "white", fontWeight: "700" }, counterBar: { width: 64, height: 4, backgroundColor: "#FFFFFF66", borderRadius: 3, marginTop: 8 }, counterFill: { height: 4, borderRadius: 3, backgroundColor: "#B66DF3" }, socialRail: { position: "absolute", right: -40, top: 35, gap: 14 }, actionWrap: { alignItems: "center" }, action: { width: 47, height: 47, borderRadius: 15, backgroundColor: "white", borderWidth: 1, borderColor: palette.line, alignItems: "center", justifyContent: "center", shadowColor: "#000", shadowOpacity: .08, shadowRadius: 8, elevation: 3 }, actionActive: { backgroundColor: "#FFF3F5", borderColor: "#F2B8C2" }, actionIcon: { fontSize: 24 }, actionLabel: { fontSize: 9, backgroundColor: "white", paddingHorizontal: 5, color: palette.muted, marginTop: -3 }, addButton: { alignSelf: "flex-start", marginTop: 14, marginLeft: 2, borderRadius: 18, paddingHorizontal: 14, paddingVertical: 8, backgroundColor: palette.purpleSoft }, addButtonText: { color: palette.purple, fontWeight: "700", fontSize: 12 }, sectionHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 22, marginBottom: 11 }, sectionTitle: { fontWeight: "800", color: palette.ink, fontSize: 16, textTransform: "capitalize" }, viewAll: { color: palette.purple, fontWeight: "600", fontSize: 13 }, summaryRow: { flexDirection: "row", gap: 9 }, summaryCard: { flex: 1, alignItems: "center", padding: 9, borderRadius: 13, backgroundColor: "white", borderWidth: 1, borderColor: palette.line }, summaryActive: { borderColor: palette.purple }, summaryImage: { width: 45, height: 45, borderRadius: 23 }, summarySlot: { fontSize: 11, fontWeight: "700", marginTop: 7, textAlign: "center" }, summaryTime: { fontSize: 10, color: palette.muted, marginTop: 4 }, legacy: { margin: 20, padding: 16, backgroundColor: "white", gap: 8 }, legacyDish: { fontSize: 16, fontWeight: "700" },
});

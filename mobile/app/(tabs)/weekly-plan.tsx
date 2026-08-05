import { useState } from "react";
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { useI18n, type MessageKey } from "@/i18n";
import { FButton, Segmented, Toast, palette } from "@/ui/foofoo";

const FOOD = require("../../assets/images/poha-idli-fruit.png");
const classes: { key: MessageKey; intent: MessageKey; options: string[] }[] = [
  { key: "breakfast", intent: "lightStart", options: ["Poha, Idli & Fruit Bowl", "Upma, Dhokla & Fruit", "Besan Chilla & Fruits", "Oats Upma & Banana"] },
  { key: "lunch", intent: "balanced", options: ["Dal, Rice, Sabzi & Salad", "Rajma Rice & Cabbage", "Chole, Rice & Kachumber", "Moong Dal Khichdi & Curd"] },
  { key: "snacks", intent: "refreshing", options: ["Sprouts Chaat", "Roasted Makhana", "Fruit Chaat", "Buttermilk & Nuts"] },
  { key: "dinner", intent: "satisfying", options: ["Veg Khichdi & Kadhi", "Moong Dal Cheela", "Vegetable Soup & Toast", "Phulka, Sabzi & Curd"] },
];

export default function WeeklyPlan() {
  const { t } = useI18n();
  const [period, setPeriod] = useState(t("weekdays"));
  const [day, setDay] = useState(1);
  const [selected, setSelected] = useState([0, 0, 0, 0]);
  const [locked, setLocked] = useState([true, true, false, false]);
  const [toast, setToast] = useState("");
  const days = period === t("weekdays") ? ["Mon\n13", "Tue\n14", "Wed\n15", "Thu\n16", "Fri\n17"] : ["Sat\n18", "Sun\n19"];
  const flash = (x: string) => { setToast(x); setTimeout(() => setToast(""), 1800); };
  return <View style={s.screen} testID="weekly-plan-screen"><ScrollView contentContainerStyle={s.page} showsVerticalScrollIndicator={false}>
    <View style={s.header}><Pressable onPress={() => router.back()}><Text style={s.back}>‹</Text></Pressable><Text style={s.title}>{t("weeklyTitle")}</Text><Pressable onPress={() => flash("Only unlocked meals were refreshed")}><Text style={s.refresh}>↻</Text></Pressable></View>
    <Segmented options={[t("weekdays"), t("weekend")]} value={period} onChange={(v) => { setPeriod(v); setDay(0); }} />
    <View style={s.range}><Text style={s.rangeText}>{period === t("weekdays") ? "13 – 17 May 2024" : "18 – 19 May 2024"}</Text></View>
    <View style={s.days}>{days.map((x, i) => <Pressable key={x} style={[s.day, day === i && s.dayActive]} onPress={() => setDay(i)}><Text style={[s.dayText, day === i && s.dayTextActive]}>{x}</Text></Pressable>)}</View>
    <View style={s.legend}><Text style={s.legendText}>{t("mealClasses")}</Text><Text style={s.selected}>● {t("selected")}</Text></View>
    {classes.map((group, groupIndex) => <View style={s.group} key={group.key}><View style={s.groupHead}><View><Text style={s.groupTitle}>{t(group.key)}</Text><Text style={s.intent}>{t(group.intent)}</Text></View><Pressable onPress={() => setLocked((old) => old.map((v, i) => i === groupIndex ? !v : v))}><Text style={[s.lock, locked[groupIndex] && s.locked]}>{locked[groupIndex] ? "▣" : "▢"}</Text></Pressable></View>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.options}>{group.options.map((name, i) => <Pressable testID={`weekly-plan-${groupIndex}-${i}`} key={name} style={[s.option, selected[groupIndex] === i && s.optionActive]} onPress={() => setSelected((old) => old.map((v, k) => k === groupIndex ? i : v))} onLongPress={() => router.push({ pathname: "/meal-detail", params: { meal: name } })}><View><Image source={FOOD} style={s.food} /><View style={[s.number, selected[groupIndex] === i && s.numberActive]}><Text style={s.numberText}>{i + 1}</Text></View>{selected[groupIndex] === i ? <View style={s.check}><Text style={s.checkText}>✓</Text></View> : null}</View><Text numberOfLines={2} style={s.optionName}>{name}</Text></Pressable>)}</ScrollView>
    </View>)}
    <FButton label={t("copyPlan")} onPress={() => flash("Tuesday’s plan copied successfully")} />
  </ScrollView><Toast visible={!!toast} text={toast} /></View>;
}

const s = StyleSheet.create({ screen: { flex: 1, backgroundColor: palette.bg }, page: { padding: 18, paddingBottom: 110 }, header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 15 }, back: { fontSize: 34, color: palette.ink }, title: { fontSize: 18, fontWeight: "800", color: palette.ink }, refresh: { fontSize: 22 }, range: { alignItems: "center", paddingVertical: 16 }, rangeText: { fontWeight: "700", color: palette.ink }, days: { flexDirection: "row", justifyContent: "space-between", marginBottom: 16 }, day: { minWidth: 47, paddingVertical: 9, borderRadius: 10, alignItems: "center" }, dayActive: { backgroundColor: palette.purple }, dayText: { textAlign: "center", fontSize: 12, lineHeight: 18, color: palette.ink }, dayTextActive: { color: "white", fontWeight: "700" }, legend: { flexDirection: "row", justifyContent: "space-between", paddingBottom: 8, borderBottomWidth: 1, borderBottomColor: palette.line }, legendText: { fontSize: 11, color: palette.muted, fontWeight: "700" }, selected: { fontSize: 11, color: palette.green }, group: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: palette.line }, groupHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 9 }, groupTitle: { fontSize: 15, fontWeight: "800", color: palette.ink }, intent: { fontSize: 11, color: palette.muted, marginTop: 2 }, lock: { color: palette.muted, fontSize: 20 }, locked: { color: palette.green }, options: { gap: 9, paddingRight: 8 }, option: { width: 98, padding: 5, borderRadius: 12, borderWidth: 1, borderColor: "transparent", backgroundColor: palette.beige }, optionActive: { borderColor: palette.green, backgroundColor: "#F7FFF9" }, food: { width: 86, height: 59, borderRadius: 9 }, number: { position: "absolute", left: 3, top: 3, width: 18, height: 18, borderRadius: 9, alignItems: "center", justifyContent: "center", backgroundColor: "#2B2926" }, numberActive: { backgroundColor: palette.green }, numberText: { color: "white", fontSize: 10, fontWeight: "800" }, check: { position: "absolute", right: 3, top: 3, width: 18, height: 18, borderRadius: 9, backgroundColor: palette.green, alignItems: "center", justifyContent: "center" }, checkText: { color: "white", fontSize: 11 }, optionName: { textAlign: "center", fontSize: 9, lineHeight: 12, color: palette.ink, marginTop: 5 }, });

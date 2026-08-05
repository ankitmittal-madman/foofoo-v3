import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

export type Locale = "en" | "hi";

const messages = {
  en: {
    greeting: "Namaste, Anita 👋", question: "What shall we plan for today?", insight: "Your family prefers lighter dinners on weekdays",
    todayPlan: "Today’s Plan", viewAll: "View all", breakfast: "Breakfast", lunch: "Lunch", snacks: "Evening Snacks", dinner: "Dinner",
    home: "Home", weekly: "Weekly Plan", pantry: "Pantry", chat: "Chat", profile: "Profile", weekdays: "Weekdays", weekend: "Weekend",
    weeklyTitle: "Weekly Meal Plan", mealClasses: "MEAL CLASSES", selected: "Selected", copyPlan: "Copy Tuesday Plan", regenerated: "Fresh unlocked ideas are ready",
    lightStart: "Energising start to your day", balanced: "Balanced & wholesome", refreshing: "Light & refreshing", satisfying: "Light & satisfying",
    like: "Like", skip: "Skip", details: "Details", share: "Share", addPlan: "Add to plan", added: "Added to plan ✓",
    pantryTitle: "My Pantry", grocery: "Grocery List", addItem: "+ Add item", shareList: "Share List", searchPantry: "Search in pantry",
    all: "All", grains: "Grains", pulses: "Pulses", spices: "Spices", others: "Others", low: "Low", ok: "OK",
    aiTitle: "AI Meal Assistant", aiHello: "What can I make for dinner with less oil?", aiReply: "Based on your pantry, these light options will work beautifully.",
    typeMessage: "Type a message…", profileTitle: "Profile", household: "Household Members", foodPrefs: "Food Preferences", allergies: "Allergies & Restrictions",
    reminders: "Meal Reminders", settings: "Settings", help: "Help & Support", language: "Language", logout: "Log Out", chooseLanguage: "Choose your preferred language",
    english: "English", hindi: "हिंदी", continue: "Continue", languageHint: "You can change this later in app settings.", mealDetail: "Meal Class Detail",
    about: "About", nutrition: "Nutrition", ingredients: "Ingredients", steps: "Steps", whyGreat: "Why it’s great?", selectThis: "Select this", cookingMode: "Start cooking",
    mins: "20 mins", easy: "Easy", calories: "~350 kcal", premium: "FooFoo Plus", notifications: "Notifications",
  },
  hi: {
    greeting: "नमस्ते, अनीता 👋", question: "आज खाने में क्या बनाएं?", insight: "आपके परिवार को सप्ताह के दिनों में हल्का डिनर पसंद है",
    todayPlan: "आज का प्लान", viewAll: "सभी देखें", breakfast: "नाश्ता", lunch: "दोपहर", snacks: "शाम का नाश्ता", dinner: "रात का खाना",
    home: "होम", weekly: "साप्ताहिक प्लान", pantry: "पैंट्री", chat: "चैट", profile: "प्रोफ़ाइल", weekdays: "कार्यदिवस", weekend: "वीकेंड",
    weeklyTitle: "साप्ताहिक भोजन प्लान", mealClasses: "भोजन श्रेणियाँ", selected: "चुना गया", copyPlan: "मंगलवार का प्लान कॉपी करें", regenerated: "नए सुझाव तैयार हैं",
    lightStart: "दिन की ऊर्जावान शुरुआत", balanced: "संतुलित और पौष्टिक", refreshing: "हल्का और ताज़गीभरा", satisfying: "हल्का और संतोषजनक",
    like: "पसंद", skip: "आज नहीं", details: "जानकारी", share: "शेयर", addPlan: "प्लान में जोड़ें", added: "प्लान में जुड़ गया ✓",
    pantryTitle: "मेरी पैंट्री", grocery: "किराना सूची", addItem: "+ सामान जोड़ें", shareList: "सूची शेयर करें", searchPantry: "पैंट्री में खोजें",
    all: "सभी", grains: "अनाज", pulses: "दालें", spices: "मसाले", others: "अन्य", low: "कम", ok: "ठीक",
    aiTitle: "AI भोजन सहायक", aiHello: "कम तेल में डिनर के लिए क्या बनाऊँ?", aiReply: "आपकी पैंट्री के अनुसार ये हल्के विकल्प बढ़िया रहेंगे।",
    typeMessage: "संदेश लिखें…", profileTitle: "प्रोफ़ाइल", household: "परिवार के सदस्य", foodPrefs: "खाने की पसंद", allergies: "एलर्जी और प्रतिबंध",
    reminders: "भोजन रिमाइंडर", settings: "सेटिंग्स", help: "सहायता", language: "भाषा", logout: "लॉग आउट", chooseLanguage: "अपनी पसंदीदा भाषा चुनें",
    english: "English", hindi: "हिंदी", continue: "आगे बढ़ें", languageHint: "इसे बाद में ऐप सेटिंग्स में बदल सकते हैं।", mealDetail: "भोजन श्रेणी विवरण",
    about: "जानकारी", nutrition: "पोषण", ingredients: "सामग्री", steps: "विधि", whyGreat: "यह अच्छा क्यों है?", selectThis: "इसे चुनें", cookingMode: "पकाना शुरू करें",
    mins: "20 मिनट", easy: "आसान", calories: "~350 कैलोरी", premium: "FooFoo Plus", notifications: "सूचनाएँ",
  },
} as const;

export type MessageKey = keyof typeof messages.en;
type Value = { locale: Locale; setLocale: (locale: Locale) => void; t: (key: MessageKey) => string };
const Context = createContext<Value>({ locale: "en", setLocale: () => {}, t: (key) => messages.en[key] });

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");
  useEffect(() => { AsyncStorage.getItem("foofoo-locale").then((v) => { if (v === "en" || v === "hi") setLocaleState(v); }); }, []);
  const setLocale = (next: Locale) => { setLocaleState(next); AsyncStorage.setItem("foofoo-locale", next).catch(() => {}); };
  const value = useMemo(() => ({ locale, setLocale, t: (key: MessageKey) => messages[locale][key] }), [locale]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export const useI18n = () => useContext(Context);

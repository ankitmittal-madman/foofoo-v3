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
    brandTagline: "AI meal decisions for your household", householdContext: "Sharma household · 4 members · Pune", refresh: "Refresh", strongFit: "Strong fit", safeStart: "Safe starting point",
    showAlternatives: "Show 3 alternatives", hideAlternatives: "Hide alternatives", lock: "Lock", locked: "Locked", makeThis: "Add to plan", notToday: "Not today", save: "Save", saved: "Saved", cookingDetails: "Cooking details",
    tooMuchWork: "Too much work", missingItem: "Missing item", memberObjected: "Family said no", differentMood: "Different mood", tryAgain: "Try again", noSafeMeal: "No safe complete meal is available.", savedMealFallback: "Showing your last saved meal while we reconnect.",
    weeklySubtitle: "Meal classes tuned to your household rhythm", mealsSelected: "meals selected", rankedHousehold: "Ranked for your household", dishes: "dishes", noSafeClass: "No safe class is available for this slot.",
    regenerateUnlocked: "Regenerate unlocked", copyForward: "Copy plan forward", finalizePlan: "Save weekly plan", saving: "Saving…", saveFailed: "Couldn’t save your plan. Please try again.", routine: "Practical · quick · reliable", relaxed: "Relaxed · richer · weekend special",
    expirySoon: "Expires soon", inStock: "In stock", quickAdd: "Quick add item", vegetables: "Vegetables", dairy: "Dairy", grainsPulses: "Grains & Pulses", missing: "Missing", have: "Have", addGrocery: "+ Add grocery item",
    cookingTitle: "Cooking mode", stepLabel: "STEP", startTimer: "Start timer", timerRunning: "Timer running · tap to pause", previous: "Previous", nextStep: "Next step", finish: "Finish", pause: "Pause", toolHint: "Tool", ingredientHint: "Keep ready",
    quickPrompts: "Quick prompts", chatPromptOne: "15-minute dinner", chatPromptTwo: "Use pantry items", chatPromptThree: "Kids will enjoy", highProtein: "High protein", lightTasty: "Light & tasty", lowCalorie: "Low calorie",
    prepCook: "Prep & Cook", difficulty: "Difficulty", mealCalories: "Calories", aiSuggestion: "AI Suggestion", aiSuggestionBody: "Based on your preferences and pantry, this is a strong fit.",
    lightBalancedQuick: "Light · balanced · quick", aboutBody: "A balanced combination of carbohydrates, protein and micronutrients for a steady start.", benefitsOne: "Light on the stomach", benefitsTwo: "Rich in iron and fibre", benefitsThree: "Keeps you full for longer",
    plannerRole: "Planner", cookRole: "Cook", budget: "Weekly budget", cookSpeed: "Cook speed", regionalIdentity: "Regional identity", fast: "Fast", puneMaharashtra: "Pune · Maharashtra", profilePlusBody: "Smarter plans and unlimited swaps",
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
    brandTagline: "आपके परिवार के लिए AI भोजन निर्णय", householdContext: "शर्मा परिवार · 4 सदस्य · पुणे", refresh: "नए सुझाव", strongFit: "बहुत उपयुक्त", safeStart: "सुरक्षित शुरुआत",
    showAlternatives: "3 विकल्प देखें", hideAlternatives: "विकल्प छिपाएँ", lock: "लॉक करें", locked: "लॉक है", makeThis: "प्लान में जोड़ें", notToday: "आज नहीं", save: "सहेजें", saved: "सहेजा गया", cookingDetails: "पकाने की जानकारी",
    tooMuchWork: "बहुत मेहनत", missingItem: "सामान नहीं है", memberObjected: "परिवार को पसंद नहीं", differentMood: "कुछ और खाने का मन", tryAgain: "फिर कोशिश करें", noSafeMeal: "अभी कोई सुरक्षित पूरा भोजन उपलब्ध नहीं है।", savedMealFallback: "कनेक्शन लौटने तक आपका पिछला सहेजा भोजन दिखाया जा रहा है।",
    weeklySubtitle: "आपके परिवार की दिनचर्या के अनुसार भोजन श्रेणियाँ", mealsSelected: "भोजन चुने गए", rankedHousehold: "आपके परिवार के लिए क्रमबद्ध", dishes: "व्यंजन", noSafeClass: "इस समय के लिए सुरक्षित श्रेणी उपलब्ध नहीं है।",
    regenerateUnlocked: "अनलॉक विकल्प दोबारा बनाएँ", copyForward: "प्लान आगे कॉपी करें", finalizePlan: "साप्ताहिक प्लान सहेजें", saving: "सहेज रहे हैं…", saveFailed: "प्लान सहेजा नहीं जा सका। फिर कोशिश करें।", routine: "व्यावहारिक · झटपट · भरोसेमंद", relaxed: "आरामदायक · खास · वीकेंड स्पेशल",
    expirySoon: "जल्द समाप्त", inStock: "स्टॉक में", quickAdd: "जल्दी सामान जोड़ें", vegetables: "सब्ज़ियाँ", dairy: "डेयरी", grainsPulses: "अनाज और दालें", missing: "चाहिए", have: "मौजूद", addGrocery: "+ किराना जोड़ें",
    cookingTitle: "कुकिंग मोड", stepLabel: "चरण", startTimer: "टाइमर शुरू करें", timerRunning: "टाइमर चल रहा है · रोकने के लिए टैप करें", previous: "पिछला", nextStep: "अगला चरण", finish: "पूरा करें", pause: "रोकें", toolHint: "बर्तन", ingredientHint: "तैयार रखें",
    quickPrompts: "जल्दी पूछें", chatPromptOne: "15 मिनट का डिनर", chatPromptTwo: "पैंट्री का सामान", chatPromptThree: "बच्चों को पसंद आए", highProtein: "अधिक प्रोटीन", lightTasty: "हल्का और स्वादिष्ट", lowCalorie: "कम कैलोरी",
    prepCook: "तैयारी और पकाना", difficulty: "कठिनाई", mealCalories: "कैलोरी", aiSuggestion: "AI सुझाव", aiSuggestionBody: "आपकी पसंद और पैंट्री के अनुसार यह एक अच्छा विकल्प है।",
    lightBalancedQuick: "हल्का · संतुलित · झटपट", aboutBody: "दिन की स्थिर शुरुआत के लिए कार्बोहाइड्रेट, प्रोटीन और सूक्ष्म पोषक तत्वों का संतुलन।", benefitsOne: "पेट के लिए हल्का", benefitsTwo: "आयरन और फाइबर से भरपूर", benefitsThree: "देर तक पेट भरा रखता है",
    plannerRole: "प्लानर", cookRole: "रसोइया", budget: "साप्ताहिक बजट", cookSpeed: "पकाने की गति", regionalIdentity: "क्षेत्रीय पहचान", fast: "तेज़", puneMaharashtra: "पुणे · महाराष्ट्र", profilePlusBody: "स्मार्ट प्लान और असीमित बदलाव",
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

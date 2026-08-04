import AsyncStorage from "@react-native-async-storage/async-storage";
import { OneSignal } from "react-native-onesignal";

const CONSENT_KEY = "foofoo.push-notification-consent";
const appId = process.env.EXPO_PUBLIC_ONESIGNAL_APP_ID?.trim();
let initialized = false;
let initialization: Promise<boolean> | null = null;

/**
 * initializeOneSignal — starts the native push SDK behind a consent gate.
 * @returns true when an App ID is configured and the SDK was initialized.
 */
export async function initializeOneSignal(): Promise<boolean> {
  if (!appId) return false;
  if (initialization) return initialization;
  initialization = (async () => {
    OneSignal.setConsentRequired(true);
    OneSignal.initialize(appId);
    initialized = true;
    const storedConsent = await AsyncStorage.getItem(CONSENT_KEY);
    OneSignal.setConsentGiven(storedConsent === "granted");
    return true;
  })();
  return initialization;
}

/**
 * identifyOneSignalUser — attaches the authenticated Supabase user ID as OneSignal External ID.
 * @param userId - Supabase auth user ID, or null after sign-out.
 */
export function identifyOneSignalUser(userId: string | null): void {
  if (!initialized) return;
  if (userId) OneSignal.login(userId);
  else OneSignal.logout();
}

/**
 * configureNotificationConsent — persists the user's push choice and optionally opens the OS prompt.
 * @param granted - whether the user explicitly opted into push notifications.
 */
export async function configureNotificationConsent(granted: boolean): Promise<void> {
  await AsyncStorage.setItem(CONSENT_KEY, granted ? "granted" : "denied");
  if (!initialized) await initializeOneSignal();
  if (!initialized) return;
  OneSignal.setConsentGiven(granted);
  if (granted) await OneSignal.Notifications.requestPermission(false);
}

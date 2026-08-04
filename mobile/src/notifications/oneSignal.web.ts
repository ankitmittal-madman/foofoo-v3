const CONSENT_KEY = "foofoo.push-notification-consent";

/**
 * Push notifications are currently native-only. Keeping a web-specific module prevents Metro
 * from loading react-native-onesignal in browsers, where its native TurboModule is unavailable.
 */
export async function initializeOneSignal(): Promise<boolean> {
  return false;
}

/** Web has no OneSignal native user identity to update. */
export function identifyOneSignalUser(_userId: string | null): void {}

/**
 * Remember the user's choice on web without attempting to open a native permission prompt.
 */
export async function configureNotificationConsent(granted: boolean): Promise<void> {
  try {
    globalThis.localStorage?.setItem(CONSENT_KEY, granted ? "granted" : "denied");
  } catch {
    // Storage can be unavailable in privacy-restricted browser contexts.
  }
}

/**
 * initializeOneSignal — web adapter for the native-only OneSignal integration.
 * @returns false because FooFoo currently registers push subscriptions only on iOS and Android.
 */
export async function initializeOneSignal(): Promise<boolean> {
  return false;
}

/**
 * identifyOneSignalUser — no-op on web because no native push subscription exists to identify.
 * @param _userId - authenticated Supabase user ID, intentionally unused on web.
 */
export function identifyOneSignalUser(_userId: string | null): void {}

/**
 * configureNotificationConsent — no-op on web; the consent record is still written to Supabase.
 * @param _granted - user's recorded push preference, intentionally unused on web.
 */
export async function configureNotificationConsent(_granted: boolean): Promise<void> {}

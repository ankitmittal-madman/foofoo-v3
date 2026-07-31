import { createContext, useContext, useEffect, useState, type PropsWithChildren } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "./supabaseClient";

interface SessionContextValue {
  session: Session | null;
  loading: boolean;
  signUp: (email: string, password: string) => Promise<{ error: string | null }>;
  signIn: (email: string, password: string) => Promise<{ error: string | null }>;
  signOut: () => Promise<void>;
}

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

/**
 * SessionProvider — wraps the whole app (mounted once in app/_layout.tsx) and keeps a single
 * live copy of the user's Supabase auth session, backed by supabase.auth's own AsyncStorage
 * persistence. `loading` is true only until the very first getSession() check resolves — every
 * screen that gates on being signed in (app/index.tsx, the onboarding layout) waits on this
 * flag before deciding whether to redirect. `signUp`/`signIn`/`signOut` are the three auth
 * actions exposed to screens; each returns a plain `{ error }` string (or null) rather than
 * throwing, so callers can show it directly without a try/catch.
 * @param children - the rest of the app tree, rendered once the provider's context is ready.
 */
export function SessionProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data: subscription } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
    });
    return () => subscription.subscription.unsubscribe();
  }, []);

  const value: SessionContextValue = {
    session,
    loading,
    signUp: async (email, password) => {
      const { error } = await supabase.auth.signUp({ email, password });
      return { error: error?.message ?? null };
    },
    signIn: async (email, password) => {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      return { error: error?.message ?? null };
    },
    signOut: async () => {
      await supabase.auth.signOut();
    },
  };

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

/**
 * useSession — reads the current auth session/loading flag and the sign-in/up/out actions from
 * SessionProvider. Throws if called outside the provider (a programming-error guard, not a
 * user-facing state) so a missing provider fails loudly during development rather than silently
 * returning undefined session data.
 * @returns the current session (or null if signed out), the initial-load flag, and the auth actions.
 */
export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within a SessionProvider");
  return ctx;
}

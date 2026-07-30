/**
 * Lightweight client logger (Expo/React Native runtime ONLY — do not import into
 * `supabase/functions/**`; that Deno/edge-function runtime has its own sanctioned sink at
 * `supabase/functions/_shared/logging/logger.ts` and cannot resolve `@react-native-async-storage`).
 *
 * This is the hot-path-friendly option for mobile client code: `debug`/`info` never touch
 * AsyncStorage (console only, dev-visible), so calling them inside render paths or gesture
 * handlers is cheap. `warn`/`error` are rarer and worth keeping around after the app closes, so
 * those two also persist a small ring buffer to AsyncStorage (bounded at MAX_PERSISTED_ENTRIES —
 * unbounded growth on-device is not acceptable for a mobile app).
 *
 * Org coding standard: product code must never call console.* directly — this file (and its
 * edge-function counterpart) is the single sanctioned exception, being the sink itself.
 * NO PII and NO secrets may be logged (DOC-P3-07 §16 / DPDP) — callers pass only non-sensitive
 * context fields; this logger does not attempt to scrub arbitrary objects, so choose what you
 * pass in deliberately.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

export type LogLevel = "debug" | "info" | "warn" | "error";

export interface LogFields {
  [key: string]: unknown;
}

const STORAGE_KEY = "@foofoo/client-log";
const MAX_PERSISTED_ENTRIES = 100;

// Visual marker so client-logger output is distinguishable from any other console output at a
// glance during development (per structured-logger-template.md design requirement).
const MARKER: Record<LogLevel, string> = {
  debug: "🔎",
  info: "ℹ️",
  warn: "⚠️",
  error: "🛑",
};

interface PersistedEntry {
  level: LogLevel;
  ts: string;
  msg: string;
  fields?: LogFields;
}

/** Best-effort append to the on-device ring buffer. Never throws — a logging failure must not
 * crash the app it is trying to help debug. */
async function persist(entry: PersistedEntry): Promise<void> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const existing: PersistedEntry[] = raw ? JSON.parse(raw) : [];
    existing.push(entry);
    const trimmed = existing.slice(-MAX_PERSISTED_ENTRIES);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    // Swallow — logging must never be the thing that breaks the app.
  }
}

function emit(level: LogLevel, msg: string, fields?: LogFields, durationMs?: number): void {
  const ts = new Date().toISOString();
  const line = `${MARKER[level]} [${ts}] ${msg}`;
  const payload = durationMs !== undefined ? { ...fields, duration_ms: durationMs } : fields;

  // deno-lint-ignore no-console -- this file is the sanctioned client-side sink itself.
  const fn = level === "error" ? console.error : level === "warn" ? console.warn : console.log;
  fn(line, payload ?? "");

  // Only warn/error get persisted — debug/info stay console-only to keep the hot path cheap.
  if (level === "warn" || level === "error") {
    void persist({ level, ts, msg, fields: payload });
  }
}

export const logger = {
  debug(msg: string, fields?: LogFields, durationMs?: number): void {
    emit("debug", msg, fields, durationMs);
  },
  info(msg: string, fields?: LogFields, durationMs?: number): void {
    emit("info", msg, fields, durationMs);
  },
  warn(msg: string, fields?: LogFields): void {
    emit("warn", msg, fields);
  },
  error(msg: string, fields?: LogFields): void {
    emit("error", msg, fields);
  },
  /** Read back the persisted warn/error ring buffer (e.g. for an in-app "send diagnostics" flow). */
  async getPersistedLog(): Promise<PersistedEntry[]> {
    try {
      const raw = await AsyncStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  },
  async clearPersistedLog(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEY);
    } catch {
      // Best-effort — nothing further to do if this fails.
    }
  },
};

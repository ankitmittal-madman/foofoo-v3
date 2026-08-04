/** Cached live weather context. Returns null when consent/config/provider availability is absent. */
import { createServiceRoleClient } from "../db/client.ts";
import type { RequestContext } from "../types/context.ts";
import { withTimeout } from "../utils/timeout.ts";

export interface WeatherContext {
  weather_condition: "rain" | "heatwave" | "cold_snap" | null;
  temp_c: number;
  is_raining: boolean;
  condition: string;
  fetched_at: string;
  source: "cache" | "openweathermap";
}

export function classifyWeather(
  condition: string,
  tempC: number,
): WeatherContext["weather_condition"] {
  const value = condition.toLowerCase();
  if (value.includes("rain") || value.includes("drizzle") || value.includes("thunderstorm")) {
    return "rain";
  }
  if (tempC >= 38) return "heatwave";
  if (tempC <= 12) return "cold_snap";
  return null;
}

export async function loadWeatherContext(
  ctx: RequestContext,
  city: string,
): Promise<WeatherContext | null> {
  const key = ctx.config.openWeatherMapApiKey;
  const normalizedCity = city.trim();
  if (!key || !normalizedCity) return null;
  const db = createServiceRoleClient(ctx.config);
  const today = new Date().toISOString().slice(0, 10);
  const now = new Date().toISOString();
  const { data: cached } = await withTimeout(
    db.from("weather_cache").select("temp_c,condition,fetched_at,expires_at")
      .eq("city", normalizedCity).eq("date", today).gt("expires_at", now).maybeSingle(),
    "weather.cache.read",
  );
  if (cached?.temp_c != null && cached.condition) {
    const tempC = Number(cached.temp_c);
    const condition = String(cached.condition);
    const weatherCondition = classifyWeather(condition, tempC);
    return {
      weather_condition: weatherCondition,
      temp_c: tempC,
      is_raining: weatherCondition === "rain",
      condition,
      fetched_at: String(cached.fetched_at),
      source: "cache",
    };
  }

  try {
    const url = new URL("https://api.openweathermap.org/data/2.5/weather");
    url.searchParams.set("q", `${normalizedCity},IN`);
    url.searchParams.set("units", "metric");
    url.searchParams.set("appid", key);
    const response = await withTimeout(fetch(url), "weather.provider", 2500);
    if (!response.ok) throw new Error(`weather provider returned ${response.status}`);
    const payload = await response.json() as {
      main?: { temp?: number; humidity?: number };
      weather?: Array<{ main?: string }>;
    };
    const tempC = Number(payload.main?.temp);
    if (!Number.isFinite(tempC)) throw new Error("weather provider omitted temperature");
    const condition = payload.weather?.[0]?.main ?? "Unknown";
    const fetchedAt = new Date();
    const expiresAt = new Date(fetchedAt.getTime() + 3 * 60 * 60 * 1000);
    await db.from("weather_cache").upsert({
      city: normalizedCity,
      date: today,
      temp_c: tempC,
      humidity_pct: payload.main?.humidity ?? null,
      condition,
      fetched_at: fetchedAt.toISOString(),
      expires_at: expiresAt.toISOString(),
    }, { onConflict: "city,date" });
    const weatherCondition = classifyWeather(condition, tempC);
    return {
      weather_condition: weatherCondition,
      temp_c: tempC,
      is_raining: weatherCondition === "rain",
      condition,
      fetched_at: fetchedAt.toISOString(),
      source: "openweathermap",
    };
  } catch (error) {
    ctx.logger.warn("weather.unavailable", {
      city: normalizedCity,
      detail: error instanceof Error ? error.message : String(error),
    });
    return null;
  }
}

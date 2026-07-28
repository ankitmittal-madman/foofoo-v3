/**
 * Fallback response (Phase C, RE-DOC-10 §11).
 *
 * When the RE is unreachable / times out / returns a bad body, the user must still see familiar
 * food, not an error. This returns a SINGLE hardcoded safe-default plate as a valid 200 response
 * (contract-conformant) with a `warnings` entry.
 *
 * ⚠️ STUB: a real per-zone cached default plate set is future work (RE-DOC-10 §11 "cached-per-zone
 * default"), not this task. This single pan-safe comfort plate (Moong Dal Khichdi — mild, veg,
 * jain-safe, weaning-safe) is a deliberate placeholder, flagged for replacement.
 */
import { API_VERSION } from "./meta.ts";

export function buildFallbackResponse(requestId: string, reason: string): Record<string, unknown> {
  return {
    request_id: requestId,
    api_version: API_VERSION,
    engine_version: "fallback",
    config_version: "fallback",
    plates: [
      {
        plate_id: `fallback:${requestId}`,
        form: "standalone",
        hero_dish_ids: ["fallback:moong_dal_khichdi"],
        hero_dish_names: ["Moong Dal Khichdi"],
        support: null,
        is_standalone: true,
        plate_score: 0,
        base_total: 0,
        gain_multiplier: 1,
        final_score: 0,
        contributions: [],
      },
    ],
    warnings: [
      `RE unavailable (${reason}); served a cached safe-default plate. [STUB: single pan-safe plate; per-zone fallback set is future work]`,
    ],
  };
}

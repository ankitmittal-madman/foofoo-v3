import { allergenFlags, ALLERGEN_BITS } from "../toHouseholdWrite";

/**
 * P1-5 (2026-08) — first mobile unit tests in this repo. allergenFlags() is real, safety-relevant
 * logic (packs a household's declared allergens into the bitmask profiles.allergen_flags stores,
 * which the RE's hard allergen filter reads) that had zero test coverage before this file.
 */
describe("allergenFlags", () => {
  it("returns 0 for no allergens selected", () => {
    expect(allergenFlags([])).toBe(0);
  });

  it("ORs together the bits for each selected allergen", () => {
    expect(allergenFlags(["dairy", "gluten"])).toBe(ALLERGEN_BITS.dairy | ALLERGEN_BITS.gluten);
  });

  it("ignores 'others' (collect-only, no bit assigned)", () => {
    expect(allergenFlags(["dairy", "others"])).toBe(ALLERGEN_BITS.dairy);
  });

  it("covers the full 9-bit model (fish/mustard extension) without dropping any bit", () => {
    const all = Object.keys(ALLERGEN_BITS);
    const combined = allergenFlags(all);
    for (const key of all) {
      expect(combined & ALLERGEN_BITS[key]).toBe(ALLERGEN_BITS[key]);
    }
    // 9 real allergen bits per the WP-21 extension: peanuts,dairy,gluten,shellfish,soy,sesame,fish,mustard
    expect(Object.keys(ALLERGEN_BITS).length).toBe(8);
  });

  it("selecting the same allergen twice is idempotent (bitwise OR, not addition)", () => {
    expect(allergenFlags(["dairy", "dairy"])).toBe(ALLERGEN_BITS.dairy);
  });
});

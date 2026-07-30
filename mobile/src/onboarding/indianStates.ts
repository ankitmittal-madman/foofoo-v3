/**
 * Indian states + Union Territories for the Screen 2 home-state picker.
 *
 * These are UI reference data, not an engine rule. The spellings deliberately
 * match the engine's canonical STATE_ZONE keys in ghar_re/reference.py so the
 * stored home_state resolves to a cuisine zone. States the engine doesn't map
 * (mostly the smaller NE states + some UTs) fall back to "North" engine-side —
 * an accepted v1 approximation, not a bug.
 *
 * One flat alphabetical list (states and UTs together), matching the mockup's
 * single searchable list (mockup 2-a).
 */
export const INDIAN_STATES: string[] = [
  'Andaman & Nicobar Islands',
  'Andhra Pradesh',
  'Arunachal Pradesh',
  'Assam',
  'Bihar',
  'Chandigarh',
  'Chhattisgarh',
  'Dadra & Nagar Haveli and Daman & Diu',
  'Delhi',
  'Goa',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jammu & Kashmir',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Ladakh',
  'Lakshadweep',
  'Madhya Pradesh',
  'Maharashtra',
  'Manipur',
  'Meghalaya',
  'Mizoram',
  'Nagaland',
  'Odisha',
  'Puducherry',
  'Punjab',
  'Rajasthan',
  'Sikkim',
  'Tamil Nadu',
  'Telangana',
  'Tripura',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal',
];

process.env.EXPO_PUBLIC_SUPABASE_URL ??= "https://test-project.supabase.co";
process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ??= "test-anon-key";

const preset = require("jest-expo/jest-preset");

module.exports = {
  ...preset,
  setupFiles: [...(preset.setupFiles || []), "<rootDir>/jest.setup.js"],
  testPathIgnorePatterns: ["/node_modules/", "/.expo/"],
};

import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";
import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    // Playwright specs live in `e2e/`; keep them out of Vitest.
    exclude: [...configDefaults.exclude, "e2e/**"],
    // Minimal values so `lib/env.js` validation passes under test.
    env: {
      BACKEND_URL: "http://backend.test",
      SUPABASE_SECRET_KEY: "test-secret-key",
      NEXT_PUBLIC_SUPABASE_URL: "https://test.supabase.co",
      NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "test-publishable-key",
    },
    // Restore `vi.stubEnv` values after each test.
    unstubEnvs: true,
  },
});

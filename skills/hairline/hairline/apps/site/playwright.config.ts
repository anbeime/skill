import { defineConfig } from "@playwright/test";

/** The built site, served by `next start`. Run `pnpm build` first; turbo does. */
export default defineConfig({
  testDir: "test",
  testMatch: "*.spec.ts",
  fullyParallel: true,
  reporter: "list",
  use: { channel: "chrome", baseURL: "http://localhost:4320", viewport: { width: 1200, height: 900 } },
  webServer: { command: "pnpm exec next start -p 4320", url: "http://localhost:4320", reuseExistingServer: !process.env.CI },
});

import { defineConfig } from "@playwright/test";

/** Browser tests run in the installed Chrome, against the harness page (test/browser/serve.mjs). */
export default defineConfig({
  testDir: "test/browser",
  testMatch: "*.spec.ts",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:4310",
    channel: "chrome",
    viewport: { width: 1200, height: 900 },
    deviceScaleFactor: 1,
    colorScheme: "light",
  },
  webServer: { command: "node test/browser/serve.mjs", url: "http://localhost:4310", reuseExistingServer: !process.env.CI },
});

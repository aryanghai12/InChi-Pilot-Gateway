import { defineConfig, devices } from "@playwright/test";
import { validateEnvironment } from "./support/environment.mjs";

// E2E_BASE_URL points at an already running stack (e.g. `docker compose up`).
// Without it, Playwright builds and starts the Next.js frontend on its own.
const baseURL = process.env.E2E_BASE_URL || "http://localhost:3000";
validateEnvironment(process.env);
const apiOnly = process.env.E2E_API_ONLY === "1";

export default defineConfig({
  testDir: "./tests",
  testMatch: apiOnly ? /(?:api-contract|session-api|registry-api)\.spec\.ts/ : /.*\.spec\.ts/,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }], ["json", { outputFile: "test-results/results.json" }], ["junit", { outputFile: "test-results/junit.xml" }]],
  use: {
    baseURL,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: process.env.E2E_BASE_URL || apiOnly
    ? undefined
    : {
        command: "npm run build && npm run start",
        cwd: "../frontend",
        url: baseURL,
        timeout: 180_000,
        reuseExistingServer: !process.env.CI,
      },
});

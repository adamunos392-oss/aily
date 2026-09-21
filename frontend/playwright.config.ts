import { defineConfig, devices } from "@playwright/test";

const backendCwd = new URL("../backend", import.meta.url).pathname;
const venvPython = new URL("../backend/.venv/bin/python", import.meta.url).pathname;

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:5199",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    locale: "zh-CN",
  },
  webServer: [
    {
      command: `PYTHONPATH=..:. ${venvPython} -m uvicorn src.main:app --host 127.0.0.1 --port 8099`,
      cwd: backendCwd,
      url: "http://127.0.0.1:8099/health",
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5199 --strictPort",
      url: "http://127.0.0.1:5199",
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});

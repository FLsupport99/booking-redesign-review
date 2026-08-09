import { defineConfig, devices } from "@playwright/test";

/* 第 3 關：行為與破圖。斷言只碰 DOM，不碰實作技術——
   同一套 spec 對 HTML 版與（將來）任何轉換後的版本都能跑。 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  reporter: [["list"]],
  timeout: 30_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: "http://127.0.0.1:4173",
    viewport: { width: 1024, height: 900 },
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "python3 -m http.server 4173 --bind 127.0.0.1",
    url: "http://127.0.0.1:4173/index.html",
    reuseExistingServer: true,
    timeout: 30_000,
  },
});

import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'attendance-real.spec.ts', workers: 1, reporter: 'list', timeout: 120000, expect: { timeout: 20000 },
  outputDir: 'test-results-attendance-real',
  use: { baseURL: 'http://127.0.0.1:5181', viewport: { width: 1440, height: 1000 }, actionTimeout: 15000, headless: true, trace: 'off', video: 'off', screenshot: 'off' },
  webServer: { command: `"${process.execPath}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5181 --strictPort`, url: 'http://127.0.0.1:5181', env: { FACEGATE_HUB_URL: 'http://127.0.0.1:8010' }, reuseExistingServer: false },
});

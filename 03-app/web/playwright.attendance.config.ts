import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'attendance.spec.ts', workers: 1, reporter: 'list', timeout: 60000, expect: { timeout: 12000 },
  outputDir: 'test-results-attendance',
  use: { baseURL: 'http://127.0.0.1:5180', viewport: { width: 1440, height: 1000 }, headless: true, trace: 'off', video: 'off', screenshot: 'off' },
  webServer: { command: `"${process.execPath}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5180 --strictPort`, url: 'http://127.0.0.1:5180', reuseExistingServer: false },
});

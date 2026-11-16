import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'liveness.spec.ts', workers: 1, reporter: 'list', timeout: 45000, expect: { timeout: 10000 }, outputDir: 'test-results-liveness',
  use: { baseURL: 'http://127.0.0.1:5186', viewport: { width: 1440, height: 1000 }, actionTimeout: 15000, headless: true, trace: 'off', video: 'off' },
  webServer: { command: `"${process.execPath}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5186 --strictPort`, url: 'http://127.0.0.1:5186', reuseExistingServer: false },
});

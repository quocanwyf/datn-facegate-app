import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'monitor.spec.ts', workers: 1, reporter: 'list', timeout: 60000, expect: { timeout: 15000 }, outputDir: 'test-results-monitor',
  use: { baseURL: 'http://127.0.0.1:5183', viewport: { width: 1440, height: 1000 }, actionTimeout: 15000, headless: true, trace: 'off', video: 'off', screenshot: 'off' },
  webServer: { command: `"${process.execPath}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5183 --strictPort`, url: 'http://127.0.0.1:5183', reuseExistingServer: false },
});

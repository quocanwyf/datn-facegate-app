import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'me.spec.ts', workers: 1, reporter: 'list', timeout: 60000, expect: { timeout: 10000 }, outputDir: 'test-results-me',
  use: { baseURL: 'http://127.0.0.1:5184', viewport: { width: 390, height: 844 }, headless: true, trace: 'off', video: 'off', screenshot: 'off' },
  webServer: { command: `"${process.execPath}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5184 --strictPort`, url: 'http://127.0.0.1:5184', reuseExistingServer: false },
});

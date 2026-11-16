import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'me-real.spec.ts', workers: 1, reporter: 'list', timeout: 90000, expect: { timeout: 20000 }, outputDir: 'test-results-me-real',
  use: { baseURL: 'http://127.0.0.1:5185', viewport: { width: 390, height: 844 }, headless: true, trace: 'off', video: 'off', screenshot: 'off' },
  webServer: { command: `"${process.execPath}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5185 --strictPort`, url: 'http://127.0.0.1:5185', env: { FACEGATE_HUB_URL: 'http://127.0.0.1:8012' }, reuseExistingServer: false },
});

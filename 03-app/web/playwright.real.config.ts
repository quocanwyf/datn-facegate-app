import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'admin-real.spec.ts', outputDir: 'test-results-real', workers: 1, reporter: 'list', timeout: 90000, expect: { timeout: 15000 },
  use: { baseURL: 'http://127.0.0.1:5177', viewport: { width: 1440, height: 1000 }, headless: true, screenshot: 'off', trace: 'off', video: 'off' },
  webServer: { command: `"${process.execPath}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5177 --strictPort`, url: 'http://127.0.0.1:5177', env: { FACEGATE_HUB_URL: 'http://127.0.0.1:8007' }, reuseExistingServer: false },
});

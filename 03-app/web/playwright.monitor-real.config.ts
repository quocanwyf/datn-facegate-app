import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'monitor-real.spec.ts', workers: 1, reporter: 'list', timeout: 180000, expect: { timeout: 25000 }, outputDir: 'test-results-monitor-real',
  use: { baseURL: 'http://127.0.0.1:5182', viewport: { width: 1440, height: 1000 }, headless: true, actionTimeout: 20000, trace: 'off', video: 'off', screenshot: 'off' },
  webServer: { command: `"${process.execPath}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5182 --strictPort`, url: 'http://127.0.0.1:5182', env: { FACEGATE_HUB_URL: 'http://127.0.0.1:8000' }, reuseExistingServer: false },
});

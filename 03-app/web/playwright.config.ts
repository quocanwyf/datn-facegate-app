import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: ['auth.spec.ts', 'employees.spec.ts', 'session.spec.ts'], fullyParallel: false, workers: 1, reporter: 'list', timeout: 90000, expect: { timeout: 15000 },
  use: { baseURL: 'http://127.0.0.1:5173', channel: 'chromium', viewport: { width: 1440, height: 900 }, headless: true },
  webServer: { command: `"${process.execPath}" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort`, url: 'http://127.0.0.1:5173', reuseExistingServer: !process.env.CI },
});

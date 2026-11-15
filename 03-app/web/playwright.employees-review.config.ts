import { defineConfig } from '@playwright/test';
import config from './playwright.config';
export default defineConfig({ ...config, testMatch: 'employees-review.spec.ts', timeout: 0, workers: 1, use: { ...config.use, headless: false } });

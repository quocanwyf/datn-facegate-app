import { test } from '@playwright/test';
import { employeeApi } from './employee-fixtures';
test('Review W-03 — danh sách nhân viên từ seed.sql, API mô phỏng', async ({ page }) => {
  await employeeApi(page);
  await page.goto('/login');
  await page.evaluate(() => { document.title = 'REVIEW W-03 · API mô phỏng'; });
  await page.pause();
});

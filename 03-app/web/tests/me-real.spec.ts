// Hub/DB clone T08 thật; revoke chỉ chạy trên bản sao, kiểm DB bằng helper riêng.
import { test, expect } from '@playwright/test';
import { promisify } from 'node:util';
import { execFile } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const exec = promisify(execFile);
const root = fileURLToPath(new URL('../../../', import.meta.url));
const screens = '../ket-qua-kiem-thu/2026-11-16_T12/screens';
test('Gửi và hủy giải trình qua Hub thật trên clone T12', async ({ page }) => {
  await page.goto('/login'); await page.getByLabel('Email', { exact: true }).fill('nv006@demo.local'); await page.getByLabel('Mật khẩu', { exact: true }).fill('Demo@123'); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await page.getByRole('link', { name: 'Giải trình', exact: true }).click(); await page.getByRole('link', { name: 'Gửi mới', exact: true }).click();
  await page.getByRole('combobox', { name: 'Loại giải trình', exact: true }).press('ArrowDown'); await page.locator('.ant-select-dropdown:visible').getByText('Lý do khác', { exact: true }).click();
  const reason = `Review T12 gửi/hủy ${Date.now()}`; await page.getByLabel('Lý do', { exact: true }).fill(reason); await page.getByRole('button', { name: 'Gửi giải trình', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Giải trình của tôi' })).toBeVisible(); const card = page.locator('.me-card').filter({ has: page.getByText(reason, { exact: true }) }); await expect(card).toBeVisible(); await page.screenshot({ path: `${screens}/E06-real-pending.png`, fullPage: true });
  await card.getByRole('button', { name: 'Hủy giải trình', exact: true }).click(); await page.getByRole('button', { name: 'Xác nhận hủy', exact: true }).click(); await expect(page.getByText(reason, { exact: true })).toHaveCount(0);
  await page.getByText('Đã xử lý', { exact: true }).click(); await expect(page.getByText(reason, { exact: true })).toBeVisible(); await page.screenshot({ path: `${screens}/E06-real-cancelled.png`, fullPage: true });
});
test('E02/E03/E06/E08 với Hub thật; revoke mẫu T08 trên clone và kiểm DB/file', async ({ page }) => {
  await page.goto('/login'); await page.getByLabel('Email', { exact: true }).fill('nv006@demo.local'); await page.getByLabel('Mật khẩu', { exact: true }).fill('Demo@123'); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByText('Chào Võ Thanh Tùng', { exact: true })).toBeVisible(); await page.screenshot({ path: `${screens}/E02-real-Hub.png`, fullPage: true });
  await page.getByRole('link', { name: 'Bảng công', exact: true }).click(); await expect(page.getByText('Ngày công', { exact: true })).toBeVisible(); await page.screenshot({ path: `${screens}/E03-real-Hub.png`, fullPage: true });
  await page.getByRole('link', { name: 'Giải trình', exact: true }).click(); await expect(page.getByRole('heading', { name: 'Giải trình của tôi' })).toBeVisible();
  await page.getByRole('link', { name: 'Khuôn mặt', exact: true }).click(); await expect(page.getByText('Phương thức: Khuôn mặt', { exact: true })).toBeVisible(); await page.screenshot({ path: `${screens}/E08-real-before.png`, fullPage: true });
  await page.getByRole('button', { name: 'Rút đồng ý và xoá dữ liệu khuôn mặt', exact: true }).click(); await page.getByRole('button', { name: 'Rút đồng ý và xóa', exact: true }).click(); await expect(page.getByRole('status')).toContainText('Đã rút đồng ý và xóa dữ liệu khuôn mặt'); await expect(page.getByText('Phương thức: Chấm công hộ', { exact: true })).toBeVisible(); await page.screenshot({ path: `${screens}/E08-real-after.png`, fullPage: true });
  const checked = await exec(`${root}/03-app/hub/.venv/Scripts/python.exe`, [`${root}/03-app/web/tests/check_t12_revoke.py`, 'after'], { cwd: root, env: { ...process.env, PYTHONUTF8: '1' }, timeout: 30000 }); expect(checked.stdout).toContain('PASS after');
});

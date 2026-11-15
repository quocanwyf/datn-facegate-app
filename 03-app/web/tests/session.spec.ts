import { test, expect } from '@playwright/test';
import { token, fillLogin } from './fixtures';
test('401 đồng thời chỉ xoay refresh một lần, retry với access mới', async ({ page }) => {
  let refreshes = 0; const first = token('OWNER', false); const next = { ...first, access_token: 'renewed-access', refresh_token: 'renewed-refresh' };
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/auth/login')) return route.fulfill({ json: first });
    if (path.endsWith('/auth/refresh')) { refreshes++; expect(route.request().postDataJSON()).toEqual({ refresh_token: first.refresh_token }); await new Promise(resolve => setTimeout(resolve, 200)); return route.fulfill({ json: next }); }
    if (path.endsWith('/health')) return route.fulfill({ json: { status: 'ok', db: true, gpu: false, model_verified: true, gallery_size: 0, version: 'test' } });
    if (path.endsWith('/auth/logout')) { expect(route.request().postDataJSON()).toEqual({ refresh_token: next.refresh_token }); return route.fulfill({ status: 204 }); }
    if (route.request().headers().authorization !== 'Bearer renewed-access') return route.fulfill({ status: 401, json: { error: { code: 'TOKEN_EXPIRED', message: 'Hết hạn' } } });
    if (path.endsWith('/dashboard/today')) return route.fulfill({ json: { date: '2026-11-15', present: 0, late: 0, not_arrived: 0, strangers: 0 } });
    return route.fulfill({ json: { items: [], total: 0, page: 1, size: 10 } });
  });
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click(); await expect(page.getByText('Có mặt', { exact: true })).toBeVisible(); expect(refreshes).toBe(1);
  await page.getByRole('button', { name: 'Menu tài khoản' }).click(); await page.getByRole('menuitem', { name: 'Đăng xuất', exact: true }).click(); await expect(page).toHaveURL(/\/login$/);
});
test('Refresh bị thu hồi: xóa phiên và chặn trang riêng', async ({ page }) => {
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/auth/login')) return route.fulfill({ json: token('OWNER', false) });
    return route.fulfill({ status: 401, json: { error: { code: 'TOKEN_REVOKED', message: 'Phiên đã bị thu hồi' } } });
  });
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click(); await expect(page).toHaveURL(/\/login$/);
});

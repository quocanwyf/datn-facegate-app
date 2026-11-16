import type { Page } from '@playwright/test';
import type { components } from '../src/api/schema';
type Role = components['schemas']['Role'];

// Chỉ dùng trong trình duyệt kiểm thử/review; không ghi vào DB hoặc mã ứng dụng.
export function token(role: Role = 'EMPLOYEE', linked = true, first = false): components['schemas']['TokenPair'] {
  return {
    access_token: 'review-access', refresh_token: 'review-refresh', expires_in: 900, must_change_password: first,
    user: { id: '00000000-0000-4000-8000-000000000001', email: 'review@example.test', roles: [{ role }],
      employee: linked ? { id: '00000000-0000-4000-8000-000000000002', code: 'REVIEW', full_name: 'Tài khoản kiểm thử' } : null },
  };
}
export async function fillLogin(page: Page, email = 'review@example.test') {
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Mật khẩu', { exact: true }).fill('Review123!');
}
export async function mockLogin(page: Page, value = token()) {
  await page.routeWebSocket('**/api/v1/ws/monitor', socket => { socket.onMessage(() => {}); });
  await page.route('**/api/v1/**', route => route.abort());
  await page.route('**/api/v1/auth/login', route => route.fulfill({ json: value }));
}

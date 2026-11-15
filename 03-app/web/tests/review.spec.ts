import { test } from '@playwright/test';
import { token } from './fixtures';

test('Review tương tác — API mô phỏng, không kết nối Hub', async ({ page }) => {
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/auth/login')) {
      const { email, password } = route.request().postDataJSON();
      if (email === 'offline@example.test') return route.abort();
      if (email === 'locked@example.test') return route.fulfill({ status: 429, json: { error: { code: 'REVIEW', message: 'Thử lại sau ít phút' } } });
      if (password !== 'Review123!') return route.fulfill({ status: 401, json: { error: { code: 'REVIEW', message: 'Email hoặc mật khẩu không đúng' } } });
      return route.fulfill({ json: token(email === 'admin@example.test' || email === 'owner@example.test' ? 'OWNER' : 'EMPLOYEE', email !== 'owner@example.test', email === 'first@example.test') });
    }
    if (path.endsWith('/auth/logout') || path.endsWith('/auth/change-password')) return route.fulfill({ status: 204 });
    return route.fulfill({ status: 404, json: { error: { code: 'REVIEW', message: 'Ngoài phạm vi review đăng nhập' } } });
  });
  await page.goto('/login');
  await page.pause();
});

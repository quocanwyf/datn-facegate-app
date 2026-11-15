import { test, expect } from '@playwright/test';
import { fillLogin, mockLogin, token } from './fixtures';
const screens = '../ket-qua-kiem-thu/2026-11-15_T07/screens';

test('Desktop: font tiếng Việt, nhãn, validation và hiện mật khẩu', async ({ page }) => {
  let calls = 0;
  await page.route('**/api/v1/auth/login', route => { calls++; return route.abort(); });
  await page.goto('/login');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByText('Vui lòng nhập email')).toBeVisible();
  await expect(page.getByText('Vui lòng nhập mật khẩu')).toBeVisible();
  expect(calls).toBe(0);
  await fillLogin(page, 'khong-phai-email');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByText('Email không đúng định dạng')).toBeVisible();
  expect(calls).toBe(0);
  await page.getByLabel('Email', { exact: true }).fill('review@example.test');
  await page.getByLabel('Email', { exact: true }).blur();
  await page.getByRole('button', { name: 'Hiện mật khẩu', exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByLabel('Mật khẩu', { exact: true })).toHaveAttribute('type', 'text');
  await page.locator('.ant-input-password-icon').click();
  expect(calls).toBe(0);
  await page.getByLabel('Mật khẩu', { exact: true }).focus();
  await page.screenshot({ path: `${screens}/login-filled.png`, fullPage: true });
  await page.goto('/login');
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.fonts.check('500 28px "Be Vietnam Pro"', 'Đăng nhập'))).toBeTruthy();
  await page.screenshot({ path: `${screens}/login-desktop.png`, fullPage: true });
});

for (const width of [360, 390, 430]) {
  test(`Mobile ${width}px: không cuộn ngang, nút đăng nhập nhìn thấy`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 }); await page.goto('/login');
    await page.evaluate(() => document.fonts.ready);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    await expect(page.getByRole('button', { name: 'Đăng nhập', exact: true })).toBeInViewport();
    await page.screenshot({ path: `${screens}/login-${width}.png`, fullPage: true });
  });
}

for (const [status, message] of [[401, 'Email hoặc mật khẩu không đúng'], [429, 'Thử lại sau ít phút'], [503, 'Hub chưa sẵn sàng']] as const) {
  test(`API ${status}: thông báo lỗi và cho thử lại`, async ({ page }) => {
    await page.route('**/api/v1/auth/login', route => route.fulfill({ status, json: { error: { code: 'TEST_ERROR', message } } }));
    await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await expect(page.getByRole('alert')).toContainText(message);
    await expect(page.getByRole('button', { name: 'Đăng nhập', exact: true })).toBeEnabled();
    if (status === 401) await page.screenshot({ path: `${screens}/login-error.png`, fullPage: true });
  });
}

test('Lỗi mạng: không báo đăng nhập thành công', async ({ page }) => {
  await page.route('**/api/v1/auth/login', route => route.abort());
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Không thể kết nối Hub');
  await expect(page).toHaveURL(/\/login$/);
});

test('Đang gửi: khóa biểu mẫu và chỉ gửi một request', async ({ page }) => {
  let calls = 0;
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/v1/auth/login', async route => { calls++; await gate; await route.fulfill({ json: token() }); });
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByLabel('Email', { exact: true })).toBeDisabled();
  await page.keyboard.press('Enter'); expect(calls).toBe(1);
  release(); await expect(page).toHaveURL(/\/me$/);
});

for (const role of ['OWNER', 'HR', 'SECURITY', 'MANAGER', 'EMPLOYEE'] as const) {
  test(`Đăng nhập ${role}: lựa chọn đúng quyền`, async ({ page }) => {
    await mockLogin(page, token(role)); await page.goto('/login'); await fillLogin(page);
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    if (role === 'EMPLOYEE') {
      await expect(page).toHaveURL(/\/me$/);
      await page.evaluate(() => { history.pushState({}, '', '/admin'); window.dispatchEvent(new PopStateEvent('popstate')); });
      await expect(page.getByText('Bạn không có quyền xem trang này')).toBeVisible();
    } else {
      await expect(page).toHaveURL(/\/choose$/);
      if (role === 'OWNER') await page.screenshot({ path: `${screens}/choose.png`, fullPage: true });
      await page.getByRole('button', { name: 'Trang quản trị', exact: true }).click();
      await expect(page).toHaveURL(role === 'SECURITY' ? /\/admin\/monitor$/ : role === 'MANAGER' ? /\/admin\/attendance$/ : /\/admin$/);
    }
  });
}

test('Quản trị không gắn nhân viên: vào admin, không vào /me', async ({ page }) => {
  await mockLogin(page, token('OWNER', false)); await page.goto('/login'); await fillLogin(page);
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click(); await expect(page).toHaveURL(/\/admin$/);
  await page.evaluate(() => { history.pushState({}, '', '/me'); window.dispatchEvent(new PopStateEvent('popstate')); });
  await expect(page.getByText('Bạn không có quyền xem trang này')).toBeVisible();
});

test('Đổi mật khẩu lần đầu: bắt buộc, kiểm xác nhận và đăng nhập lại', async ({ page }) => {
  await mockLogin(page, token('EMPLOYEE', true, true));
  await page.route('**/api/v1/auth/change-password', async route => {
    expect(route.request().headers().authorization).toBe('Bearer review-access');
    expect(route.request().postDataJSON()).toEqual({ old_password: 'Review123!', new_password: 'NewReview123!' });
    await route.fulfill({ status: 204 });
  });
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Đổi mật khẩu lần đầu' })).toBeVisible();
  await page.screenshot({ path: `${screens}/change-password.png`, fullPage: true });
  await page.getByLabel('Mật khẩu hiện tại', { exact: true }).fill('Review123!');
  await page.getByLabel('Mật khẩu mới', { exact: true }).fill('NewReview123!');
  await page.getByLabel('Nhập lại mật khẩu mới', { exact: true }).fill('KhongKhop');
  await page.getByRole('button', { name: 'Lưu mật khẩu mới' }).click();
  await expect(page.getByText('Mật khẩu nhập lại chưa khớp')).toBeVisible();
  await page.getByLabel('Nhập lại mật khẩu mới', { exact: true }).fill('NewReview123!');
  await page.getByRole('button', { name: 'Lưu mật khẩu mới' }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole('status')).toContainText('Đã đổi mật khẩu');
});

test('Đăng xuất: gửi refresh token, xóa phiên và chặn trang riêng', async ({ page }) => {
  await mockLogin(page);
  await page.route('**/api/v1/auth/logout', async route => {
    expect(route.request().postDataJSON()).toEqual({ refresh_token: 'review-refresh' }); await route.fulfill({ status: 204 });
  });
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await page.getByRole('button', { name: 'Đăng xuất' }).click(); await expect(page).toHaveURL(/\/login$/);
  await page.goto('/me'); await expect(page).toHaveURL(/\/login$/);
});

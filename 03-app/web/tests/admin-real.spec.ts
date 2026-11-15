import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
const screens = '../ket-qua-kiem-thu/2026-11-15_T07/screens';
const inputs = JSON.parse(readFileSync('../ket-qua-kiem-thu/2026-11-15_T07/private-inputs.json', 'utf8')) as { employee_id: string; profile_id: string };
async function login(page: Page, number: number) {
  await page.goto('/login'); await page.getByLabel('Email', { exact: true }).fill(`nv${String(number).padStart(3, '0')}@demo.local`); await page.getByLabel('Mật khẩu', { exact: true }).fill('Demo@123'); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  if (number !== 8) await page.getByRole('button', { name: 'Trang quản trị', exact: true }).click();
}
async function route(page: Page, path: string) { await page.evaluate(path => { history.pushState({}, '', path); window.dispatchEvent(new PopStateEvent('popstate')); }, path); }
async function screenshot(page: Page, name: string) {
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => [...document.querySelectorAll('.admin-content, .ant-table-row')].every(element => { const style = getComputedStyle(element); return Number(style.opacity) >= .999 && style.transform === 'none'; }));
  await page.screenshot({ path: `${screens}/${name}.png`, fullPage: true, mask: [page.locator('.face-grid img')] });
}
for (const [role, number, count] of [['OWNER', 1, 12], ['HR', 2, 11], ['SECURITY', 20, 2], ['MANAGER', 5, 4], ['EMPLOYEE', 8, 0]] as const) {
  test(`Hub thật: menu và route ${role}`, async ({ page }) => {
    await login(page, number);
    if (role === 'EMPLOYEE') { await expect(page).toHaveURL(/\/me$/); await route(page, '/admin/settings'); await expect(page.getByText('Bạn không có quyền xem trang này')).toBeVisible(); }
    else { await expect(page.getByRole('navigation', { name: 'Điều hướng quản trị', exact: true }).getByRole('link')).toHaveCount(count); if (role !== 'OWNER') { await route(page, '/admin/audit'); await expect(page.getByText('Bạn không có quyền xem trang này')).toBeVisible(); } }
  });
}
test('Hub thật: các màn lõi, font tiếng Việt, tạo phòng ban và QR ghép', async ({ page }) => {
  await login(page, 1); await screenshot(page, 'W02-dashboard');
  await route(page, '/admin/employees'); await expect(page.getByText('NV001', { exact: true })).toBeVisible(); await screenshot(page, 'W03-employees');
  await route(page, `/admin/employees/${inputs.employee_id}`); await expect(page.getByRole('tab', { name: 'Thông tin', exact: true })).toBeVisible(); await screenshot(page, 'W04-info');
  await page.getByRole('tab', { name: 'Khuôn mặt', exact: true }).click(); await expect(page.getByAltText('Ảnh mẫu đăng ký khuôn mặt')).toHaveCount(5); await screenshot(page, 'W04-face-masked');
  await route(page, '/admin/organization'); await page.getByRole('button', { name: 'Thêm phòng ban', exact: true }).click(); await page.getByLabel('Tên phòng ban', { exact: true }).fill('Nghiệm thu T07'); await page.getByRole('button', { name: 'Lưu phòng ban', exact: true }).click(); await expect(page.getByRole('dialog')).toHaveCount(0); await screenshot(page, 'W05-departments');
  await page.getByRole('tab', { name: 'Tài khoản', exact: true }).click(); await expect(page.getByRole('table')).toBeVisible(); await screenshot(page, 'W05-users');
  await route(page, '/admin/gates'); await expect(page.getByRole('button', { name: 'Lưu cửa', exact: true })).toBeVisible(); await screenshot(page, 'W07-gates'); await page.getByRole('button', { name: 'Thêm thiết bị', exact: true }).click(); await page.getByLabel('Tên thiết bị').fill('T07 QR review'); await page.getByRole('button', { name: 'Tạo mã ghép', exact: true }).click(); await expect(page.getByText('Mã 6 số')).toBeVisible(); await screenshot(page, 'W07-pairing'); await page.getByRole('button', { name: 'Đóng mã ghép' }).click();
  await route(page, '/admin/settings'); await expect(page.getByText('Số đo trên BLUFR (gallery 1000 người), chưa đo tại văn phòng')).toBeVisible(); await screenshot(page, 'W14-settings');
  await route(page, '/admin/audit'); await expect(page.getByRole('table')).toBeVisible(); await screenshot(page, 'W16-audit');
  for (const font of ['Be Vietnam Pro', 'Inter']) expect(await page.evaluate(font => document.fonts.check(`500 16px "${font}"`, 'Đăng nhập, Nhân viên, Bảng công, Giải trình, Xác nhận khuôn mặt'), font)).toBeTruthy();
});
test('Hub thật: HR chỉ gửi policy/departments, W14 chỉ xem', async ({ page }) => {
  await login(page, 2); await route(page, '/admin/gates'); await expect(page.getByLabel('Tên cửa', { exact: true })).toBeDisabled(); await expect(page.getByRole('button', { name: 'Thêm cửa', exact: true })).toHaveCount(0);
  const request = page.waitForRequest(request => request.method() === 'PATCH' && request.url().includes('/gates/'));
  await page.getByRole('button', { name: 'Lưu cửa', exact: true }).click(); expect(Object.keys((await request).postDataJSON())).toEqual(['default_policy']); await expect(page.getByRole('status').filter({ hasText: 'Đã lưu cửa' })).toBeVisible(); await screenshot(page, 'W07-HR-policy');
  await route(page, '/admin/settings'); await expect(page.getByText('Bạn chỉ có quyền xem cấu hình.')).toBeVisible(); await expect(page.getByRole('button', { name: 'Lưu cấu hình' })).toHaveCount(0); await screenshot(page, 'W14-HR-readonly');
  await route(page, '/admin/organization'); await page.getByRole('tab', { name: 'Tài khoản', exact: true }).click(); await expect(page.getByRole('button', { name: 'Sửa tài khoản nv001@demo.local', exact: true })).toHaveCount(0);
});
test('Hub thật: duyệt bộ 5 ảnh U03, gallery thực sự thay đổi', async ({ page }) => {
  await login(page, 2); await route(page, '/admin/faces'); await expect(page.getByAltText('Ảnh mẫu đăng ký khuôn mặt')).toHaveCount(5); await screenshot(page, 'W08-pending-masked');
  const result = page.waitForResponse(response => response.url().endsWith(`/face-profiles/${inputs.profile_id}/approve`) && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Xác nhận', exact: true }).click(); expect((await result).status()).toBe(200); await expect(page.getByText('Không có hồ sơ chờ xác nhận')).toBeVisible(); await screenshot(page, 'W08-approved-empty');
  const health = await page.request.get('/api/v1/health'); expect((await health.json()).gallery_size).toBe(1);
});

function socketMessage(socket: WebSocket, type: string): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { socket.removeEventListener('message', receive); reject(new Error('Không nhận được config Kiosk')); }, 15000);
    function receive(event: MessageEvent) { const value = JSON.parse(String(event.data)); if (value.type === type) { clearTimeout(timer); socket.removeEventListener('message', receive); resolve(value); } }
    socket.addEventListener('message', receive);
  });
}
test('Hub thật: OWNER lưu cấu hình nguyên khối và Kiosk nhận config', async ({ page }) => {
  const loginResponse = await page.request.post('/api/v1/auth/login', { data: { email: 'nv001@demo.local', password: 'Demo@123' } });
  const identity = await loginResponse.json(); const headers = { Authorization: `Bearer ${identity.access_token}` };
  const gates = await (await page.request.get('/api/v1/gates', { headers })).json();
  const invitation = await (await page.request.post('/api/v1/devices', { headers, data: { gate_id: gates[0].id, name: 'T07 config receiver' } })).json();
  const paired = await (await page.request.post('/api/v1/kiosk/pair', { data: { code: invitation.pairing_code } })).json();
  const before = await (await page.request.get('/api/v1/settings/recognition', { headers })).json();
  const socket = new WebSocket('ws://127.0.0.1:8007/api/v1/ws/kiosk');
  const first = socketMessage(socket, 'config');
  await new Promise<void>((resolve, reject) => { socket.addEventListener('open', () => resolve(), { once: true }); socket.addEventListener('error', () => reject(new Error('Không mở được WS')), { once: true }); });
  socket.send(JSON.stringify({ type: 'auth', device_token: paired.device_token })); await first;
  try {
    await login(page, 1); await route(page, '/admin/settings');
    await expect(page.getByLabel('Ngưỡng L', { exact: true })).toBeDisabled();
    await page.getByLabel('Cửa sổ W (khung)', { exact: true }).fill('2');
    await page.getByRole('button', { name: 'Lưu cấu hình', exact: true }).click();
    await expect(page.getByText('Ngưỡng đếm không được lớn hơn W').first()).toBeVisible();
    expect((await (await page.request.get('/api/v1/settings/recognition', { headers })).json()).window_size).toBe(before.window_size);
    await page.getByLabel('Cửa sổ W (khung)', { exact: true }).fill(String(before.window_size));
    const changed = before.max_fps === 4 ? 5 : 4;
    await page.getByLabel('Khung hình tối đa (khung/giây)', { exact: true }).fill(String(changed));
    await page.getByRole('button', { name: 'Lưu cấu hình', exact: true }).click();
    const config = socketMessage(socket, 'config');
    await page.getByRole('button', { name: 'Xác nhận lưu', exact: true }).click();
    expect((await config).max_fps).toBe(changed);
    await expect(page.getByRole('status').filter({ hasText: 'Đã lưu toàn bộ cấu hình' })).toBeVisible();
  } finally {
    await page.request.put('/api/v1/settings/recognition', { headers, data: before });
    socket.close(); await page.request.post(`/api/v1/devices/${invitation.device.id}/revoke`, { headers });
  }
});
test('Hub thật: sửa phòng ban và chặn tên trùng, giữ biểu mẫu', async ({ page }) => {
  await login(page, 1); await route(page, '/admin/organization');
  await page.getByRole('button', { name: 'Sửa phòng ban Nghiệm thu T07', exact: true }).click();
  await page.getByLabel('Tên phòng ban', { exact: true }).fill('Nghiệm thu T07 đã sửa');
  await page.getByRole('button', { name: 'Lưu phòng ban', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('cell', { name: 'Nghiệm thu T07 đã sửa', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Thêm phòng ban', exact: true }).click();
  await page.getByLabel('Tên phòng ban', { exact: true }).fill('Nghiệm thu T07 đã sửa');
  const response = page.waitForResponse(response => response.url().endsWith('/departments') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Lưu phòng ban', exact: true }).click(); expect((await response).status()).toBe(409);
  await expect(page.getByRole('dialog').getByRole('alert')).toBeVisible();
  await expect(page.getByLabel('Tên phòng ban', { exact: true })).toHaveValue('Nghiệm thu T07 đã sửa');
});

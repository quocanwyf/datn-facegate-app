// API và UI thật trên DB T10 riêng từ start_t10_hub.py; không chèn ngày công/event.
import { test, expect, type APIRequestContext, type Page } from '@playwright/test';
const screens = '../ket-qua-kiem-thu/2026-11-16_T10/screens';
async function login(page: Page, number: number) {
  await page.goto('/login'); await page.getByLabel('Email', { exact: true }).fill(`nv${String(number).padStart(3, '0')}@demo.local`); await page.getByLabel('Mật khẩu', { exact: true }).fill('Demo@123');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click(); await page.getByRole('button', { name: 'Trang quản trị', exact: true }).click();
}
async function route(page: Page, path: string) { await page.evaluate(path => { history.pushState({}, '', path); window.dispatchEvent(new PopStateEvent('popstate')); }, path); }
async function shot(page: Page, name: string) { await page.evaluate(() => document.fonts.ready); await page.waitForFunction(() => { const element = document.querySelector('.admin-content'); return element && Number(getComputedStyle(element).opacity) >= .999; }); await page.screenshot({ path: `${screens}/${name}.png`, fullPage: true }); }
const date = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
async function createOwnRequest(request: APIRequestContext, number: number) {
  const login = await request.post('/api/v1/auth/login', { data: { email: `nv${String(number).padStart(3, '0')}@demo.local`, password: 'Demo@123' } });
  expect(login.status()).toBe(200); const pair = await login.json(); const headers = { Authorization: `Bearer ${pair.access_token}` };
  const pending = await (await request.get('/api/v1/me/requests?status=PENDING&size=100', { headers })).json();
  for (const row of pending.items) if (row.reason === 'T10 review qua API thật' && row.work_date === date) expect((await request.post(`/api/v1/me/requests/${row.id}/cancel`, { headers })).status()).toBe(200);
  const created = await request.post('/api/v1/me/requests', { headers, data: { work_date: date, type: 'FORGOT_IN', requested_in: `${date}T08:30:00+07:00`, reason: 'T10 review qua API thật' } });
  expect(created.status()).toBe(201); return (await created.json()).id as string;
}

test('Hub thật: tạo ca, bảng công/Excel, tự bảo vệ và Manager duyệt giải trình', async ({ page, browser }) => {
  await createOwnRequest(page.request, 1); const target = await createOwnRequest(page.request, 6);
  await login(page, 1); await route(page, '/admin/schedules');
  await page.getByRole('button', { name: 'Thêm ca', exact: true }).click();
  const name = `Review T10 ${Date.now()}`;
  await page.getByLabel('Tên ca', { exact: true }).fill(name);
  for (const [label, value] of [['Giờ bắt đầu', '08:30'], ['Giờ kết thúc', '17:30']] as const) { await page.getByLabel(label, { exact: true }).fill(value); await page.getByLabel(label, { exact: true }).press('Enter'); }
  await page.getByRole('button', { name: 'Lưu ca', exact: true }).click();
  await expect(page.getByRole('cell', { name, exact: true })).toBeVisible(); await shot(page, 'W06-real-shifts');
  await route(page, '/admin/attendance');
  await expect(page.getByRole('cell', { name: 'NV006', exact: true })).toBeVisible();
  await expect(page.locator('.attendance-cell').filter({ hasText: 'C' }).first()).toBeVisible();
  const downloaded = page.waitForEvent('download'); await page.getByRole('button', { name: 'Xuất Excel', exact: true }).click();
  const workbook = await downloaded; expect(workbook.suggestedFilename()).toMatch(/^bang-cong-\d{4}-\d{2}\.xlsx$/);
  await workbook.saveAs(`../ket-qua-kiem-thu/2026-11-16_T10/${workbook.suggestedFilename()}`);
  await shot(page, 'W09-real-month');
  await page.getByRole('button', { name: new RegExp(`^NV001 ${date} `) }).click();
  await expect(page.getByRole('button', { name: 'Sửa ngày công', exact: true })).toHaveCount(0);
  await page.locator('.ant-drawer-close').click();
  await route(page, '/admin/requests'); await expect(page.getByText('Không tự duyệt', { exact: true })).toBeVisible(); await shot(page, 'W12-real-self-protection');
  const manager = await browser.newPage({ baseURL: 'http://127.0.0.1:5181', viewport: { width: 1440, height: 1000 } });
  try {
    await login(manager, 5); await route(manager, '/admin/requests');
    await expect(manager.getByRole('button', { name: `Duyệt NV006 ${date}`, exact: true })).toBeVisible(); await shot(manager, 'W12-real-manager-pending');
    const approved = manager.waitForResponse(response => response.url().endsWith(`/attendance/requests/${target}/approve`) && response.request().method() === 'POST');
    await manager.getByRole('button', { name: `Duyệt NV006 ${date}`, exact: true }).click(); await manager.getByRole('button', { name: 'Xác nhận duyệt', exact: true }).click();
    expect((await approved).status()).toBe(200); await expect(manager.getByText('Đã duyệt giải trình và tính lại ngày công', { exact: true })).toBeVisible();
    await shot(manager, 'W12-real-approved');
  } finally { await manager.close(); }
});

test('Hub thật: tạo/xóa phân ca và ngày lễ qua giao diện', async ({ page }) => {
  await login(page, 1); await route(page, '/admin/schedules');
  await expect(page.getByRole('button', { name: 'Thêm ca', exact: true })).toBeVisible();
  const shiftName = 'Hành chính'; // Tên ca từ seed.sql chính thức.
  await expect(page.getByRole('cell', { name: shiftName, exact: true })).toBeVisible();
  await page.getByRole('tab', { name: 'Phân ca', exact: true }).click();
  await page.getByRole('radiogroup', { name: 'Loại đối tượng phân ca', exact: true }).getByText('Nhân viên', { exact: true }).click();
  await expect(page.getByRole('radio', { name: 'Nhân viên', exact: true })).toBeChecked();
  await page.getByRole('combobox', { name: 'Đối tượng phân ca', exact: true }).fill('NV009');
  await page.locator('.ant-select-dropdown:visible').getByText('NV009 · Ngô Đức Long', { exact: true }).click();
  await page.getByRole('button', { name: 'Thêm phân ca', exact: true }).click();
  await page.getByLabel('Ca làm việc', { exact: true }).click(); await page.locator('.ant-select-dropdown:visible').getByText(shiftName, { exact: true }).click();
  await page.getByLabel('Các thứ', { exact: true }).click(); await page.locator('.ant-select-dropdown:visible').getByText('Thứ 7', { exact: true }).click(); await page.keyboard.press('Escape');
  await page.getByLabel('Hiệu lực từ', { exact: true }).fill('02/01/2031'); await page.getByLabel('Hiệu lực từ', { exact: true }).press('Enter');
  await page.getByRole('button', { name: 'Lưu phân ca', exact: true }).click();
  await expect(page.locator('.week-grid').getByText(shiftName, { exact: true })).toBeVisible(); await shot(page, 'W06-real-assignment');
  await page.locator('.week-grid').getByRole('button', { name: 'Xóa', exact: true }).click(); await page.getByRole('button', { name: 'Xóa phân ca', exact: true }).click();
  await expect(page.locator('.week-grid').getByText(shiftName, { exact: true })).toHaveCount(0);
  await page.getByRole('tab', { name: 'Ngày lễ', exact: true }).click(); await page.getByRole('button', { name: 'Thêm ngày lễ', exact: true }).click();
  const name = `Ngày lễ review T10 ${Date.now()}`;
  await page.getByLabel('Ngày nghỉ lễ', { exact: true }).fill('02/01/2031'); await page.getByLabel('Ngày nghỉ lễ', { exact: true }).press('Enter');
  await page.getByLabel('Tên ngày lễ', { exact: true }).fill(name); await page.getByRole('button', { name: 'Lưu ngày lễ', exact: true }).click();
  await expect(page.getByRole('cell', { name, exact: true })).toBeVisible(); await shot(page, 'W06-real-holiday');
  await page.getByRole('row').filter({ hasText: name }).getByRole('button', { name: 'Xóa', exact: true }).click(); await page.getByRole('button', { name: 'Xóa ngày lễ', exact: true }).click();
  await expect(page.getByRole('cell', { name, exact: true })).toHaveCount(0);
});

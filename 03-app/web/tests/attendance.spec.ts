// Fixture chỉ trong trình duyệt; không tạo event/ngày công trong DB.
import { test, expect, type Page } from '@playwright/test';
import type { components } from '../src/api/schema';
import { employeeApi, seedEmployees, seedDepartments } from './employee-fixtures';
import { token, fillLogin } from './fixtures';
const screens = '../ket-qua-kiem-thu/2026-11-16_T10/screens';
const shift = { id: '10000000-0000-4000-8000-000000000001', name: 'Hành chính', start_time: '08:30', end_time: '17:30', break_start: '12:00', break_end: '13:00', grace_in_min: 10, grace_out_min: 10 };
const brief = (number: number) => { const row = seedEmployees[number]!; return { id: row.id, code: row.code, full_name: row.full_name, department_id: row.department_id, department_name: row.department_name }; };
async function setup(page: Page, role: 'OWNER' | 'HR' | 'MANAGER' = 'OWNER') {
  await page.clock.setFixedTime(new Date('2026-11-16T02:00:00Z'));
  const state = await employeeApi(page, role); const writes: string[] = [];
  const days: components['schemas']['AttendanceDay'][] = [0, 5].map((number, index) => ({ id: `20000000-0000-4000-8000-00000000000${index}`, employee: brief(number), work_date: '2026-11-16', shift,
    check_in_at: null, check_out_at: null, status: 'WAITING_IN', suspect_forgot_out: false, late_min: 0, early_min: 0, worked_min: 0, source: 'AUTO', finalized: false }));
  const requests: components['schemas']['AttendanceRequest'][] = [0, 5].map((number, index) => ({ id: `30000000-0000-4000-8000-00000000000${index}`, employee: brief(number), work_date: '2026-11-16', type: 'FORGOT_IN', requested_in: '2026-11-16T08:30:00+07:00', reason: 'Kiểm tra giao diện giải trình', status: 'PENDING', created_at: '2026-11-16T02:00:00Z', can_review: true }));
  await page.route('**/api/v1/**', async route => {
    const request = route.request(), url = new URL(request.url()), path = url.pathname.replace('/api/v1', '');
    if (path === '/auth/login') { const session = token(role); session.user.employee = brief(0); return route.fulfill({ json: session }); }
    if (path === '/shifts') return route.fulfill({ status: request.method() === 'POST' ? 201 : 200, json: request.method() === 'POST' ? shift : [shift] });
    if (path === '/holidays') return route.fulfill({ json: [{ date: '2026-11-20', name: 'Ngày lễ kiểm giao diện' }] });
    if (path === '/shift-assignments') return request.method() === 'POST' ? route.fulfill({ status: 409, json: { error: { code: 'ASSIGNMENT_OVERLAP', message: 'Phân ca trùng khoảng hiệu lực.' } } }) : route.fulfill({ json: [] });
    if (path === '/attendance/days') return route.fulfill({ json: { items: days, total: days.length, page: 1, size: 100 } });
    if (path.startsWith('/attendance/days/')) { writes.push(path); return route.fulfill({ json: { ...days[1], source: 'MANUAL', edit_reason: request.postDataJSON().reason } }); }
    if (path === '/attendance/export') { writes.push(url.search); return route.fulfill({ contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers: { 'Content-Disposition': 'attachment; filename="bang-cong-2026-11.xlsx"' }, body: 'UI download contract fixture; actual workbook verified in T09' }); }
    if (path === '/attendance/requests') return route.fulfill({ json: { items: requests.filter(row => row.status === url.searchParams.get('status')), total: requests.filter(row => row.status === url.searchParams.get('status')).length, page: 1, size: 100 } });
    if (/\/attendance\/requests\/[^/]+\/(approve|reject)$/.test(path)) { writes.push(path); return route.fulfill({ json: { ...requests[1], status: path.endsWith('/approve') ? 'APPROVED' : 'REJECTED' } }); }
    return route.fallback();
  });
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await page.getByRole('button', { name: 'Trang quản trị', exact: true }).click();
  return { state, writes, days };
}
async function route(page: Page, path: string) { await page.evaluate(path => { history.pushState({}, '', path); window.dispatchEvent(new PopStateEvent('popstate')); }, path); }
async function shot(page: Page, name: string) { await page.evaluate(() => document.fonts.ready); await page.waitForFunction(() => { const element = document.querySelector('.admin-content'); if (!element) return false; const style = getComputedStyle(element); return Number(style.opacity) >= .999 && ['none', 'matrix(1, 0, 0, 1, 0, 0)'].includes(style.transform); }); await page.screenshot({ path: `${screens}/${name}.png`, fullPage: true }); }

test('W09: WAITING_IN, màu token, không sửa bản thân, sửa người khác có lý do', async ({ page }) => {
  const { writes } = await setup(page); await route(page, '/admin/attendance');
  const own = page.getByRole('button', { name: 'NV001 2026-11-16 Chưa đến — tạm thời', exact: true });
  await expect(own).toHaveText('C'); await expect(own).toHaveCSS('background-color', 'rgb(227, 242, 253)');
  await shot(page, 'W09-waiting-fixture'); await own.click();
  await expect(page.getByText('Ngày công chưa chốt — kết quả tạm thời')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Sửa ngày công', exact: true })).toHaveCount(0);
  await page.locator('.ant-drawer-close').click();
  await page.getByRole('button', { name: 'NV006 2026-11-16 Chưa đến — tạm thời', exact: true }).click();
  await page.getByRole('button', { name: 'Sửa ngày công', exact: true }).click();
  await page.getByRole('button', { name: 'Lưu ngày công', exact: true }).click(); expect(writes).toHaveLength(0);
  await page.getByLabel('Lý do sửa', { exact: true }).fill('Đối chiếu sổ trực');
  await page.getByRole('button', { name: 'Lưu ngày công', exact: true }).click();
  await expect(page.getByText('Đã sửa ngày công', { exact: true })).toBeVisible(); expect(writes).toHaveLength(1);
});

test('W12: không hiện duyệt bản thân kể cả server trả can_review=true', async ({ page }) => {
  await setup(page); await route(page, '/admin/requests');
  await expect(page.getByRole('button', { name: 'Duyệt NV001 2026-11-16', exact: true })).toHaveCount(0);
  await expect(page.getByText('Không tự duyệt', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Duyệt NV006 2026-11-16', exact: true })).toBeVisible();
  await shot(page, 'W12-pending-fixture');
  await page.getByRole('button', { name: 'Từ chối NV006 2026-11-16', exact: true }).click();
  await page.getByRole('button', { name: 'Xác nhận từ chối', exact: true }).click();
  await expect(page.getByText('Nhập lý do từ chối', { exact: true })).toBeVisible();
});

test('W06: phân ca trùng giữ form, thông báo tiếng Việt', async ({ page }) => {
  await setup(page); await route(page, '/admin/schedules'); await expect(page.getByText('Hành chính', { exact: true })).toBeVisible(); await shot(page, 'W06-shifts-fixture');
  await page.getByRole('tab', { name: 'Phân ca', exact: true }).click();
  await page.getByRole('combobox', { name: 'Đối tượng phân ca', exact: true }).click(); await page.locator('.ant-select-dropdown:visible').getByText(seedDepartments[0]!.name, { exact: true }).click();
  await page.getByRole('button', { name: 'Thêm phân ca', exact: true }).click();
  await page.getByLabel('Ca làm việc', { exact: true }).click(); await page.locator('.ant-select-dropdown:visible').getByText('Hành chính', { exact: true }).click();
  await page.getByLabel('Các thứ', { exact: true }).click(); await page.locator('.ant-select-dropdown:visible').getByText('Thứ 2', { exact: true }).click(); await page.keyboard.press('Escape');
  await page.getByLabel('Hiệu lực từ', { exact: true }).fill('16/11/2026'); await page.getByLabel('Hiệu lực từ', { exact: true }).press('Enter');
  await page.getByRole('button', { name: 'Lưu phân ca', exact: true }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'Đã có phân ca trùng thời gian cho thứ này' })).toBeVisible();
  await expect(page.getByRole('dialog')).toBeVisible(); await shot(page, 'W06-overlap-fixture');
});

test('MANAGER: xuất Excel không tự thêm lọc ngoài team, không có nút sửa/nghỉ', async ({ page }) => {
  const { writes } = await setup(page, 'MANAGER'); await route(page, '/admin/attendance');
  await expect(page.getByRole('button', { name: 'Đánh dấu nghỉ', exact: true })).toHaveCount(0);
  const downloaded = page.waitForEvent('download'); await page.getByRole('button', { name: 'Xuất Excel', exact: true }).click();
  expect((await downloaded).suggestedFilename()).toBe('bang-cong-2026-11.xlsx'); expect(writes[0]).toBe('?month=2026-11');
  await page.getByRole('button', { name: 'NV006 2026-11-16 Chưa đến — tạm thời', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Sửa ngày công', exact: true })).toHaveCount(0);
});

// Chỉ fixture browser; không phải dữ liệu chấm công hay sinh trắc thật.
import { test, expect, type Page } from '@playwright/test';
import { token, fillLogin } from './fixtures';
import type { components } from '../src/api/schema';
const screens = '../ket-qua-kiem-thu/2026-11-16_T12/screens';
const employee = token().user.employee!;
const shift = { id: 'shift', name: 'Ca hành chính', start_time: '08:30', end_time: '17:30' };
const day: components['schemas']['AttendanceDay'] = { id: 'day', employee, work_date: '2026-11-16', shift, status: 'WAITING_IN', source: 'AUTO', finalized: false, suspect_forgot_out: false, late_min: 0, early_min: 0, worked_min: 0 };
const request: components['schemas']['AttendanceRequest'] = { id: 'request', employee, work_date: '2026-11-16', type: 'FORGOT_IN', status: 'PENDING', reason: 'Quên quét lúc vào', requested_in: '2026-11-16T01:30:00Z', created_at: '2026-11-16T02:00:00Z', can_review: true };
async function setup(page: Page, manager = false) {
  let todayDay = day, cancelled = false, revokeCalls = 0; let extraToday: Partial<components['schemas']['MeToday']> = {}; const sent: Record<string, unknown>[] = [], reviews: unknown[] = [];
  let face = { attendance_method: 'FACE', face_consent_at: '2026-11-15T02:00:00Z', face_profile_status: 'ACTIVE' };
  await page.routeWebSocket('**/api/v1/ws/monitor', socket => socket.onMessage(() => {}));
  await page.route('**/api/v1/**', route => {
    const req = route.request(), url = new URL(req.url()), path = url.pathname.replace('/api/v1', '');
    if (path === '/auth/login') return route.fulfill({ json: token(manager ? 'MANAGER' : 'EMPLOYEE') });
    if (path === '/me/today') return route.fulfill({ json: { date: '2026-11-16', shift, attendance_method: 'MANUAL', day: todayDay, passes: [{ occurred_at: '2026-11-16T02:00:00Z', gate_name: 'Cửa phụ', gate_mode: 'ACCESS_ONLY', result: 'MATCH' }], ...extraToday } });
    if (path === '/me/attendance') return route.fulfill({ json: { month: url.searchParams.get('month'), days: [todayDay], summary: { work_days: 1, late_count: 1, late_minutes: 11, missing_or_absent: 0 } } });
    if (path.startsWith('/me/days/')) return route.fulfill({ json: { day: { ...todayDay, suspect_forgot_out: true }, events: [], request: cancelled ? null : request } });
    if (path === '/me/requests' && req.method() === 'GET') return route.fulfill({ json: { items: url.searchParams.get('status') === 'PENDING' && !cancelled ? [request] : [], total: url.searchParams.get('status') === 'PENDING' && !cancelled ? 1 : 0, page: 1, size: 100 } });
    if (path === '/me/requests' && req.method() === 'POST') { sent.push(req.postDataJSON()); return route.fulfill({ status: 409, json: { error: { code: 'REQUEST_PENDING_EXISTS', message: 'Đã tồn tại' } } }); }
    if (path.endsWith('/cancel')) { cancelled = true; return route.fulfill({ json: { ...request, status: 'CANCELLED' } }); }
    if (path === '/me/face') return route.fulfill({ json: face });
    if (path === '/me/face/revoke') { revokeCalls++; face = { attendance_method: 'MANUAL', face_consent_at: '', face_profile_status: '' }; return revokeCalls === 1 ? route.fulfill({ status: 503, json: { error: { code: 'BIOMETRIC_DELETE_INCOMPLETE', message: 'Xóa chưa hoàn tất, vui lòng thử lại.' } } }) : route.fulfill({ status: 204 }); }
    if (path === '/attendance/requests') return route.fulfill({ json: { items: [request, { ...request, id: 'other', employee: { ...employee, id: 'other-person', code: 'NV007', full_name: 'Nhân viên team' } }], total: 2, page: 1, size: 100 } });
    if (/\/attendance\/requests\/other\/(approve|reject)/.test(path)) { reviews.push(req.postDataJSON()); return route.fulfill({ json: { ...request, status: 'REJECTED' } }); }
    return route.fulfill({ status: 404, json: { error: { code: 'REVIEW_ONLY', message: 'Ngoài fixture T12' } } });
  });
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click(); if (manager) await page.getByRole('button', { name: 'Trang cá nhân', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Ngày làm việc của bạn' })).toBeVisible();
  return { sent, reviews, revokes: () => revokeCalls, setDay: (value: typeof day) => { todayDay = value; }, setToday: (value: typeof extraToday) => { extraToday = value; } };
}
async function route(page: Page, path: string) { await page.evaluate(path => { history.pushState({}, '', path); window.dispatchEvent(new PopStateEvent('popstate')); }, path); }
async function shot(page: Page, name: string) {
  await page.evaluate(() => document.fonts.ready); expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  const nav = page.getByRole('navigation', { name: 'Điều hướng cá nhân' }); await expect(nav).toBeInViewport(); const box = await nav.boundingBox(); expect(box!.y + box!.height).toBeCloseTo(844, 0);
  await page.screenshot({ path: `${screens}/${name}.png`, fullPage: true });
}
test('390×844: hôm nay 3 trạng thái, tháng/ngày và footer không tràn', async ({ page }) => {
  const state = await setup(page); await expect(page.getByText('Chưa đến — tạm thời', { exact: true })).toBeVisible(); await expect(page.getByText('Không tính công', { exact: true })).toBeVisible(); await shot(page, 'E02-waiting');
  state.setDay({ ...day, status: 'IN_PROGRESS', check_in_at: '2026-11-16T01:41:00Z' }); await page.getByRole('button', { name: 'Làm mới hôm nay' }).click(); await expect(page.getByText('08:41', { exact: true })).toBeVisible(); await shot(page, 'E02-in');
  state.setDay({ ...day, status: 'LATE', finalized: true, check_in_at: '2026-11-16T01:41:00Z', check_out_at: '2026-11-16T10:30:00Z', late_min: 11, worked_min: 469 }); await page.getByRole('button', { name: 'Làm mới hôm nay' }).click(); await expect(page.getByText('17:30', { exact: true })).toBeVisible(); await shot(page, 'E02-out');
  await page.getByRole('link', { name: 'Bảng công', exact: true }).click(); await expect(page.getByText('Ngày công', { exact: true })).toBeVisible(); await shot(page, 'E03-month');
  await route(page, '/me/days/2026-11-16'); await expect(page.getByText('Có thể bạn quên quét khi ra về')).toBeVisible(); await expect(page.getByRole('link', { name: 'Gửi giải trình', exact: true })).toHaveCount(0); await shot(page, 'E04-day');
  await route(page, '/me/days/2026-99-99'); await expect(page.getByText('Ngày không hợp lệ', { exact: true })).toBeVisible();
});
test('E05/E06: validation, giờ có offset, 409 giữ lý do, hủy giải trình', async ({ page }) => {
  const state = await setup(page); await route(page, '/me/requests/new?date=2026-11-16'); await page.getByRole('button', { name: 'Gửi giải trình', exact: true }).click(); await expect(page.getByText('Nhập giờ vào đề nghị')).toBeVisible(); expect(state.sent).toHaveLength(0);
  await page.getByLabel('Giờ vào đề nghị').fill('08:30'); await page.getByLabel('Giờ vào đề nghị').press('Enter'); await page.getByLabel('Lý do', { exact: true }).fill('Quên quét buổi sáng'); await page.getByRole('button', { name: 'Gửi giải trình', exact: true }).click(); await expect(page.getByRole('alert')).toContainText('Ngày này đã có giải trình đang chờ duyệt'); expect(state.sent[0]?.requested_in).toBe('2026-11-16T01:30:00.000Z'); await expect(page.getByLabel('Lý do', { exact: true })).toHaveValue('Quên quét buổi sáng'); await shot(page, 'E05-request');
  await route(page, '/me/requests'); await expect(page.getByText(request.reason, { exact: true })).toBeVisible(); await shot(page, 'E06-requests'); await page.getByRole('button', { name: 'Hủy giải trình', exact: true }).click(); await page.getByRole('button', { name: 'Xác nhận hủy', exact: true }).click(); await expect(page.getByText('Chưa có giải trình', { exact: true })).toBeVisible();
});
test('E08: không ảnh mẫu; lỗi xóa vẫn MANUAL và thử lại, chỉ báo thành công sau 204', async ({ page }) => {
  const state = await setup(page); await page.getByRole('link', { name: 'Khuôn mặt', exact: true }).click(); await expect(page.getByText('Phương thức: Khuôn mặt', { exact: true })).toBeVisible(); await expect(page.locator('.me-content img')).toHaveCount(0); await shot(page, 'E08-face');
  await page.getByRole('button', { name: 'Rút đồng ý và xoá dữ liệu khuôn mặt', exact: true }).click(); await page.getByRole('button', { name: 'Rút đồng ý và xóa', exact: true }).click(); await expect(page.getByRole('alert')).toContainText('Xóa chưa hoàn tất'); expect(state.revokes()).toBe(1); await expect(page.getByText('Phương thức: Chấm công hộ', { exact: true })).toBeVisible(); await page.getByRole('button', { name: 'Rút đồng ý và xóa', exact: true }).click(); await expect(page.getByRole('status')).toContainText('Đã rút đồng ý'); expect(state.revokes()).toBe(2);
});
test('E10: không hiển thị bản thân dù can_review sai; từ chối bắt buộc ghi chú', async ({ page }) => {
  const state = await setup(page, true); await page.getByRole('link', { name: 'Duyệt', exact: true }).click(); await expect(page.getByRole('heading', { name: 'Nhân viên team · NV007' })).toBeVisible(); await expect(page.getByRole('heading', { name: /Tài khoản kiểm thử/ })).toHaveCount(0); await shot(page, 'E10-team');
  await page.getByRole('button', { name: 'Từ chối', exact: true }).click(); await page.getByRole('button', { name: 'Xác nhận', exact: true }).click(); await expect(page.getByText('Nhập lý do từ chối', { exact: true })).toBeVisible(); expect(state.reviews).toHaveLength(0); await page.getByLabel('Lý do từ chối').fill('Cần bổ sung lý do'); await page.getByRole('button', { name: 'Xác nhận', exact: true }).click(); await expect(page.getByText('Đã xử lý giải trình', { exact: true })).toBeVisible(); expect(state.reviews).toEqual([{ note: 'Cần bổ sung lý do' }]);
});

test('E02: ngày lễ ưu tiên, không ca và MANUAL đúng thông điệp', async ({ page }) => {
  const state = await setup(page); state.setToday({ holiday: 'Ngày lễ thử giao diện', shift: null, day: { ...day, status: 'HOLIDAY' } }); await page.getByRole('button', { name: 'Làm mới hôm nay' }).click(); await expect(page.getByRole('heading', { name: 'Hôm nay là ngày lễ: Ngày lễ thử giao diện' })).toBeVisible(); await shot(page, 'E02-holiday');
  state.setToday({ holiday: null, shift: null, day: { ...day, status: 'OFF' } }); await page.getByRole('button', { name: 'Làm mới hôm nay' }).click(); await expect(page.getByRole('heading', { name: 'Hôm nay bạn không có ca' })).toBeVisible(); await expect(page.getByText('Bạn chấm công tại quầy lễ tân', { exact: true })).toBeVisible();
});

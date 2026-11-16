// Double giao thức/UI trong browser; không ghi nhận dạng hoặc ảnh giả vào DB.
import { test, expect, type Page, type WebSocketRoute } from '@playwright/test';
import type { components } from '../src/api/schema';
import { token, fillLogin } from './fixtures';
import { seedEmployees, seedDepartments } from './employee-fixtures';
const screens = '../ket-qua-kiem-thu/2026-11-16_T11/screens';
const gate = { id: '10000000-0000-4000-8000-000000000001', name: 'Cửa kiểm giao diện', mode: 'ATTENDANCE_ACCESS' as const, default_policy: 'ALLOW_ALL_ACTIVE' as const, threshold_level: 'DEFAULT_VAL' as const, cos_threshold: .4233, is_active: true, allowed_department_ids: [], devices: [] };
const event: components['schemas']['Event'] = { id: '20000000-0000-4000-8000-000000000001', occurred_at: '2026-11-16T02:00:00Z', gate, result: 'UNKNOWN', door_action: 'NONE', has_snapshot: false, n_frames: 5, top1_score: .1, threshold_used: .4233 };
async function setup(page: Page, role: 'OWNER' | 'HR' | 'SECURITY' = 'OWNER') {
  let peer: WebSocketRoute | undefined; const authFrames: Record<string, unknown>[] = []; const handled: unknown[] = []; let refreshes = 0;
  await page.routeWebSocket('**/api/v1/ws/monitor', socket => { peer = socket; socket.onMessage(message => { const frame = JSON.parse(String(message)); authFrames.push(frame); socket.send(JSON.stringify({ type: 'counters', open_alerts: 0, pending_face_profiles: 0, pending_requests: 0 })); }); });
  await page.route('**/api/v1/**', async route => {
    const request = route.request(), path = new URL(request.url()).pathname.replace('/api/v1', '');
    if (path === '/auth/login') return route.fulfill({ json: token(role) });
    if (path === '/auth/refresh') { refreshes++; return route.fulfill({ json: { ...token(role), access_token: 'review-renewed', refresh_token: 'review-rotated' } }); }
    if (path === '/health') return route.fulfill({ json: { status: 'ok', db: true, gpu: false, model_verified: true, gallery_size: 1, version: 'UI fixture' } });
    if (path === '/gates') return route.fulfill({ json: [gate] });
    if (path === '/departments') return route.fulfill({ json: seedDepartments });
    if (path === '/employees') { const rows = role === 'SECURITY' ? seedEmployees.filter(row => row.attendance_method === 'MANUAL' && row.status === 'ACTIVE') : seedEmployees; return route.fulfill({ json: { items: rows, page: 1, size: 100, total: rows.length } }); }
    if (path === '/events/manual-report') return route.fulfill({ json: [] });
    if (path === '/events') return route.fulfill({ json: { items: [], total: 0, page: 1, size: 100 } });
    if (path.endsWith('/snapshot')) return route.fulfill({ status: 404, json: { error: { code: 'HTTP_404', message: 'Không còn ảnh cảnh báo.' } } });
    if (path.endsWith('/handle')) { const body = request.postDataJSON(); handled.push(body); peer?.send(JSON.stringify({ type: 'alert_handled', event_id: event.id, handling: { ...body, handled_by: 'Bảo vệ kiểm thử', handled_at: '2026-11-16T02:01:00Z' } })); return route.fulfill({ json: { ...event, handling: { ...body, handled_by: 'Bảo vệ kiểm thử', handled_at: '2026-11-16T02:01:00Z' } } }); }
    return route.fulfill({ status: 404, json: { error: { code: 'REVIEW_ONLY', message: 'Ngoài phạm vi fixture giám sát' } } });
  });
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click(); await page.getByRole('button', { name: 'Trang quản trị', exact: true }).click();
  await page.evaluate(() => { history.pushState({}, '', '/admin/monitor'); window.dispatchEvent(new PopStateEvent('popstate')); });
  await expect.poll(() => authFrames.length).toBe(1);
  return { send: (value: unknown) => peer!.send(JSON.stringify(value)), close: () => peer!.close({ code: 1011 }), authFrames, handled, refreshes: () => refreshes };
}
async function shot(page: Page, name: string) { await page.evaluate(() => document.fonts.ready); await page.screenshot({ path: `${screens}/${name}.png`, fullPage: true, mask: [page.locator('.alert-snapshot')] }); }

test('W10: event/alert cùng id chỉ một dòng; auth không ở URL; xử lý không thêm hồ sơ', async ({ page }) => {
  const state = await setup(page); state.send({ type: 'event', ...event }); state.send({ type: 'alert', ...event });
  await expect(page.locator(`[data-event-id="${event.id}"]`)).toHaveCount(1); await expect(page.locator(`[data-alert-id="${event.id}"]`)).toHaveCount(1);
  expect(state.authFrames[0]).toEqual({ type: 'auth', access_token: 'review-access' }); await shot(page, 'W10-fixture-realtime');
  await page.getByRole('button', { name: 'Xử lý', exact: true }).click(); await expect(page.getByText('Không thêm ảnh này vào hồ sơ khuôn mặt.', { exact: true })).toBeVisible();
  await page.getByRole('combobox', { name: /Kết quả xử lý/ }).press('ArrowDown'); await page.locator('.ant-select-dropdown:visible').getByText('Là nhân viên', { exact: true }).click();
  await page.getByRole('button', { name: 'Lưu xử lý', exact: true }).click(); await expect(page.getByText('Chọn nhân viên', { exact: true }).last()).toBeVisible(); expect(state.handled).toHaveLength(0);
});

test('HR: không có xử lý/mở cửa; snapshot 404 và banner mất WS', async ({ page }) => {
  const state = await setup(page, 'HR'); state.send({ type: 'event', ...event, has_snapshot: true });
  await expect(page.getByText('Ảnh không còn', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Xử lý', exact: true })).toHaveCount(0); await expect(page.getByRole('button', { name: 'Mở cửa mô phỏng', exact: true })).toHaveCount(0);
  state.close(); await expect(page.getByText('Mất kết nối thời gian thực — đang nối lại', { exact: true })).toBeVisible();
});

test('TOKEN_EXPIRED: làm mới rồi xác thực socket mới bằng token mới', async ({ page }) => {
  const state = await setup(page); state.send({ type: 'error', code: 'TOKEN_EXPIRED' });
  await expect.poll(state.refreshes).toBe(1); await expect.poll(() => state.authFrames.length).toBe(2);
  expect(state.authFrames[1]?.access_token).toBe('review-renewed');
});

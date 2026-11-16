import { test, expect } from '@playwright/test';
import { fillLogin, token } from './fixtures';
import type { components } from '../src/api/schema';
const settings: components['schemas']['RecognitionSettings'] = { window_size: 5, match_min: 3, unknown_min: 4, spoof_min: 3, lost_face_sec: 1, iou_reset: .3, cooldown_employee_sec: 60, cooldown_alert_sec: 15, result_display_sec: 3, max_fps: 4, frame_long_side: 640, jpeg_quality: 80, min_face_px: 80, max_abs_yaw_ratio: .35, anti_spoof_enabled: false, liveness_threshold: null, attendance_window_before_h: 3, attendance_window_after_h: 4, min_checkout_after_checkin_min: 30, forgot_out_before_end_h: 2 };
for (const role of ['OWNER', 'HR'] as const) test(`${role}: cấu hình chống giả mạo giữ cổng phê duyệt server`, async ({ page }) => {
  const writes: unknown[] = [];
  await page.routeWebSocket('**/api/v1/ws/monitor', socket => socket.onMessage(() => {}));
  await page.route('**/api/v1/**', route => {
    const request = route.request(), path = new URL(request.url()).pathname;
    if (path.endsWith('/auth/login')) return route.fulfill({ json: token(role, false) });
    if (path.endsWith('/settings/recognition')) {
      if (request.method() === 'GET') return route.fulfill({ json: settings });
      writes.push(request.postDataJSON()); return route.fulfill({ status: 422, json: { error: { code: 'VALIDATION_ERROR', message: 'Chống giả mạo chưa được hiệu chỉnh và chốt L.' } } });
    }
    if (path.endsWith('/models/active')) return route.fulfill({ status: 404, json: { error: { code: 'HTTP_404', message: 'Không có mô hình fixture' } } });
    if (path.endsWith('/health')) return route.fulfill({ json: { status: 'ok', db: true, gpu: false, model_verified: true, gallery_size: 1, version: 'fixture' } });
    if (path.endsWith('/dashboard/today')) return route.fulfill({ json: { date: '2026-11-16', present: 0, late: 0, not_arrived: 0, strangers: 0 } });
    return route.fulfill({ json: { items: [], total: 0, page: 1, size: 10 } });
  });
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page).toHaveURL(/\/admin$/);
  await page.evaluate(() => { history.pushState({}, '', '/admin/settings'); window.dispatchEvent(new PopStateEvent('popstate')); });
  const level = page.getByLabel('Ngưỡng L', { exact: true });
  if (role === 'HR') { await expect(level).toBeDisabled(); await expect(page.getByRole('button', { name: 'Lưu cấu hình', exact: true })).toHaveCount(0); return; }
  await expect(level).toBeEnabled(); await level.fill('0.7'); await page.getByRole('switch', { name: 'Bật chống giả mạo', exact: true }).click();
  await page.getByRole('button', { name: 'Lưu cấu hình', exact: true }).click(); await page.getByRole('button', { name: 'Xác nhận lưu', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('Chống giả mạo chưa được hiệu chỉnh và chốt L.'); expect(writes).toHaveLength(1); expect(writes[0]).toMatchObject({ anti_spoof_enabled: true, liveness_threshold: .7 }); await expect(level).toHaveValue('0.70');
});

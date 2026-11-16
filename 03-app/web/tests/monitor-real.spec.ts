// kiosk_sim dùng U03/U04 được đồng ý; ảnh/embedding nằm ngoài Git. Không giả event.
import { test, expect, type Page } from '@playwright/test';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const exec = promisify(execFile);
const root = fileURLToPath(new URL('../../../', import.meta.url));
const report = fileURLToPath(new URL('../../ket-qua-kiem-thu/2026-11-16_T11/', import.meta.url));
async function route(page: Page, path: string) { await page.evaluate(path => { history.pushState({}, '', path); window.dispatchEvent(new PopStateEvent('popstate')); }, path); }
async function shot(page: Page, name: string) {
  await page.evaluate(() => document.fonts.ready);
  const privacy = await page.addStyleTag({ content: '.alert-snapshot { visibility: hidden !important; }' });
  await page.screenshot({ path: `${report}/screens/${name}.png`, fullPage: true, mask: [page.locator('.alert-snapshot')] }); await privacy.evaluate(element => element.parentNode?.removeChild(element));
}
async function probe(kind: string, photos: string) {
  const result = await exec(`${root}/03-app/hub/.venv/Scripts/python.exe`, [`${root}/03-app/hub/scripts/probe_t11_realtime.py`, kind, photos], { cwd: root, encoding: 'utf8', env: { ...process.env, PYTHONUTF8: '1' }, timeout: 70000 });
  writeFileSync(`${report}/kiosk-${kind}.log`, result.stdout + result.stderr); expect(result.stdout).toContain(`PASS actual kiosk_sim ${kind}`);
}

test('Quét thật từ ảnh → W10 realtime, INACTIVE bị chặn, xử lý không đổi gallery, CSV', async ({ page }) => {
  const received = new Map<string, { received_ms: number; result: string }>();
  page.on('websocket', socket => { if (socket.url().endsWith('/api/v1/ws/monitor')) socket.on('framereceived', frame => { try { const value = JSON.parse(String(frame.payload)); if (value.type === 'event') received.set(value.id, { received_ms: Date.now(), result: value.result }); } catch { /* Chỉ đo Event JSON hợp lệ. */ } }); });
  await page.goto('/login'); await page.getByLabel('Email', { exact: true }).fill('nv001@demo.local'); await page.getByLabel('Mật khẩu', { exact: true }).fill('Demo@123'); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click(); await page.getByRole('button', { name: 'Trang quản trị', exact: true }).click(); await route(page, '/admin/monitor');
  await expect(page.getByRole('heading', { name: 'Sự kiện mới nhất', exact: true })).toBeVisible();
  const actor = await page.request.post('/api/v1/auth/login', { data: { email: 'nv001@demo.local', password: 'Demo@123' } }); const headers = { Authorization: `Bearer ${(await actor.json()).access_token}` };
  const employee = (await (await page.request.get('/api/v1/employees?q=NV006', { headers })).json()).items.find((row: { code: string }) => row.code === 'NV006');
  const profiles = async () => (await (await page.request.get(`/api/v1/face-profiles?employee_id=${employee.id}`, { headers })).json()).items.reduce((count: number, row: { samples: unknown[] }) => count + row.samples.length, 0);
  const samplesBefore = await profiles(); const galleryBefore = (await (await page.request.get('/api/v1/health')).json()).gallery_size;
  expect(samplesBefore).toBeGreaterThanOrEqual(5); expect(galleryBefore).toBeGreaterThanOrEqual(1);
  await probe('known', 'D:/WorkSpace/DATN/U03');
  await expect.poll(() => [...received.values()].some(row => row.result === 'MATCH')).toBe(true);
  await probe('unknown', 'D:/WorkSpace/DATN/U04');
  await expect.poll(() => [...received.values()].some(row => row.result === 'UNKNOWN')).toBe(true); await shot(page, 'W10-real-camera-alert-masked');
  const unknown = [...received].find(([, value]) => value.result === 'UNKNOWN')![0];
  const card = page.locator(`[data-alert-id="${unknown}"]`); await card.getByRole('button', { name: 'Xử lý', exact: true }).click();
  await page.getByRole('combobox', { name: /Kết quả xử lý/ }).press('ArrowDown'); await page.locator('.ant-select-dropdown:visible').getByText('Là nhân viên', { exact: true }).click();
  await page.getByRole('combobox', { name: /Nhân viên được xác nhận/ }).fill('NV006'); await page.locator('.ant-select-dropdown:visible').getByText('NV006 · Võ Thanh Tùng', { exact: true }).click(); await page.getByRole('button', { name: 'Lưu xử lý', exact: true }).click();
  await expect(page.getByText('Đã lưu xử lý cảnh báo', { exact: true })).toBeVisible();
  expect(await profiles()).toBe(samplesBefore); expect((await (await page.request.get('/api/v1/health')).json()).gallery_size).toBe(galleryBefore);
  await probe('suspended', 'D:/WorkSpace/DATN/U03'); await expect.poll(() => [...received.values()].some(row => row.result === 'DENIED_INACTIVE')).toBe(true);
  const commits = new Map<string, number>();
  for (const match of readFileSync(`${report}/hub-review.log`, 'utf8').matchAll(/MONITOR_COMMIT (\{[^\r\n]+\})/g)) { const row = JSON.parse(match[1]!); commits.set(row.event_id, row.commit_observed_ms); }
  const timings = [...received].filter(([id]) => commits.has(id)).map(([id, row]) => ({ event_id: id, result: row.result, commit_observed_ms: commits.get(id)!, web_received_ms: row.received_ms, latency_ms: row.received_ms - commits.get(id)! }));
  expect(timings.length).toBeGreaterThanOrEqual(3); for (const value of timings) expect(value.latency_ms).toBeLessThanOrEqual(1000);
  writeFileSync(`${report}/realtime-latency.json`, JSON.stringify({ source: 'kiosk_sim authorized real photos U03/U04, actual CPU Hub with approved T08 gallery', timing_definition: 'server callback immediately after DB commit → browser WS frame received (same host clock, 1ms client resolution)', samples_before: samplesBefore, samples_after: await profiles(), gallery_size: galleryBefore, timings }, null, 2));
  await route(page, '/admin/events'); await expect(page.getByRole('cell', { name: 'NV006 · Võ Thanh Tùng', exact: true }).first()).toBeVisible();
  const downloaded = page.waitForEvent('download'); await page.getByRole('button', { name: 'Xuất CSV', exact: true }).click(); const file = await downloaded; await file.saveAs(`${report}/su-kien.csv`);
  expect(readFileSync(`${report}/su-kien.csv`).subarray(0, 3)).toEqual(Buffer.from([239, 187, 191])); await shot(page, 'W11-real-events');
});

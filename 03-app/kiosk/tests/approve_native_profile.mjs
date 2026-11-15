// Duyệt hồ sơ Kiosk thật qua UI web; không chèn hồ sơ hoặc vector vào DB.
import { createRequire } from 'node:module';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
const require = createRequire(new URL('../../web/package.json', import.meta.url));
const { chromium } = require('@playwright/test');
const report = fileURLToPath(new URL('../../ket-qua-kiem-thu/2026-11-15_T08/', import.meta.url));
await mkdir(`${report}/screens`, { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.goto('http://127.0.0.1:5173/login');
  await page.getByLabel('Email', { exact: true }).fill('nv001@demo.local');
  await page.getByLabel('Mật khẩu', { exact: true }).fill('Demo@123');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await page.getByRole('button', { name: 'Trang quản trị', exact: true }).click();
  await page.evaluate(() => { history.pushState({}, '', '/admin/faces'); window.dispatchEvent(new PopStateEvent('popstate')); });
  await page.getByAltText('Ảnh mẫu đăng ký khuôn mặt').first().waitFor();
  const count = await page.getByAltText('Ảnh mẫu đăng ký khuôn mặt').count();
  if (count !== 5) throw new Error(`Cần đúng 5 mẫu thật, nhận được ${count}.`);
  await page.getByText('Võ Thanh Tùng', { exact: true }).first().waitFor();
  await page.screenshot({ path: `${report}/screens/W08-native-pending-masked.png`, fullPage: true, mask: [page.locator('.face-grid img')] });
  const response = page.waitForResponse(value => /\/face-profiles\/[^/]+\/approve$/.test(value.url()) && value.request().method() === 'POST');
  await page.getByRole('button', { name: 'Xác nhận', exact: true }).click();
  if ((await response).status() !== 200) throw new Error('Duyệt hồ sơ không thành công.');
  await page.getByText('Không có hồ sơ chờ xác nhận').waitFor();
  const health = await (await page.request.get('http://127.0.0.1:5173/api/v1/health')).json();
  if (health.gallery_size !== 1) throw new Error('Gallery chưa cập nhật.');
  await page.screenshot({ path: `${report}/screens/W08-native-approved.png`, fullPage: true });
  await writeFile(`${report}/native-web-approval.json`, JSON.stringify({ at: new Date().toISOString(), source: 'native Android camera replay → real Hub → web UI', employee: 'NV006', samples: count, approval_status: 200, gallery_size: health.gallery_size }, null, 2));
  console.log('PASS: 5 mẫu Kiosk thật, web duyệt 200, gallery_size=1.');
} finally { await browser.close(); }

import { test, expect, type Page } from '@playwright/test';
import { employeeApi, managerScope, seedDepartments, seedEmployees } from './employee-fixtures';
import { fillLogin } from './fixtures';
const screens = '../ket-qua-kiem-thu/2026-11-15_T07/screens';
async function openEmployees(page: Page) {
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await page.getByRole('navigation', { name: 'Điều hướng quản trị', exact: true }).getByRole('link', { name: 'Nhân viên', exact: true }).click();
  await expect(page.getByRole('table')).toBeVisible();
  await expect(page.getByText('NV001', { exact: true })).toBeVisible();
}
async function menu(page: Page, code: string, label: string) {
  await page.getByRole('button', { name: `Thao tác ${code}`, exact: true }).click();
  await page.getByRole('menuitem', { name: label, exact: true }).click();
}
async function newEmployee(page: Page, code = 'REVIEW025') {
  await page.getByRole('button', { name: 'Thêm nhân viên', exact: true }).click();
  await page.getByLabel('Mã nhân viên', { exact: true }).fill(code);
  await page.getByLabel('Họ và tên', { exact: true }).fill('Nhân viên review');
  await page.getByLabel('Phòng ban', { exact: true }).click();
  await page.getByText(seedDepartments[0]!.name, { exact: true }).last().click();
}

test('W-03: 24 nhân viên từ seed, 20/trang, ngày và trạng thái tiếng Việt', async ({ page }) => {
  const state = await employeeApi(page); await openEmployees(page);
  await expect(page.getByText('1–20 / 24 nhân viên')).toBeVisible();
  await expect(page.getByRole('table').getByText('Chưa đăng ký').first()).toBeVisible();
  await expect(page.getByRole('table').getByText('05/01/2026').first()).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  await page.mouse.move(700, 60);
  await expect(page.getByRole('tooltip')).toHaveCount(0);
  await page.screenshot({ path: `${screens}/employees-desktop.png`, fullPage: true });
  await page.getByTitle('2', { exact: true }).click();
  await expect(page.getByText('21–24 / 24 nhân viên')).toBeVisible();
  await expect(page.getByText('NV024', { exact: true })).toBeVisible();
  expect(state.requests.some(request => request.url.includes('page=2') && request.url.includes('size=20'))).toBeTruthy();
});

test('Tìm kiếm và kết hợp bộ lọc gửi đúng hợp đồng, đổi lọc về trang 1', async ({ page }) => {
  const state = await employeeApi(page); await openEmployees(page);
  await page.getByTitle('2', { exact: true }).click(); await expect(page.getByText('NV024', { exact: true })).toBeVisible();
  await page.getByRole('combobox', { name: 'Lọc trạng thái', exact: true }).click();
  await page.getByText('Tạm khoá', { exact: true }).last().click();
  await expect(page.getByText('1–1 / 1 nhân viên')).toBeVisible();
  await expect(page.getByText('NV019', { exact: true })).toBeVisible();
  const search = page.getByRole('searchbox', { name: 'Tìm nhân viên theo tên hoặc mã' });
  await search.fill('KHONG_TON_TAI'); await expect(page.getByText('Không tìm thấy nhân viên phù hợp')).toBeVisible();
  expect(state.requests.some(request => request.url.includes('status=SUSPENDED') && request.url.includes('page=1') && request.url.includes('q=KHONG_TON_TAI'))).toBeTruthy();
  await page.getByRole('button', { name: 'Xóa bộ lọc' }).click(); await expect(page.getByText('1–20 / 24 nhân viên')).toBeVisible();
  await page.getByRole('combobox', { name: 'Lọc phương thức', exact: true }).click();
  await page.getByText('Chấm công hộ', { exact: true }).last().click();
  await expect(page.getByText('NV022', { exact: true })).toBeVisible();
  await expect(page.getByText('1–1 / 1 nhân viên')).toBeVisible();
});

test('Phòng ban và hồ sơ khuôn mặt lọc tại API; không giả hồ sơ ACTIVE', async ({ page }) => {
  const state = await employeeApi(page); await openEmployees(page);
  await page.getByRole('combobox', { name: 'Lọc phòng ban', exact: true }).click();
  await page.getByText(seedDepartments[0]!.name, { exact: true }).last().click();
  await expect(page.getByText('1–1 / 1 nhân viên')).toBeVisible();
  await page.getByRole('combobox', { name: 'Lọc hồ sơ khuôn mặt', exact: true }).click();
  await page.getByText('Đang dùng', { exact: true }).last().click();
  await expect(page.getByText('Không tìm thấy nhân viên phù hợp')).toBeVisible();
  expect(state.requests.some(request => request.url.includes(`department_id=${seedDepartments[0]!.id}`) && request.url.includes('face_profile_status=ACTIVE'))).toBeTruthy();
});

test('Thêm: validation, trùng mã giữ form, tạo tài khoản/mật khẩu tạm một lần', async ({ page }) => {
  const state = await employeeApi(page); await openEmployees(page);
  await page.getByRole('button', { name: 'Thêm nhân viên', exact: true }).click();
  await page.getByRole('button', { name: 'Lưu nhân viên', exact: true }).click();
  await expect(page.getByText('Vui lòng nhập mã nhân viên')).toBeVisible();
  await expect(page.getByText('Vui lòng nhập họ và tên')).toBeVisible();
  await page.getByRole('button', { name: 'Hủy', exact: true }).click();
  await newEmployee(page, 'NV001'); await page.getByRole('button', { name: 'Lưu nhân viên', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Mã nhân viên đã tồn tại');
  await expect(page.getByLabel('Họ và tên', { exact: true })).toHaveValue('Nhân viên review');
  await page.getByLabel('Mã nhân viên', { exact: true }).fill('REVIEW025');
  await page.getByRole('checkbox', { name: 'Tạo tài khoản đăng nhập' }).check();
  await page.getByRole('button', { name: 'Lưu nhân viên', exact: true }).click();
  await expect(page.getByText('Cần email để tạo tài khoản đăng nhập')).toBeVisible();
  await page.getByLabel('Email', { exact: true }).fill('review025@example.test');
  await page.screenshot({ path: `${screens}/employee-create.png` });
  await page.getByRole('button', { name: 'Lưu nhân viên', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Tài khoản đã được tạo' })).toBeVisible();
  await expect(page.getByText('ReviewTemp123!', { exact: true })).toBeVisible();
  const body = state.requests.filter(item => item.method === 'POST' && item.url === '/api/v1/employees').at(-1)!.body;
  expect(body).toMatchObject({ code: 'REVIEW025', email: 'review025@example.test', create_account: true });
  await page.getByRole('button', { name: 'Đã lưu mật khẩu' }).click();
  await expect(page.getByText('ReviewTemp123!', { exact: true })).not.toBeVisible();
});

test('Sửa: mã khóa và PATCH không chứa code/trạng thái', async ({ page }) => {
  const state = await employeeApi(page); await openEmployees(page); await menu(page, 'NV001', 'Sửa');
  await expect(page.getByLabel('Mã nhân viên', { exact: true })).toBeDisabled();
  await page.getByLabel('Họ và tên', { exact: true }).fill('Tên đã sửa để review');
  await page.getByRole('button', { name: 'Lưu nhân viên', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Tên đã sửa để review' })).toBeVisible();
  const body = state.requests.find(item => item.method === 'PATCH')!.body;
  expect(body).toMatchObject({ full_name: 'Tên đã sửa để review' }); expect(body).not.toHaveProperty('code'); expect(body).not.toHaveProperty('status');
  expect(body).toMatchObject({ joined_at: '2026-01-05' });
});

test('Tạm khóa/mở khóa: không gửi thao tác xóa khuôn mặt', async ({ page }) => {
  const state = await employeeApi(page); await openEmployees(page);
  await menu(page, 'NV001', 'Tạm khóa'); await expect(page.getByRole('status').filter({ hasText: 'Đã tạm khóa nhân viên' })).toBeVisible();
  await menu(page, 'NV001', 'Mở khóa'); await expect(page.getByRole('status').filter({ hasText: 'Đã mở khóa nhân viên' })).toBeVisible();
  expect(state.employees[0]!.status).toBe('ACTIVE'); expect(state.requests.some(item => item.method === 'DELETE')).toBeFalsy();
});

test('Nghỉ việc: hủy không gửi; lỗi 503 giữ hộp thoại; thử lại mới báo thành công', async ({ page }) => {
  const state = await employeeApi(page); await openEmployees(page); await menu(page, 'NV001', 'Nghỉ việc');
  await expect(page.getByText(/Toàn bộ ảnh mẫu và đặc trưng khuôn mặt sẽ bị xoá ngay/)).toBeVisible();
  await page.getByRole('button', { name: 'Hủy', exact: true }).click();
  expect(state.requests.some(item => item.url.endsWith('/terminate'))).toBeFalsy();
  state.terminateFailures = 1;
  await menu(page, 'NV001', 'Nghỉ việc'); await page.getByRole('button', { name: 'Xác nhận nghỉ việc', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Xác nhận nghỉ việc' })).toBeVisible();
  await expect(page.getByRole('alert')).toContainText('Thao tác chưa hoàn tất');
  expect(state.employees[0]!.status).toBe('ACTIVE');
  await page.screenshot({ path: `${screens}/employee-terminate-error.png` });
  await page.getByRole('button', { name: 'Xác nhận nghỉ việc', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Xác nhận nghỉ việc' })).not.toBeVisible();
  await expect(page.getByRole('status').filter({ hasText: 'Đã chuyển nhân viên sang nghỉ việc' })).toBeVisible();
  expect(state.employees[0]!.status).toBe('TERMINATED');
});

test('MANAGER: chỉ đọc team, không có nút thêm/menu ghi', async ({ page }) => {
  const state = await employeeApi(page, 'MANAGER');
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await page.getByRole('navigation', { name: 'Điều hướng quản trị', exact: true }).getByRole('link', { name: 'Nhân viên', exact: true }).click();
  const count = seedEmployees.filter(employee => employee.department_id === managerScope).length;
  await expect(page.getByText(`1–${count} / ${count} nhân viên`)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Thêm nhân viên', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: /^Thao tác NV/ })).toHaveCount(0);
  await expect(page.getByText('NV001', { exact: true })).toHaveCount(0);
  expect(state.requests.some(item => item.method !== 'GET' && !item.url.endsWith('/auth/login'))).toBeFalsy();
  await page.screenshot({ path: `${screens}/employees-manager.png`, fullPage: true });
});

test('Lỗi danh sách: thử lại; 403 không hiển thị bảng cũ', async ({ page }) => {
  const state = await employeeApi(page); await openEmployees(page);
  state.listError = 503; await page.getByRole('button', { name: 'Làm mới', exact: true }).click();
  await expect(page.getByText('Không tải được danh sách nhân viên', { exact: true })).toBeVisible();
  await expect(page.getByRole('table')).toHaveCount(0);
  state.listError = 0; await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
  await expect(page.getByText('NV001', { exact: true })).toBeVisible();
  state.listError = 403; await page.getByRole('button', { name: 'Làm mới', exact: true }).click();
  await expect(page.getByText('Bạn không có quyền xem trang này')).toBeVisible();
  await expect(page.getByRole('table')).toHaveCount(0);
});

test('Dưới 1024px: Drawer điều hướng và bảng cuộn trong panel', async ({ page }) => {
  await employeeApi(page); await openEmployees(page); await page.setViewportSize({ width: 800, height: 900 });
  await expect(page.getByRole('button', { name: 'Mở điều hướng' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.getByRole('button', { name: 'Mở điều hướng' }).click();
  await expect(page.getByRole('dialog', { name: 'FaceGate · Quản trị' })).toBeVisible();
  await page.screenshot({ path: `${screens}/employees-navigation-tablet.png`, fullPage: true });
});

test('Đang lưu: chặn gửi lặp và đóng Drawer', async ({ page }) => {
  const state = await employeeApi(page); state.mutationDelay = 800;
  await openEmployees(page); await newEmployee(page);
  await page.getByRole('button', { name: 'Lưu nhân viên', exact: true }).click();
  await expect(page.getByLabel('Họ và tên', { exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Hủy', exact: true })).toBeDisabled();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('status').filter({ hasText: 'Đã thêm nhân viên' })).toBeVisible();
  expect(state.requests.filter(item => item.method === 'POST' && item.url === '/api/v1/employees')).toHaveLength(1);
});

test('SECURITY: ẩn menu nhân viên và chặn URL trực tiếp trước khi gọi API', async ({ page }) => {
  const state = await employeeApi(page, 'SECURITY');
  await page.goto('/login'); await fillLogin(page); await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByRole('navigation', { name: 'Điều hướng quản trị', exact: true }).getByRole('link', { name: 'Nhân viên', exact: true })).toHaveCount(0);
  await page.evaluate(() => { history.pushState({}, '', '/admin/employees'); dispatchEvent(new PopStateEvent('popstate')); });
  await expect(page.getByText('Bạn không có quyền xem trang này')).toBeVisible();
  expect(state.requests.some(item => item.url.startsWith('/api/v1/employees'))).toBeFalsy();
});

test('Danh sách trống: trạng thái riêng và vẫn có hành động thêm', async ({ page }) => {
  await employeeApi(page); await page.goto('/login'); await fillLogin(page, 'empty@example.test');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await page.getByRole('navigation', { name: 'Điều hướng quản trị', exact: true }).getByRole('link', { name: 'Nhân viên', exact: true }).click();
  await expect(page.getByText('Chưa có nhân viên', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Thêm nhân viên', exact: true })).toBeVisible();
  await page.screenshot({ path: `${screens}/employees-empty.png` });
});

test('HR: có thao tác ghi, không có Nhật ký chỉ dành OWNER', async ({ page }) => {
  await employeeApi(page, 'HR'); await openEmployees(page);
  await expect(page.getByRole('button', { name: 'Thêm nhân viên', exact: true })).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Điều hướng quản trị', exact: true }).getByRole('link', { name: 'Nhật ký', exact: true })).toHaveCount(0);
});

import { readFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import type { Page } from '@playwright/test';
import type { components } from '../src/api/schema';
import { token } from './fixtures';

// Dữ liệu danh sách đọc từ seed.sql; không ghi DB và không tạo dữ liệu sinh trắc/công/event.
const sql = readFileSync(new URL('../../db/seed.sql', import.meta.url), 'utf8');
const rows = (table: string) => [...sql.matchAll(new RegExp(`INSERT INTO ${table}\\([^\\n]+?\\) VALUES \\(([^\\n]+)\\);`, 'g'))].map(match => [...match[1]!.matchAll(/'(?:''|[^'])*'|NULL|true|false/g)].map(item => item[0].startsWith("'") ? item[0].slice(1, -1).replaceAll("''", "'") : item[0]));
export const seedDepartments: components['schemas']['Department'][] = rows('department').map(row => ({ id: row[0]!, name: row[2]! }));
export const managerScope = rows('user_role').find(row => row[1] === 'MANAGER')![2]!;
export const seedEmployees: components['schemas']['Employee'][] = rows('employee').map(row => ({
  id: row[0]!, department_id: row[2]!, department_name: seedDepartments.find(item => item.id === row[2])!.name,
  code: row[3]!, full_name: row[4]!, email: row[5]!, status: row[6] as components['schemas']['EmployeeStatus'],
  attendance_method: row[7] as components['schemas']['AttendanceMethod'], joined_at: row[8]!, face_profile_status: null,
}));

export async function employeeApi(page: Page, role: components['schemas']['Role'] = 'OWNER') {
  const state = {
    employees: structuredClone(seedEmployees), role, listError: 0, terminateFailures: 0, mutationDelay: 0,
    listFailures: 0, emptyMode: false,
    requests: [] as { method: string; url: string; body: unknown }[],
  };
  await page.route('**/api/v1/**', async route => {
    const request = route.request(); const url = new URL(request.url());
    const path = url.pathname.replace('/api/v1', ''); const method = request.method();
    const body = request.postData() ? request.postDataJSON() : null;
    state.requests.push({ method, url: url.pathname + url.search, body });
    const fail = (status: number, message: string) => route.fulfill({ status, json: { error: { code: status === 503 ? 'BIOMETRIC_DELETE_INCOMPLETE' : 'REVIEW_ERROR', message } } });
    if (path === '/auth/login') {
      const roles: Record<string, components['schemas']['Role']> = { 'admin@example.test': 'OWNER', 'hr@example.test': 'HR', 'manager@example.test': 'MANAGER', 'security@example.test': 'SECURITY', 'employee@example.test': 'EMPLOYEE', 'error@example.test': 'OWNER', 'empty@example.test': 'OWNER', 'delete-error@example.test': 'OWNER' };
      state.role = roles[body.email] ?? state.role;
      state.listFailures = body.email === 'error@example.test' ? 1 : 0;
      state.emptyMode = body.email === 'empty@example.test';
      state.terminateFailures = body.email === 'delete-error@example.test' ? 1 : state.terminateFailures;
      if (body.password !== 'Review123!') return fail(401, 'Email hoặc mật khẩu không đúng');
      const session = token(state.role, false);
      if (state.role === 'MANAGER') session.user.roles[0]!.scope_department_id = managerScope;
      if (state.role === 'EMPLOYEE') session.user.employee = { id: seedEmployees[0]!.id, code: seedEmployees[0]!.code, full_name: seedEmployees[0]!.full_name };
      return route.fulfill({ json: session });
    }
    if (path === '/auth/logout' || path === '/auth/change-password') return route.fulfill({ status: 204 });
    if (path === '/health') return route.fulfill({ json: { status: 'degraded', db: true, gpu: false, model_verified: false, gallery_size: 0, version: 'review' } satisfies components['schemas']['Health'] });
    if (request.headers().authorization !== 'Bearer review-access') return fail(401, 'Phiên đăng nhập đã hết hạn');
    if (path === '/departments') return route.fulfill({ json: seedDepartments });
    if (!['OWNER', 'HR', 'MANAGER'].includes(state.role)) return fail(403, 'Bạn không có quyền xem nhân viên');
    if (path === '/employees' && method === 'GET') {
      if (state.listFailures > 0) { state.listFailures--; return fail(503, 'Không tải được danh sách. Vui lòng thử lại.'); }
      if (state.listError) return fail(state.listError, 'Không tải được danh sách. Vui lòng thử lại.');
      const query = url.searchParams;
      let list = state.emptyMode ? [] : state.employees.filter(employee => state.role !== 'MANAGER' || employee.department_id === managerScope);
      const term = query.get('q')?.toLocaleLowerCase('vi');
      if (term) list = list.filter(employee => `${employee.full_name} ${employee.code}`.toLocaleLowerCase('vi').includes(term));
      for (const key of ['department_id', 'status', 'attendance_method', 'face_profile_status'] as const) if (query.get(key)) list = list.filter(employee => (employee[key] ?? 'NONE') === query.get(key));
      const pageNumber = Number(query.get('page') || 1); const size = Number(query.get('size') || 20);
      return route.fulfill({ json: { items: list.slice((pageNumber - 1) * size, pageNumber * size), total: list.length, page: pageNumber, size } satisfies components['schemas']['PageEmployee'] });
    }
    if (!['OWNER', 'HR'].includes(state.role)) return fail(403, 'Bạn không có quyền thay đổi hồ sơ');
    if (state.mutationDelay) await new Promise(resolve => setTimeout(resolve, state.mutationDelay));
    if (path === '/employees' && method === 'POST') {
      if (state.employees.some(employee => employee.code === body.code)) return fail(409, 'Mã nhân viên đã tồn tại');
      const employee: components['schemas']['Employee'] = { ...body, id: randomUUID(), department_name: seedDepartments.find(item => item.id === body.department_id)?.name, status: 'ACTIVE', attendance_method: 'FACE', face_profile_status: null };
      state.employees.push(employee);
      return route.fulfill({ status: 201, json: { employee, ...(body.create_account ? { temporary_password: 'ReviewTemp123!' } : {}) } satisfies components['schemas']['EmployeeCreated'] });
    }
    const parts = path.split('/'); const employee = state.employees.find(item => item.id === parts[2]);
    if (!employee) return fail(404, 'Không tìm thấy nhân viên');
    if (method === 'PATCH') { Object.assign(employee, body, { department_name: seedDepartments.find(item => item.id === body.department_id)?.name }); return route.fulfill({ json: employee }); }
    if (method === 'POST' && parts[3] === 'terminate' && state.terminateFailures > 0) { state.terminateFailures--; return fail(503, 'Thao tác chưa hoàn tất, vui lòng thử lại'); }
    if (method === 'POST' && ['suspend', 'reactivate', 'terminate'].includes(parts[3]!)) {
      employee.status = parts[3] === 'suspend' ? 'SUSPENDED' : parts[3] === 'reactivate' ? 'ACTIVE' : 'TERMINATED';
      return route.fulfill({ json: employee });
    }
    return fail(404, 'Ngoài phạm vi review nhân viên');
  });
  return state;
}

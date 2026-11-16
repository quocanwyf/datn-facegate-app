import { api } from '../../api/client';
import { readResult } from '../../api/result';
import type { components } from '../../api/schema';
export type Day = components['schemas']['AttendanceDay'];
export type Employee = components['schemas']['Employee'];
export async function allEmployees(signal?: AbortSignal) {
  const items: Employee[] = [];
  for (let page = 1; ; page++) {
    const result = readResult(await api.GET('/employees', { params: { query: { page, size: 100 } }, signal }));
    items.push(...result.items);
    if (items.length >= result.total || !result.items.length) return items;
  }
}
export async function allDays(from: string, to: string, department_id?: string, employee_id?: string, signal?: AbortSignal) {
  const items: Day[] = [];
  for (let page = 1; ; page++) {
    const result = readResult(await api.GET('/attendance/days', { params: { query: { from, to, department_id, employee_id, page, size: 100 } }, signal }));
    items.push(...result.items);
    if (items.length >= result.total || !result.items.length) return [...new Map(items.map(row => [`${row.employee.id}/${row.work_date}`, row])).values()];
  }
}
export const workStatuses = new Set(['NORMAL', 'LATE', 'EARLY', 'LATE_EARLY']);
export const dayMark: Record<Day['status'], string> = { NORMAL: 'Đ', LATE: 'M', EARLY: 'S', LATE_EARLY: 'MS', MISSING_OUT: 'T', ABSENT: 'V', LEAVE: 'P', HOLIDAY: 'L', OFF: '–', NOT_STARTED: '·', IN_PROGRESS: '…', WAITING_IN: 'C' };

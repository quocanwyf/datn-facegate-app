import { api } from '../api/client';
import { readResult } from '../api/result';
import type { components } from '../api/schema';
export type AttendanceRequest = components['schemas']['AttendanceRequest'];
export async function myRequests(status: components['schemas']['RequestStatus'], signal?: AbortSignal) {
  const items: AttendanceRequest[] = [];
  for (let page = 1; ; page++) {
    const result = readResult(await api.GET('/me/requests', { params: { query: { status, page, size: 100 } }, signal }));
    items.push(...result.items); if (items.length >= result.total || !result.items.length) return items;
  }
}
export async function teamRequests(signal?: AbortSignal) {
  const items: AttendanceRequest[] = [];
  for (let page = 1; ; page++) {
    const result = readResult(await api.GET('/attendance/requests', { params: { query: { status: 'PENDING', scope: 'team', page, size: 100 } }, signal }));
    items.push(...result.items); if (items.length >= result.total || !result.items.length) return items;
  }
}

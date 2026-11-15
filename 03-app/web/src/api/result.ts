import type { components } from './schema';
import { connectionError } from './client';
export class HttpError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
export function readResult<T>(result: { data?: T; error?: components['schemas']['Error']; response: Response }): T {
  if (!result.response.ok || result.data === undefined && result.response.status !== 204) throw new HttpError(result.response.status,
    result.response.status === 401 ? 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.' : result.error?.error.message || 'Không thể tải dữ liệu. Vui lòng thử lại.');
  return result.data as T;
}
export const requestMessage = (error: unknown) => error instanceof HttpError ? error.message : connectionError;

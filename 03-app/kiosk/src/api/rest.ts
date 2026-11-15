import type { components } from './schema';
export class ApiFailure extends Error {
  readonly code: string;
  constructor(message: string, code: string) { super(message); this.code = code; }
}
export function unwrap<T>(value: { data?: T; error?: components['schemas']['Error']; response: Response }): T {
  if (!value.response.ok) throw new ApiFailure(value.error?.error.message ?? 'Không thể hoàn tất yêu cầu. Vui lòng thử lại.', value.error?.error.code ?? '');
  return value.data as T;
}
export function failureMessage(error: unknown) { return error instanceof ApiFailure ? error.message : 'Không kết nối được Hub. Kiểm tra địa chỉ và Wi-Fi.'; }
export function hubAddress(value: string) {
  const url = new URL(value.trim());
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== '/') throw new Error('Địa chỉ Hub không hợp lệ');
  return url.origin;
}

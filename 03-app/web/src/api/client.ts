import createClient from 'openapi-fetch';
import type { components, paths } from './schema';

export type Session = components['schemas']['TokenPair'];
export type User = components['schemas']['UserMe'];
export const api = createClient<paths>({ baseUrl: '/api/v1' });
let accessToken: (() => string | undefined) = () => undefined;
export function configureAccessToken(provider: () => string | undefined) {
  accessToken = provider;
}
api.use({
  onRequest({ request }) {
    const token = accessToken();
    if (token) request.headers.set('Authorization', `Bearer ${token}`);
    return request;
  },
});
type ApiError = components['schemas']['Error'];

export function errorMessage(status: number, error: ApiError | undefined) {
  if (error?.error.message) return error.error.message;
  if (status === 401) return 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn.';
  if (status === 429) return 'Thử lại sau ít phút';
  return 'Không thể hoàn tất yêu cầu. Vui lòng thử lại.';
}
export const connectionError = 'Không thể kết nối Hub. Vui lòng kiểm tra kết nối và thử lại.';

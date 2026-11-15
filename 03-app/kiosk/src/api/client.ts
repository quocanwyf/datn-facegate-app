import createClient from 'openapi-fetch';
import type { components, paths } from './schema';

export function createKioskClient(
  hubUrl: string,
  getDeviceToken: () => Promise<string | null>,
) {
  const client = createClient<paths>({ baseUrl: `${hubUrl.replace(/\/+$/, '')}/api/v1` });
  client.use({
    async onRequest({ request }) {
      const token = await getDeviceToken();
      if (token) request.headers.set('Authorization', `Bearer ${token}`);
      return request;
    },
  });
  return client;
}

export function kioskErrorMessage(error: components['schemas']['Error'] | undefined) {
  return error?.error.message ?? 'Không thể hoàn tất yêu cầu. Vui lòng thử lại.';
}

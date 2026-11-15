import createClient from 'openapi-fetch';
import { fetch as expoFetch } from 'expo/fetch';
import type { components, paths } from './schema';

export function createKioskClient(
  hubUrl: string,
  getDeviceToken: () => Promise<string | null>,
) {
  const client = createClient<paths>({ baseUrl: `${hubUrl.replace(/\/+$/, '')}/api/v1`, fetch: async request => {
    const abort = new AbortController(); const cancel = () => abort.abort();
    if (request.signal.aborted) abort.abort();
    request.signal.addEventListener('abort', cancel, { once: true });
    const timeout = setTimeout(cancel, 15000);
    try { return await expoFetch(request, { signal: abort.signal }); }
    finally { clearTimeout(timeout); request.signal.removeEventListener('abort', cancel); }
  } });
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

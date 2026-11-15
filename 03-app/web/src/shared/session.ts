import type { components } from '../api/schema';
type Session = components['schemas']['TokenPair'];
let current: Session | null = null;
let expiresAt = 0;
let revision = 0;
let flight: Promise<string | undefined> | undefined;
const listeners = new Set<() => void>();
export const getSession = () => current;
export const subscribeSession = (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; };
export function setAuthSession(value: Session | null) {
  current = value; expiresAt = value ? Date.now() + value.expires_in * 1000 : 0; revision++;
  listeners.forEach(listener => listener());
}
export async function freshToken(force = false): Promise<string | undefined> {
  if (!current) return undefined;
  if (!force && Date.now() < expiresAt - 30000) return current.access_token;
  if (flight) return flight;
  const version = revision; const refresh = current.refresh_token;
  flight = (async () => {
    const response = await fetch('/api/v1/auth/refresh', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refresh }), signal: AbortSignal.timeout(15000) });
    if (version !== revision) return current?.access_token;
    if (!response.ok) { if (response.status === 401) setAuthSession(null); throw new Error('Không thể làm mới phiên đăng nhập'); }
    const pair: Session = await response.json(); setAuthSession(pair); return pair.access_token;
  })();
  try { return await flight; } finally { flight = undefined; }
}
export async function authenticatedFetch(request: Request): Promise<Response> {
  const protectedRoute = !/\/auth\/(login|refresh)$/.test(new URL(request.url).pathname);
  // Giữ body dạng buffer để có thể gửi lại đúng một lần, kể cả POST/PATCH.
  const body = request.body ? await request.arrayBuffer() : undefined;
  const send = () => fetch(request.url, { method: request.method, headers: request.headers, body, signal: request.signal, credentials: request.credentials, cache: request.cache, redirect: request.redirect });
  if (protectedRoute) { const token = await freshToken(); if (token) request.headers.set('Authorization', `Bearer ${token}`); }
  const response = await send();
  if (response.status !== 401 || !protectedRoute || !current) return response;
  // Các request đồng thời dùng chung một lần xoay refresh token.
  const used = request.headers.get('Authorization');
  const token = used !== `Bearer ${current.access_token}` ? current.access_token : await freshToken(true);
  if (!token) return response;
  request.headers.set('Authorization', `Bearer ${token}`); return send();
}

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Session } from '../../api/client';
import type { components } from '../../api/schema';
import { freshToken, getSession, setAuthSession } from '../../shared/session';

export type Event = components['schemas']['Event'];
type Counters = Pick<components['schemas']['Dashboard'], 'open_alerts' | 'pending_face_profiles' | 'pending_requests'>;
type State = { events: Event[]; status: 'connecting' | 'online' | 'offline'; counters?: Counters };
const Context = createContext<State>({ events: [], status: 'connecting' });
export const useMonitor = () => useContext(Context);

function isEvent(value: unknown): value is Event {
  if (!value || typeof value !== 'object') return false;
  const row = value as Record<string, unknown>;
  if (typeof row.id !== 'string' || typeof row.occurred_at !== 'string' || typeof row.result !== 'string' || typeof row.has_snapshot !== 'boolean' || !row.gate || typeof row.gate !== 'object') return false;
  const gate = row.gate as Record<string, unknown>;
  if (typeof gate.id !== 'string' || typeof gate.name !== 'string' || !['ATTENDANCE_ACCESS', 'ACCESS_ONLY'].includes(String(gate.mode)) || !['OPEN', 'NONE'].includes(String(row.door_action))) return false;
  if (!['MATCH', 'UNKNOWN', 'SPOOF', 'DENIED_RULE', 'DENIED_INACTIVE', 'MANUAL_OPEN', 'MANUAL_ATTENDANCE'].includes(row.result)) return false;
  if (row.employee != null) { if (typeof row.employee !== 'object') return false; const employee = row.employee as Record<string, unknown>; if (typeof employee.id !== 'string' || typeof employee.code !== 'string' || typeof employee.full_name !== 'string') return false; }
  return true;
}

export function MonitorProvider({ session, children }: { session: Session; children: ReactNode }) {
  const [events, setEvents] = useState<Event[]>([]); const [status, setStatus] = useState<State['status']>('connecting');
  const [counters, setCounters] = useState<Counters>(); const client = useQueryClient();
  useEffect(() => {
    let active = true, refused = false, attempt = 0, renew = false;
    let socket: WebSocket | undefined; let retry: ReturnType<typeof setTimeout> | undefined;
    const invalidate = (...keys: string[]) => keys.forEach(key => { void client.invalidateQueries({ queryKey: [key] }); });
    async function connect() {
      if (!active || refused) return;
      try {
        const token = await freshToken(renew); renew = false;
        if (!active || !token || getSession()?.user.id !== session.user.id) return;
        const current = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/api/v1/ws/monitor`);
        socket = current;
        current.onopen = () => { if (active && socket === current) { current.send(JSON.stringify({ type: 'auth', access_token: token })); attempt = 0; setEvents([]); setStatus('online'); invalidate('events', 'recent-events', 'monitor-alerts', 'dashboard', 'gates', 'devices'); } };
        current.onmessage = message => {
          if (!active || socket !== current) return;
          try {
            const value: unknown = JSON.parse(String(message.data));
            if (!value || typeof value !== 'object' || !('type' in value)) return;
            if ((value.type === 'event' || value.type === 'alert') && isEvent(value)) {
              const event = value;
              setEvents(previous => [event, ...previous.filter(row => row.id !== event.id)].slice(0, 60));
              if (value.type === 'event') invalidate('events', 'recent-events', 'monitor-alerts', 'dashboard');
            } else if (value.type === 'alert_handled' && 'event_id' in value && typeof value.event_id === 'string' && 'handling' in value) {
              const handling = value.handling as Event['handling'];
              setEvents(previous => previous.map(row => row.id === value.event_id ? { ...row, handling } : row));
              invalidate('events', 'monitor-alerts', 'dashboard');
            } else if (value.type === 'device_status') invalidate('gates', 'devices', 'dashboard');
            else if (value.type === 'counters') { setCounters(value as Counters); invalidate('dashboard'); }
            else if (value.type === 'error' && 'code' in value) {
              if (value.code === 'TOKEN_EXPIRED') { renew = true; current.close(); }
              else if (value.code === 'FORBIDDEN') { refused = true; setStatus('offline'); current.close(); }
              else if (value.code === 'TOKEN_INVALID' || value.code === 'UNAUTHORIZED') { refused = true; setAuthSession(null); current.close(); }
            }
          } catch { /* Không đưa thông điệp không hợp lệ vào giao diện. */ }
        };
        current.onerror = () => { if (active && socket === current) setStatus('offline'); };
        current.onclose = () => { if (!active || socket !== current) return; setStatus('offline'); if (!refused) retry = setTimeout(() => void connect(), Math.min(1000 * 2 ** attempt++, 15000)); };
      } catch { if (active) { setStatus('offline'); retry = setTimeout(() => void connect(), Math.min(1000 * 2 ** attempt++, 15000)); } }
    }
    void connect();
    return () => { active = false; clearTimeout(retry); socket?.close(); };
  }, [client, session.user.id]);
  return <Context.Provider value={{ events, status, counters }}>{children}</Context.Provider>;
}

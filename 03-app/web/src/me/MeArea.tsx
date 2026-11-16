import { useEffect, useRef, useState } from 'react';
import { Alert, Badge, Button, Dropdown } from 'antd';
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarDays, ClipboardCheck, FileText, Home, ScanFace } from 'lucide-react';
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import type { Session } from '../api/client';
import { canAdmin } from '../shared/access';
import { teamRequests } from './data';
import { TodayPage, MonthPage, DayPage, FacePage } from './Pages';
import { NewRequestPage, MyRequestsPage, TeamPage } from './Requests';
import './me.css';

export function MeArea(props: { session: Session; busy: boolean; error: string; onLogout: () => void }) {
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 10000, refetchOnWindowFocus: true } } }));
  return <QueryClientProvider client={client}><MeShell {...props} /></QueryClientProvider>;
}
function MeShell({ session, busy, error, onLogout }: { session: Session; busy: boolean; error: string; onLogout: () => void }) {
  const navigate = useNavigate(), location = useLocation(), client = useQueryClient(); const touch = useRef<number>();
  useEffect(() => { window.scrollTo(0, 0); }, [location.pathname]);
  const manager = session.user.roles.some(row => row.role === 'MANAGER');
  const team = useQuery({ queryKey: ['me-team'], queryFn: ({ signal }) => teamRequests(signal), enabled: manager });
  const count = team.data?.filter(row => row.can_review && row.employee.id !== session.user.employee?.id).length ?? 0;
  const items = [{ to: '/me', label: 'Hôm nay', icon: Home }, { to: '/me/attendance', label: 'Bảng công', icon: CalendarDays }, { to: '/me/requests', label: 'Giải trình', icon: FileText }, { to: '/me/face', label: 'Khuôn mặt', icon: ScanFace }, ...(manager ? [{ to: '/me/team', label: 'Duyệt', icon: ClipboardCheck }] : [])];
  const title = items.find(row => row.to !== '/me' && location.pathname.startsWith(row.to))?.label ?? (location.pathname.includes('/days/') ? 'Chi tiết ngày' : 'Hôm nay');
  return <div className="me-shell" onTouchStart={event => { touch.current = window.scrollY <= 0 ? event.touches[0]?.clientY : undefined; }} onTouchEnd={event => { if (touch.current !== undefined && (event.changedTouches[0]?.clientY ?? 0) - touch.current > 80) void client.invalidateQueries(); touch.current = undefined; }}>
    <header className="me-header"><h1>{title}</h1><Dropdown trigger={['click']} menu={{ items: [{ key: 'password', label: 'Đổi mật khẩu', onClick: () => navigate('/change-password') }, ...(canAdmin(session.user) ? [{ key: 'choose', label: 'Chọn không gian', onClick: () => navigate('/choose') }] : []), { key: 'logout', label: 'Đăng xuất', disabled: busy, onClick: onLogout }] }}><Button className="me-avatar" aria-label="Menu tài khoản" disabled={busy}>{session.user.employee?.full_name.split(' ').at(-1)?.slice(0, 1)}</Button></Dropdown></header>
    <main className="me-content">{error && <Alert role="alert" type="error" message={error} />}<Routes>
      <Route path="/me" element={<TodayPage session={session} />} /><Route path="/me/attendance" element={<MonthPage />} /><Route path="/me/days/:date" element={<DayPage />} /><Route path="/me/requests" element={<MyRequestsPage />} /><Route path="/me/requests/new" element={<NewRequestPage />} /><Route path="/me/face" element={<FacePage />} /><Route path="/me/team" element={manager ? <TeamPage session={session} /> : <Navigate to="/me" replace />} /><Route path="*" element={<Navigate to="/me" replace />} />
    </Routes></main>
    <nav className="me-bottom" aria-label="Điều hướng cá nhân">{items.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} aria-label={label} end={to === '/me'}><Badge count={to === '/me/team' ? count : 0} size="small"><Icon size={21} aria-hidden="true" /></Badge><span>{label}</span></NavLink>)}</nav>
  </div>;
}

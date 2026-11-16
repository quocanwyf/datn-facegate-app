import { useRef, useState } from 'react';
import { Alert, Avatar, Button, Drawer, Dropdown, Result, Tooltip } from 'antd';
import { Bell, Building2, CalendarDays, ClipboardList, DoorOpen, FileClock, Fingerprint, LayoutDashboard, LogOut, Menu, ScanFace, ScrollText, Settings2, ShieldCheck, Users } from 'lucide-react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { api, type Session } from '../api/client';
import { readResult } from '../api/result';
import { EmployeesPage } from './employees/EmployeesPage';
import { statusInfo } from '../theme/status';
import { PageHero } from '../components/PageHero';
import { FacesPage } from './face-review/FacesPage';
import { EmployeeDetail } from './employees/EmployeeDetail';
import { OrganizationPage } from './organization/OrganizationPage';
import { GatesPage } from './gates/GatesPage';
import { SettingsPage } from './settings/SettingsPage';
import { AuditPage } from './audit/AuditPage';
import { DashboardPage } from './dashboard/DashboardPage';
import { SchedulesPage } from './schedules/SchedulesPage';
import { AttendancePage } from './attendance/AttendancePage';
import { RequestsPage } from './attendance/RequestsPage';
import '../admin.css';

gsap.registerPlugin(useGSAP);
const entries = [
  { path: '/admin', label: 'Tổng quan', icon: LayoutDashboard, roles: ['OWNER', 'HR'] },
  { path: '/admin/monitor', label: 'Giám sát', icon: ShieldCheck, roles: ['OWNER', 'HR', 'SECURITY'] },
  { path: '/admin/employees', label: 'Nhân viên', icon: Users, roles: ['OWNER', 'HR', 'MANAGER'] },
  { path: '/admin/faces', label: 'Xác nhận khuôn mặt', icon: ScanFace, roles: ['OWNER', 'HR'] },
  { path: '/admin/attendance', label: 'Bảng công', icon: CalendarDays, roles: ['OWNER', 'HR', 'MANAGER'] },
  { path: '/admin/requests', label: 'Giải trình', icon: ClipboardList, roles: ['OWNER', 'HR', 'MANAGER'] },
  { path: '/admin/events', label: 'Sự kiện', icon: FileClock, roles: ['OWNER', 'HR', 'MANAGER', 'SECURITY'] },
  { path: '/admin/schedules', label: 'Ca & lịch', icon: CalendarDays, roles: ['OWNER', 'HR'] },
  { path: '/admin/organization', label: 'Phòng ban & tài khoản', icon: Building2, roles: ['OWNER', 'HR'] },
  { path: '/admin/gates', label: 'Cửa & thiết bị', icon: DoorOpen, roles: ['OWNER', 'HR'] },
  { path: '/admin/settings', label: 'Cấu hình nhận dạng', icon: Settings2, roles: ['OWNER', 'HR'] },
  { path: '/admin/audit', label: 'Nhật ký', icon: ScrollText, roles: ['OWNER'] },
];

export function AdminArea(props: { session: Session; busy: boolean; error: string; onLogout: () => void }) {
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } } }));
  return <QueryClientProvider client={client}><AdminShell {...props} /></QueryClientProvider>;
}

function AdminShell({ session, busy, error, onLogout }: { session: Session; busy: boolean; error: string; onLogout: () => void }) {
  const navigate = useNavigate(); const { pathname } = useLocation();
  const [drawer, setDrawer] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const visible = entries.filter(entry => session.user.roles.some(({ role }) => entry.roles.includes(role)));
  const active = entries.find(entry => entry.path === pathname || entry.path !== '/admin' && pathname.startsWith(`${entry.path}/`));
  const allowed = !!active && visible.includes(active);
  const health = useQuery({ queryKey: ['health'], queryFn: async ({ signal }) => readResult(await api.GET('/health', { signal: AbortSignal.any([signal, AbortSignal.timeout(5000)]) })), refetchInterval: 30000 });
  const healthText = health.isError ? 'Hub mất kết nối' : !health.data ? 'Đang kiểm tra Hub' : health.data.status === 'ok' ? 'Hub trực tuyến' : 'Hub chưa sẵn sàng';
  useGSAP(() => {
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => { gsap.fromTo('.admin-content', { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: .28, ease: 'power2.out', clearProps: 'all' }); });
    return () => media.revert();
  }, { scope: container, dependencies: [pathname], revertOnUpdate: true });
  const navigation = (expanded = false) => <nav aria-label={expanded ? 'Điều hướng quản trị mở rộng' : 'Điều hướng quản trị'}>{visible.map(({ path, label, icon: Icon }) => <Tooltip key={path} title={!expanded ? label : undefined} placement="right"><Link to={path} className={`rail-item ${active?.path === path ? 'selected' : ''}`} aria-label={label} aria-current={active?.path === path ? 'page' : undefined} onClick={() => setDrawer(false)}><Icon size={24} strokeWidth={1.5} />{expanded && <span>{label}</span>}</Link></Tooltip>)}</nav>;
  return <div className="admin-layout" ref={container}>
    <a className="skip-link" href="#main-content">Đi tới nội dung</a><aside className="admin-rail"><div className="rail-logo"><Fingerprint size={28} /></div>{navigation()}<span className="rail-end">FG</span></aside>
    <Drawer title="FaceGate · Quản trị" placement="left" width={300} open={drawer} onClose={() => setDrawer(false)} className="navigation-drawer">{navigation(true)}</Drawer>
    <div className="admin-main">
      <header className="admin-header"><Button className="mobile-menu" aria-label="Mở điều hướng" type="text" icon={<Menu size={22} />} onClick={() => setDrawer(true)} /><span className="company-label">FaceGate</span><span className={`hub-indicator ${health.isError || health.data?.status === 'degraded' ? 'offline' : health.data?.status === 'ok' ? 'online' : 'unknown'}`} role="status"><i />{healthText}</span>
        {visible.some(entry => entry.path === '/admin/monitor') && <Tooltip title="Giám sát và cảnh báo"><Button type="text" aria-label="Giám sát và cảnh báo" icon={<Bell size={20} />} onClick={() => navigate('/admin/monitor')} /></Tooltip>}
        <Dropdown trigger={['click']} menu={{ items: [ ...(session.user.employee ? [{ key: 'me', label: 'Trang cá nhân' }] : []), { key: 'password', label: 'Đổi mật khẩu' }, { key: 'logout', label: 'Đăng xuất', icon: <LogOut size={16} /> } ], onClick: ({ key }) => { if (key === 'logout') onLogout(); else navigate(key === 'me' ? '/me' : '/change-password'); } }}><Button type="text" className="account-button" aria-label="Menu tài khoản" disabled={busy}><Avatar size={32}>{(session.user.employee?.full_name || session.user.email).slice(0, 1).toUpperCase()}</Avatar><span className="account-details"><b>{session.user.employee?.full_name || session.user.email}</b><small>{session.user.roles.map(({ role }) => statusInfo('user_role.role', role).label).join(' · ')}</small></span></Button></Dropdown>
      </header>
      <main className="admin-content" id="main-content" tabIndex={-1}>
        {error && <Alert className="feedback" type="error" role="alert" message={error} showIcon />}
        {!allowed ? <Result status="403" title="403" subTitle="Bạn không có quyền xem trang này" /> : pathname === '/admin/employees' ? <EmployeesPage session={session} /> : pathname.startsWith('/admin/employees/') ? <EmployeeDetail session={session} /> : pathname === '/admin/faces' ? <FacesPage /> : pathname === '/admin/organization' ? <OrganizationPage session={session} /> : pathname === '/admin/gates' ? <GatesPage session={session} /> : pathname === '/admin/settings' ? <SettingsPage session={session} /> : pathname === '/admin/audit' ? <AuditPage /> : pathname === '/admin/schedules' ? <SchedulesPage /> : pathname === '/admin/attendance' ? <AttendancePage session={session} /> : pathname === '/admin/requests' ? <RequestsPage session={session} /> : pathname === '/admin' ? <DashboardPage /> : <><PageHero title={active.label} description="Không gian quản trị FaceGate" /><section className="content-panel"><Alert type="info" showIcon message="Bạn đã đăng nhập thành công" description="Nội dung trang này sẽ được triển khai ở chức năng tiếp theo." /><Button className="start-employees" type="primary" onClick={() => navigate('/admin/employees')} disabled={!visible.some(entry => entry.path === '/admin/employees')}>Mở danh sách nhân viên</Button></section></>}
      </main>
      <footer className="admin-footer">Bản trình diễn nghiên cứu – không dùng thương mại</footer>
    </div>
  </div>;
}

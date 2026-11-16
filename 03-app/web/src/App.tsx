import { lazy, Suspense, useRef, useState, useSyncExternalStore } from 'react';
import { freshToken, getSession, setAuthSession, subscribeSession } from './shared/session';
import { Alert, Button, Form, Input, Result, Typography } from 'antd';
import { ArrowRight, Eye, EyeOff, Fingerprint, LogOut, ShieldCheck } from 'lucide-react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { api, connectionError, errorMessage, type Session } from './api/client';
import type { components } from './api/schema';
import { adminHome, canAdmin } from './shared/access';
const AdminArea = lazy(() => import('./admin/AdminArea').then(module => ({ default: module.AdminArea })));
const MeArea = lazy(() => import('./me/MeArea').then(module => ({ default: module.MeArea })));

const { Title, Paragraph, Text } = Typography;
const passwordIcon = (visible: boolean) => <button type="button" aria-label={visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} aria-pressed={visible}>{visible ? <EyeOff size={18} /> : <Eye size={18} />}</button>;

export function App() {
  // Phiên giữ trong bộ nhớ; tải lại trang yêu cầu đăng nhập lại.
  const session: Session | null = useSyncExternalStore(subscribeSession, getSession);
  const setSession = setAuthSession;
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  const [loginForm] = Form.useForm<components['schemas']['LoginRequest']>();
  const [passwordForm] = Form.useForm();

  async function submitLogin(values: components['schemas']['LoginRequest']) {
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setError(''); setNotice('');
    try {
      const { data, error: failure, response } = await api.POST('/auth/login', {
        body: { email: values.email.trim(), password: values.password }, signal: AbortSignal.timeout(15000),
      });
      if (!data) { setError(errorMessage(response.status, failure)); return; }
      setSession(data); loginForm.resetFields();
      navigate(data.must_change_password ? '/change-password' : canAdmin(data.user) && data.user.employee ? '/choose' : canAdmin(data.user) ? adminHome(data.user) : '/me', { replace: true });
    } catch { setError(connectionError); }
    finally { submitting.current = false; setBusy(false); }
  }

  async function changePassword(values: components['schemas']['ChangePassword']) {
    if (!session || submitting.current) return;
    submitting.current = true; setBusy(true); setError('');
    try {
      const { error: failure, response } = await api.POST('/auth/change-password', {
        body: { old_password: values.old_password, new_password: values.new_password },
        headers: { Authorization: `Bearer ${session.access_token}` }, signal: AbortSignal.timeout(15000),
      });
      if (!response.ok) { setError(failure?.error.message || 'Không thể đổi mật khẩu. Vui lòng thử lại.'); return; }
      setSession(null); passwordForm.resetFields(); setNotice('Đã đổi mật khẩu. Vui lòng đăng nhập lại.'); navigate('/login', { replace: true });
    } catch { setError(connectionError); }
    finally { submitting.current = false; setBusy(false); }
  }

  async function logout() {
    if (!session || submitting.current) return;
    submitting.current = true; setBusy(true); setError('');
    try {
      await freshToken();
      const active = getSession();
      if (!active) { navigate('/login', { replace: true }); return; }
      const { response, error: failure } = await api.POST('/auth/logout', {
        body: { refresh_token: active.refresh_token }, headers: { Authorization: `Bearer ${active.access_token}` }, signal: AbortSignal.timeout(15000),
      });
      if (!response.ok && response.status !== 401) { setError(failure?.error.message || 'Chưa đăng xuất được. Vui lòng thử lại.'); return; }
      setSession(null); navigate('/login', { replace: true });
    } catch { setError(connectionError); }
    finally { submitting.current = false; setBusy(false); }
  }

  let content;
  if (!session && location.pathname !== '/login') return <Navigate to="/login" replace />;
  if (session?.must_change_password && location.pathname !== '/change-password') return <Navigate to="/change-password" replace />;
  if (session && !session.must_change_password && location.pathname.startsWith('/admin') && canAdmin(session.user)) return <Suspense fallback={<main className="loading-page" role="status">Đang tải giao diện…</main>}><AdminArea key={session.user.id} session={session} busy={busy} error={error} onLogout={() => void logout()} /></Suspense>;
  if (session && !session.must_change_password && /^\/me(?:\/|$)/.test(location.pathname)) {
    if (!session.user.employee) return <Navigate to={canAdmin(session.user) ? adminHome(session.user) : '/choose'} replace />;
    return <Suspense fallback={<main className="loading-page" role="status">Đang tải giao diện…</main>}><MeArea key={`${session.user.id}:${JSON.stringify(session.user.roles)}`} session={session} busy={busy} error={error} onLogout={() => void logout()} /></Suspense>;
  }

  if (!session) {
    content = <>
      <div className="section-kicker">CHÀO MỪNG TRỞ LẠI</div>
      <Title level={2}>Đăng nhập</Title>
      <Paragraph type="secondary" className="intro">Truy cập không gian làm việc của bạn.</Paragraph>
      <Form scrollToFirstError form={loginForm} layout="vertical" onFinish={submitLogin} requiredMark={false} disabled={busy}>
        <div className="inset-field">
          <Form.Item name="email" label="Email" normalize={(value: string) => value.trim()} rules={[{ required: true, message: 'Vui lòng nhập email' }, { type: 'email', message: 'Email không đúng định dạng' }]}>
            <Input variant="filled" autoComplete="username" inputMode="email" spellCheck={false} placeholder="ten@congty.vn" />
          </Form.Item>
        </div>
        <div className="inset-field password-field">
          <Form.Item name="password" label="Mật khẩu" rules={[{ required: true, message: 'Vui lòng nhập mật khẩu' }]}>
            <Input.Password iconRender={passwordIcon} variant="filled" autoComplete="current-password" placeholder="Nhập mật khẩu của bạn" />
          </Form.Item>
        </div>
        <Button type="primary" block size="large" htmlType="submit" loading={busy} icon={<ArrowRight size={18} />} iconPosition="end">Đăng nhập</Button>
      </Form>
    </>;
  } else if (location.pathname === '/change-password') {
    content = <>
      <div className="section-kicker">BẢO VỆ TÀI KHOẢN</div>
      <Title level={2}>{session.must_change_password ? 'Đổi mật khẩu lần đầu' : 'Đổi mật khẩu'}</Title>
      <Paragraph type="secondary">Mật khẩu mới cần có ít nhất 8 ký tự.</Paragraph>
      <Form scrollToFirstError form={passwordForm} layout="vertical" requiredMark={false} onFinish={changePassword} disabled={busy}>
        <Form.Item name="old_password" label="Mật khẩu hiện tại" rules={[{ required: true, message: 'Vui lòng nhập mật khẩu hiện tại' }]}><Input.Password iconRender={passwordIcon} variant="filled" autoComplete="current-password" /></Form.Item>
        <Form.Item name="new_password" label="Mật khẩu mới" rules={[{ required: true, message: 'Vui lòng nhập mật khẩu mới' }, { min: 8, message: 'Mật khẩu mới cần ít nhất 8 ký tự' }]}><Input.Password iconRender={passwordIcon} variant="filled" autoComplete="new-password" /></Form.Item>
        <Form.Item name="confirmation" label="Nhập lại mật khẩu mới" dependencies={['new_password']} rules={[{ required: true, message: 'Vui lòng nhập lại mật khẩu mới' }, ({ getFieldValue }: { getFieldValue: (name: string) => string }) => ({ validator: (_: unknown, value: string) => !value || value === getFieldValue('new_password') ? Promise.resolve() : Promise.reject(new Error('Mật khẩu nhập lại chưa khớp')) })]}><Input.Password iconRender={passwordIcon} variant="filled" autoComplete="new-password" /></Form.Item>
        <Button type="primary" block htmlType="submit" loading={busy}>Lưu mật khẩu mới</Button>
      </Form>
    </>;
  } else if (location.pathname === '/choose' || location.pathname === '/login') {
    content = <><Title level={2}>Chọn không gian</Title><Paragraph type="secondary">Vào trang quản trị hay trang cá nhân?</Paragraph>
      <div className="actions">{canAdmin(session.user) && <Button type="primary" block onClick={() => navigate(adminHome(session.user))}>Trang quản trị</Button>}{session.user.employee && <Button block onClick={() => navigate('/me')}>Trang cá nhân</Button>}</div>
    </>;
  } else {
    const allowed = location.pathname.startsWith('/admin') ? canAdmin(session.user) : location.pathname === '/me' && !!session.user.employee;
    content = allowed ? <>
      <div className="section-kicker">ĐĂNG NHẬP THÀNH CÔNG</div><Title level={2}>{location.pathname === '/me' ? 'Trang cá nhân' : 'Trang quản trị'}</Title>
      <Paragraph>{session.user.email}</Paragraph><Alert type="info" showIcon message="Bạn đã đăng nhập thành công" description="Nội dung trang này sẽ được triển khai ở chức năng tiếp theo." />
      {canAdmin(session.user) && session.user.employee && <Button block onClick={() => navigate('/choose')}>Chọn lại không gian</Button>}
      <Button block onClick={() => { setError(''); navigate('/change-password'); }}>Đổi mật khẩu</Button>
    </> : <Result status="403" title="403" subTitle="Bạn không có quyền xem trang này" extra={<Button onClick={() => navigate(canAdmin(session.user) ? adminHome(session.user) : '/me')}>Về trang của tôi</Button>} />;
  }

  return <main className="auth-page">
    <header className="brand"><span className="brand-icon"><Fingerprint size={24} strokeWidth={1.7} /></span><span>FaceGate</span></header>
    <section className="auth-card" aria-label="Tài khoản FaceGate">
      <div className="card-emblem"><ShieldCheck size={24} strokeWidth={1.5} /></div>
      {notice && <Alert className="feedback" role="status" type="success" showIcon message={notice} />}
      {error && <Alert className="feedback" role="alert" type="error" showIcon message={error} />}
      {content}
      {session && <Button className="logout-button" type="text" block loading={busy} icon={<LogOut size={16} />} onClick={logout}>Đăng xuất</Button>}
      <div className="card-footer"><span className="footer-dot" />Bản trình diễn nghiên cứu</div>
    </section>
    <footer className="page-footer"><Text type="secondary">Chấm công & kiểm soát ra vào bằng khuôn mặt</Text><span>Không dùng thương mại</span></footer>
  </main>;
}

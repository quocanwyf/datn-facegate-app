import { useRef, useState } from 'react';
import { Alert, Button, Empty, Modal } from 'antd';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';
import { api, type Session } from '../api/client';
import type { components } from '../api/schema';
import { readResult, requestMessage } from '../api/result';
import { QueryState } from '../components/QueryState';
import { StatusPill } from '../components/StatusPill';
import { KpiTile } from '../components/KpiTile';
import { companyDate } from '../shared/companyDate';
import { dateTime } from '../shared/format';
import { statusInfo } from '../theme/status';

gsap.registerPlugin(useGSAP);
export const shortDate = (value: string) => value.split('-').reverse().join('/');
export const clock = (value?: string | null) => value ? companyDate(value).format('HH:mm') : '—';
type Day = components['schemas']['AttendanceDay'];
function Times({ day }: { day?: Day | null }) {
  const root = useRef<HTMLDivElement>(null), previous = useRef<string>();
  const value = `${day?.check_in_at ?? ''}/${day?.check_out_at ?? ''}`;
  useGSAP(() => {
    const changed = previous.current !== undefined && previous.current !== value; previous.current = value;
    const media = gsap.matchMedia(); if (changed) media.add('(prefers-reduced-motion: no-preference)', () => { gsap.fromTo('.me-time b', { rotationX: -75, autoAlpha: .4 }, { rotationX: 0, autoAlpha: 1, duration: .35, clearProps: 'transform,opacity,visibility' }); });
    return () => media.revert();
  }, { scope: root, dependencies: [value], revertOnUpdate: true });
  return <div ref={root} className="me-times"><div className="me-time"><span>Giờ vào</span><b>{clock(day?.check_in_at)}</b></div><div className="me-time"><span>Giờ ra</span><b>{clock(day?.check_out_at)}</b></div></div>;
}
function DayStatus({ day }: { day: Day }) { return <div className="me-day-status"><StatusPill domain="attendance_day.status" value={day.status} />{!day.finalized && ['NOT_STARTED', 'WAITING_IN', 'IN_PROGRESS'].includes(day.status) && <small>tạm thời · chưa chốt ngày công</small>}</div>; }
export function TodayPage({ session }: { session: Session }) {
  const today = useQuery({ queryKey: ['me-today'], queryFn: async ({ signal }) => readResult(await api.GET('/me/today', { signal })), refetchOnMount: 'always', refetchInterval: 60000 });
  const value = !today.isError ? today.data : undefined;
  return <><div className="me-intro"><div><p>Chào {session.user.employee?.full_name}</p><h2>Ngày làm việc của bạn</h2></div><Button aria-label="Làm mới hôm nay" icon={<RefreshCw size={18} />} loading={today.isFetching} onClick={() => void today.refetch()} /></div><QueryState query={today} />{value && <>
    <p className="me-muted">{shortDate(value.date)} · {new Intl.DateTimeFormat('vi-VN', { weekday: 'long' }).format(new Date(`${value.date}T12:00:00+07:00`))}</p>
    {value.attendance_method === 'MANUAL' && <Alert type="info" showIcon message="Bạn chấm công tại quầy lễ tân" />}
    <section className="me-card me-shift"><div className="section-kicker">CA HÔM NAY</div><h2>{value.holiday ? `Hôm nay là ngày lễ: ${value.holiday}` : value.shift?.name ?? 'Hôm nay bạn không có ca'}</h2>{value.shift && <p>{value.shift.start_time} – {value.shift.end_time}</p>}<Times day={value.day} />{value.day && <DayStatus day={value.day} />}<Link className="me-link" to={`/me/days/${value.date}`}>Xem chi tiết ngày →</Link></section>
    <section className="me-card"><h2>Lượt qua cửa hôm nay</h2>{!value.passes.length && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Chưa có lượt qua cửa" />}{value.passes.map((row, index) => <article className="me-event" key={`${row.occurred_at}/${index}`}><b>{clock(row.occurred_at)} · {row.gate_name}</b><StatusPill domain="recognition_event.result" value={row.result} />{row.gate_mode === 'ACCESS_ONLY' && <small>Không tính công</small>}</article>)}</section>
  </>}</>;
}
export function MonthPage() {
  const [month, setMonth] = useState(() => companyDate().format('YYYY-MM'));
  const query = useQuery({ queryKey: ['me-month', month], queryFn: async ({ signal }) => readResult(await api.GET('/me/attendance', { params: { query: { month } }, signal })) });
  const data = !query.isError ? query.data : undefined;
  const begin = companyDate(`${month}-01T12:00:00+07:00`), offset = (begin.day() + 6) % 7;
  const days = new Map(data?.days.map(row => [row.work_date, row]));
  return <><div className="me-month-picker"><Button aria-label="Tháng trước" icon={<ChevronLeft size={20} />} onClick={() => setMonth(begin.subtract(1, 'month').format('YYYY-MM'))} /><h2>Tháng {begin.format('MM/YYYY')}</h2><Button aria-label="Tháng sau" icon={<ChevronRight size={20} />} onClick={() => setMonth(begin.add(1, 'month').format('YYYY-MM'))} /></div><QueryState query={query} />{data && <>
    <section className="me-card"><div className="me-calendar" aria-label={`Bảng công tháng ${month}`}>{['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map(label => <span className="me-weekday" key={label}>{label}</span>)}{Array.from({ length: offset }, (_, index) => <span key={`blank${index}`} />)}{Array.from({ length: begin.daysInMonth() }, (_, index) => {
      const date = `${month}-${String(index + 1).padStart(2, '0')}`, day = days.get(date), info = day && statusInfo('attendance_day.status', day.status);
      return <Link to={`/me/days/${date}`} key={date} aria-label={`${shortDate(date)} · ${info?.label ?? 'Chưa có dữ liệu'}`} className={date === companyDate().format('YYYY-MM-DD') ? 'is-today' : ''}><span>{index + 1}</span><i style={{ background: info?.bg, borderColor: info?.fg }} /></Link>;
    })}</div><details><summary>Chú giải trạng thái</summary><div className="me-legend">{(['NORMAL', 'LATE', 'EARLY', 'LATE_EARLY', 'ABSENT', 'MISSING_OUT', 'WAITING_IN', 'IN_PROGRESS', 'NOT_STARTED', 'LEAVE', 'HOLIDAY', 'OFF'] as const).map(status => <StatusPill key={status} domain="attendance_day.status" value={status} />)}</div></details></section>
    <div className="me-kpis"><KpiTile label="Ngày công" value={data.summary.work_days} /><KpiTile label="Số lần muộn" value={data.summary.late_count} /><KpiTile label="Tổng phút muộn" value={data.summary.late_minutes} /><KpiTile label="Ngày thiếu giờ ra/vắng" value={data.summary.missing_or_absent} /></div>
  </>}</>;
}
export function DayPage() {
  const date = useParams().date ?? '', parsed = new Date(`${date}T12:00:00+07:00`);
  const valid = /^\d{4}-\d{2}-\d{2}$/.test(date) && !Number.isNaN(parsed.valueOf()) && companyDate(parsed.toISOString()).format('YYYY-MM-DD') === date;
  const query = useQuery({ queryKey: ['me-day', date], enabled: valid, queryFn: async ({ signal }) => readResult(await api.GET('/me/days/{date}', { params: { path: { date } }, signal })) });
  const value = !query.isError ? query.data : undefined;
  if (!valid) return <Alert type="error" message="Ngày không hợp lệ" />;
  return <><Link className="me-link" to="/me/attendance">← Bảng công</Link><h2>{shortDate(date)}</h2><QueryState query={query} />{value && <>
    <section className="me-card"><h2>{value.day?.shift?.name ?? 'Không có ca được ghi nhận'}</h2>{value.day?.shift && <p>{value.day.shift.start_time} – {value.day.shift.end_time}</p>}<Times day={value.day} />{value.day ? <><DayStatus day={value.day} /><dl className="me-facts"><dt>Muộn / về sớm</dt><dd>{value.day.late_min} / {value.day.early_min} phút</dd><dt>Giờ làm</dt><dd>{Math.floor(value.day.worked_min / 60)} giờ {value.day.worked_min % 60} phút</dd><dt>Nguồn</dt><dd><StatusPill domain="attendance_day.source" value={value.day.source} /></dd></dl>{value.day.suspect_forgot_out && <Alert type="warning" showIcon message="Có thể bạn quên quét khi ra về" />}</> : <p>Chưa có dữ liệu ngày công</p>}</section>
    <section className="me-card"><h2>Sự kiện trong ngày</h2>{!value.events.length && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Chưa có sự kiện" />}{value.events.map(row => <article key={row.id} className="me-event"><b>{clock(row.occurred_at)} · {row.gate.name}</b><StatusPill domain="recognition_event.result" value={row.result} />{row.gate.mode === 'ACCESS_ONLY' && <small>Không tính công</small>}</article>)}</section>
    {value.request?.status === 'PENDING' ? <section className="me-card"><StatusPill domain="attendance_request.status" value={value.request.status} /><p>Ngày này đã có giải trình đang chờ duyệt.</p><Link to="/me/requests">Xem giải trình</Link></section> : <><Link className="me-primary-link" to={`/me/requests/new?date=${date}`}>Gửi giải trình</Link>{value.request && <p>Giải trình gần nhất: <StatusPill domain="attendance_request.status" value={value.request.status} /></p>}</>}
  </>}</>;
}
export function FacePage() {
  const client = useQueryClient(), lock = useRef(false); const [confirm, setConfirm] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const face = useQuery({ queryKey: ['me-face'], queryFn: async ({ signal }) => readResult(await api.GET('/me/face', { signal })) });
  async function revoke() {
    if (lock.current) return; lock.current = true; setBusy(true); setError('');
    try { readResult(await api.POST('/me/face/revoke')); setConfirm(false); setNotice('Đã rút đồng ý và xóa dữ liệu khuôn mặt. Bạn chấm công tại quầy lễ tân.'); }
    catch (failure) { setError(requestMessage(failure)); }
    finally { await Promise.all([client.invalidateQueries({ queryKey: ['me-face'] }), client.invalidateQueries({ queryKey: ['me-today'] })]); lock.current = false; setBusy(false); }
  }
  return <><h2>Dữ liệu khuôn mặt</h2>{notice && <Alert role="status" type="success" message={notice} />}<QueryState query={face} />{!face.isError && face.data && <section className="me-card"><StatusPill domain="face_profile.status" value={face.data.face_profile_status} /><p>{face.data.face_consent_at ? `Đã đồng ý lúc ${dateTime(face.data.face_consent_at)}` : 'Chưa đồng ý'}</p><p>Phương thức: {face.data.attendance_method === 'FACE' ? 'Khuôn mặt' : 'Chấm công hộ'}</p><div className="me-privacy"><h3>Bạn kiểm soát dữ liệu của mình</h3><p>Ảnh mẫu và vector khuôn mặt được lưu trong kho riêng của Hub để nhận diện.</p><p>Khi rút đồng ý, hồ sơ đang dùng và chờ duyệt cùng dữ liệu liên kết sẽ bị xóa; công và sự kiện vẫn được giữ.</p><p>Muốn sử dụng lại, bạn cần đồng ý và đăng ký khuôn mặt lại tại kiosk.</p></div><Button danger block onClick={() => { setError(''); setConfirm(true); }}>Rút đồng ý và xoá dữ liệu khuôn mặt</Button></section>}
    <Modal open={confirm} title="Rút đồng ý khuôn mặt" okText="Rút đồng ý và xóa" okButtonProps={{ danger: true }} cancelText="Hủy" confirmLoading={busy} closable={!busy} maskClosable={!busy} cancelButtonProps={{ disabled: busy }} onCancel={() => setConfirm(false)} onOk={() => void revoke()}>{error && <Alert role="alert" type="error" message={error} />}<p>Sau khi rút, bạn sẽ không chấm công bằng khuôn mặt được nữa và phải chấm công tại quầy lễ tân. Tiếp tục?</p>{error && <p>Nếu xóa chưa hoàn tất, nhận dạng vẫn bị ngừng. Bấm lại để thử xóa phần còn lại.</p>}</Modal>
  </>;
}

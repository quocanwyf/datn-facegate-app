import { useRef, useState } from 'react';
import { Alert, Button, DatePicker, Empty, Form, Input, Modal, Segmented, Select, Space, TimePicker } from 'antd';
import dayjs, { type Dayjs } from 'dayjs';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { api, type Session } from '../api/client';
import type { components } from '../api/schema';
import { HttpError, readResult, requestMessage } from '../api/result';
import { QueryState } from '../components/QueryState';
import { StatusPill } from '../components/StatusPill';
import { companyDate } from '../shared/companyDate';
import { dateTime } from '../shared/format';
import { statusInfo } from '../theme/status';
import { myRequests, teamRequests, type AttendanceRequest } from './data';
import { shortDate } from './Pages';

type RequestForm = { work_date: string; type: components['schemas']['RequestType']; requested_in?: string; requested_out?: string; reason: string };
const types = ['FORGOT_IN', 'FORGOT_OUT', 'NOT_RECOGNIZED', 'BUSINESS_TRIP', 'OTHER'] as const;
export function NewRequestPage() {
  const [search] = useSearchParams(), navigate = useNavigate(), client = useQueryClient(); const [form] = Form.useForm<RequestForm>();
  const kind = Form.useWatch('type', form), lock = useRef(false); const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const inVisible = ['FORGOT_IN', 'NOT_RECOGNIZED', 'BUSINESS_TRIP'].includes(kind), outVisible = ['FORGOT_OUT', 'NOT_RECOGNIZED', 'BUSINESS_TRIP'].includes(kind);
  async function submit(values: RequestForm) {
    if (lock.current) return; lock.current = true; setBusy(true); setError('');
    try {
      const timestamp = (value?: string) => value ? companyDate(`${values.work_date}T${value}:00+07:00`).toISOString() : null;
      readResult(await api.POST('/me/requests', { body: { work_date: values.work_date, type: values.type, reason: values.reason.trim(), requested_in: inVisible ? timestamp(values.requested_in) : null, requested_out: outVisible ? timestamp(values.requested_out) : null } }));
      await Promise.all(['me-requests', 'me-day'].map(key => client.invalidateQueries({ queryKey: [key] }))); navigate('/me/requests', { replace: true });
    } catch (failure) { setError(failure instanceof HttpError && failure.code === 'REQUEST_PENDING_EXISTS' ? 'Ngày này đã có giải trình đang chờ duyệt' : requestMessage(failure)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <><Link to="/me/requests" className="me-link">← Giải trình của tôi</Link><h2>Gửi giải trình</h2><section className="me-card">{error && <Alert role="alert" type="error" message={error} />}<Form form={form} layout="vertical" requiredMark={false} disabled={busy} initialValues={{ work_date: search.get('date') ?? companyDate().format('YYYY-MM-DD'), type: 'FORGOT_IN' }} onFinish={values => void submit(values)}>
    <Form.Item name="work_date" label="Ngày giải trình" getValueProps={(value?: string) => ({ value: value ? dayjs(value) : null })} normalize={(value: Dayjs | null) => value?.format('YYYY-MM-DD')} rules={[{ required: true, message: 'Chọn ngày giải trình' }]}><DatePicker format="DD/MM/YYYY" inputReadOnly /></Form.Item>
    <Form.Item name="type" label="Loại giải trình" rules={[{ required: true }]}><Select onChange={() => form.resetFields(['requested_in', 'requested_out'])} options={types.map(value => ({ value, label: statusInfo('attendance_request.type', value).label }))} /></Form.Item>
    {inVisible && <Form.Item name="requested_in" label="Giờ vào đề nghị" preserve={false} getValueProps={(value?: string) => ({ value: value ? dayjs(`2000-01-01T${value}`) : null })} normalize={(value: Dayjs | null) => value?.format('HH:mm')} rules={[{ required: kind === 'FORGOT_IN', message: 'Nhập giờ vào đề nghị' }]}><TimePicker format="HH:mm" needConfirm={false} /></Form.Item>}
    {outVisible && <Form.Item name="requested_out" label="Giờ ra đề nghị" preserve={false} getValueProps={(value?: string) => ({ value: value ? dayjs(`2000-01-01T${value}`) : null })} normalize={(value: Dayjs | null) => value?.format('HH:mm')} dependencies={['requested_in']} rules={[{ required: kind === 'FORGOT_OUT', message: 'Nhập giờ ra đề nghị' }, ({ getFieldValue }) => ({ validator: (_, value: string) => !value || !getFieldValue('requested_in') || value > getFieldValue('requested_in') ? Promise.resolve() : Promise.reject(new Error('Giờ ra phải sau giờ vào')) })]}><TimePicker format="HH:mm" needConfirm={false} /></Form.Item>}
    <Form.Item name="reason" label="Lý do" rules={[{ required: true, whitespace: true, message: 'Nhập lý do giải trình' }]}><Input.TextArea rows={4} /></Form.Item><Button type="primary" block htmlType="submit" loading={busy}>Gửi giải trình</Button>
  </Form></section></>;
}
function RequestBody({ row }: { row: AttendanceRequest }) { return <><div className="me-request-heading"><b>{shortDate(row.work_date)}</b><StatusPill domain="attendance_request.status" value={row.status} /></div><StatusPill domain="attendance_request.type" value={row.type} /><p>{row.reason}</p><dl className="me-facts"><dt>Vào đề nghị</dt><dd>{dateTime(row.requested_in)}</dd><dt>Ra đề nghị</dt><dd>{dateTime(row.requested_out)}</dd></dl></>; }
export function MyRequestsPage() {
  const [tab, setTab] = useState('pending'), [cancel, setCancel] = useState<AttendanceRequest>(), [busy, setBusy] = useState(false), [error, setError] = useState(''); const lock = useRef(false), client = useQueryClient();
  const query = useQuery({ queryKey: ['me-requests', tab], queryFn: async ({ signal }) => (await Promise.all((tab === 'pending' ? ['PENDING'] as const : ['APPROVED', 'REJECTED', 'CANCELLED'] as const).map(status => myRequests(status, signal)))).flat().sort((a, b) => b.created_at.localeCompare(a.created_at)) });
  async function doCancel() {
    if (!cancel || lock.current) return; lock.current = true; setBusy(true); setError('');
    try { readResult(await api.POST('/me/requests/{id}/cancel', { params: { path: { id: cancel.id } } })); setCancel(undefined); await Promise.all(['me-requests', 'me-day'].map(key => client.invalidateQueries({ queryKey: [key] }))); }
    catch (failure) { setError(requestMessage(failure)); } finally { lock.current = false; setBusy(false); }
  }
  return <><div className="me-intro"><h2>Giải trình của tôi</h2><Link className="me-link" to="/me/requests/new">Gửi mới</Link></div><Segmented block aria-label="Trạng thái giải trình" value={tab} options={[{ value: 'pending', label: 'Chờ duyệt' }, { value: 'processed', label: 'Đã xử lý' }]} onChange={setTab} /><QueryState query={query} />{!query.isError && query.data && <>{!query.data.length && <Empty description="Chưa có giải trình" />}{query.data.map(row => <article className="me-card" key={row.id}><RequestBody row={row} />{row.status === 'PENDING' ? <Button danger onClick={() => { setError(''); setCancel(row); }}>Hủy giải trình</Button> : <><p>{row.reviewer_name ?? '—'} · {dateTime(row.reviewed_at)}</p><p>Ghi chú: {row.review_note || '—'}</p></>}</article>)}</>}
    <Modal open={!!cancel} title="Hủy giải trình đang chờ?" okText="Xác nhận hủy" cancelText="Giữ giải trình" confirmLoading={busy} closable={!busy} maskClosable={!busy} cancelButtonProps={{ disabled: busy }} onCancel={() => setCancel(undefined)} onOk={() => void doCancel()}>{error && <Alert role="alert" type="error" message={error} />}<p>{cancel && shortDate(cancel.work_date)} · {cancel && statusInfo('attendance_request.type', cancel.type).label}</p></Modal>
  </>;
}
export function TeamPage({ session }: { session: Session }) {
  const query = useQuery({ queryKey: ['me-team'], queryFn: ({ signal }) => teamRequests(signal) }), client = useQueryClient();
  const [action, setAction] = useState<{ row: AttendanceRequest; approve: boolean }>(), [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState(''); const lock = useRef(false), [form] = Form.useForm<{ note?: string }>();
  const rows = query.data?.filter(row => row.employee.id !== session.user.employee?.id && row.can_review);
  async function save(note?: string) {
    if (!action || lock.current) return; lock.current = true; setBusy(true); setError('');
    try {
      const params = { params: { path: { id: action.row.id } }, body: { note: note?.trim() || null } };
      if (action.approve) readResult(await api.POST('/attendance/requests/{id}/approve', params)); else readResult(await api.POST('/attendance/requests/{id}/reject', params));
      setAction(undefined); setNotice('Đã xử lý giải trình'); await client.invalidateQueries({ queryKey: ['me-team'] });
    } catch (failure) { setError(requestMessage(failure)); } finally { lock.current = false; setBusy(false); }
  }
  return <><h2>Duyệt giải trình</h2><p className="me-muted">Không tự duyệt. Nếu chưa có người đúng cấp, cần bố trí người duyệt hợp lệ.</p>{notice && <Alert role="status" type="success" message={notice} />}<QueryState query={query} />{!query.isError && rows && <>{!rows.length && <Empty description="Không có giải trình chờ duyệt" />}{rows.map(row => <article className="me-card" key={row.id}><h3>{row.employee.full_name} · {row.employee.code}</h3><RequestBody row={row} /><p>Giờ thực tế: {dateTime(row.recorded_in)} → {dateTime(row.recorded_out)}</p><Space><Button disabled={busy} onClick={() => { form.resetFields(); setError(''); setAction({ row, approve: false }); }}>Từ chối</Button><Button type="primary" disabled={busy} onClick={() => { form.resetFields(); setError(''); setAction({ row, approve: true }); }}>Duyệt</Button></Space></article>)}</>}
    <Modal className="me-review-sheet" open={!!action} title={action?.approve ? 'Duyệt giải trình' : 'Từ chối giải trình'} okText="Xác nhận" cancelText="Hủy" confirmLoading={busy} closable={!busy} maskClosable={!busy} cancelButtonProps={{ disabled: busy }} onCancel={() => setAction(undefined)} onOk={() => form.submit()}>{error && <Alert role="alert" type="error" message={error} />}<p>{action?.row.employee.full_name}</p><Form form={form} layout="vertical" disabled={busy} onFinish={values => void save(values.note)}><Form.Item name="note" label={action?.approve ? 'Ghi chú (không bắt buộc)' : 'Lý do từ chối'} rules={[{ required: !action?.approve, whitespace: true, message: 'Nhập lý do từ chối' }]}><Input.TextArea rows={4} /></Form.Item></Form></Modal>
  </>;
}

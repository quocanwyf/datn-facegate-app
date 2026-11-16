import { useRef, useState } from 'react';
import { Alert, Button, Form, Input, Modal, Segmented, Space, Table } from 'antd';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { Session } from '../../api/client';
import { api } from '../../api/client';
import type { components } from '../../api/schema';
import { readResult, requestMessage } from '../../api/result';
import { QueryState } from '../../components/QueryState';
import { PageHero } from '../../components/PageHero';
import { StatusPill } from '../../components/StatusPill';
import { dateTime } from '../../shared/format';

type Request = components['schemas']['AttendanceRequest'];
async function loadRequests(status: components['schemas']['RequestStatus'], signal: AbortSignal) {
  const items: Request[] = [];
  for (let page = 1; ; page++) {
    const response = readResult(await api.GET('/attendance/requests', { params: { query: { status, page, size: 100 } }, signal }));
    items.push(...response.items);
    if (items.length >= response.total || !response.items.length) return items;
  }
}

export function RequestsPage({ session }: { session: Session }) {
  const [tab, setTab] = useState('pending'); const [action, setAction] = useState<{ row: Request; approve: boolean }>();
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [notice, setNotice] = useState('');
  const lock = useRef(false); const client = useQueryClient(); const [form] = Form.useForm<{ note?: string }>();
  const requests = useQuery({ queryKey: ['requests', tab, session.user.id], queryFn: async ({ signal }) => {
    const statuses = tab === 'pending' ? ['PENDING' as const] : ['APPROVED', 'REJECTED', 'CANCELLED'] as const;
    return (await Promise.all(statuses.map(status => loadRequests(status, signal)))).flat().sort((a, b) => b.created_at.localeCompare(a.created_at));
  } });
  async function save(note?: string) {
    if (!action || lock.current) return; lock.current = true; setBusy(true); setError('');
    const snapshot = action;
    try {
      if (snapshot.approve) readResult(await api.POST('/attendance/requests/{id}/approve', { params: { path: { id: snapshot.row.id } }, body: { note: note?.trim() || null } }));
      else readResult(await api.POST('/attendance/requests/{id}/reject', { params: { path: { id: snapshot.row.id } }, body: { note: note?.trim() || null } }));
      setAction(undefined); setNotice(snapshot.approve ? 'Đã duyệt giải trình và tính lại ngày công' : 'Đã từ chối giải trình');
      await Promise.all([client.invalidateQueries({ queryKey: ['requests'] }), client.invalidateQueries({ queryKey: ['attendance'] })]);
    } catch (failure) { setError(requestMessage(failure)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <><PageHero title="Giải trình" description="Đối chiếu giờ đề nghị và giờ đã ghi nhận trước khi xử lý." />
    {notice && <Alert role="status" className="feedback" type="success" message={notice} />}
    <section className="content-panel"><Segmented aria-label="Trạng thái giải trình" options={[{ value: 'pending', label: 'Chờ duyệt' }, { value: 'processed', label: 'Đã xử lý' }]} value={tab} disabled={busy} onChange={setTab} />
      {tab === 'pending' && <Alert className="feedback" type="info" showIcon message="Giải trình giữ trạng thái chờ tới khi có người đúng cấp duyệt." description="Nếu chưa có tài khoản duyệt hợp lệ, cần bố trí người duyệt. Người gửi không thể tự duyệt, kể cả có nhiều vai trò." />}
      <QueryState query={requests} /><Table rowKey="id" dataSource={requests.data} scroll={{ x: 1100 }} pagination={{ pageSize: 20, showSizeChanger: false }} columns={[
        { title: 'Nhân viên', render: (_, row: Request) => <><b>{row.employee.full_name}</b><p className="muted">{row.employee.code} · {row.employee.department_name}</p></> },
        { title: 'Ngày / loại', render: (_, row: Request) => <>{row.work_date.split('-').reverse().join('/')}<br /><StatusPill domain="attendance_request.type" value={row.type} /></> },
        { title: 'Giờ đề nghị', render: (_, row: Request) => <>{dateTime(row.requested_in)}<br />{dateTime(row.requested_out)}</> },
        { title: 'Giờ ghi nhận', render: (_, row: Request) => <>{dateTime(row.recorded_in)}<br />{dateTime(row.recorded_out)}</> },
        { title: 'Lý do / gửi lúc', render: (_, row: Request) => <>{row.reason}<p className="muted">{dateTime(row.created_at)}</p></> },
        { title: tab === 'pending' ? 'Thao tác' : 'Kết quả', render: (_, row: Request) => tab === 'processed' ? <><StatusPill domain="attendance_request.status" value={row.status} /><p>{row.reviewer_name || '—'}</p><p>{dateTime(row.reviewed_at)}</p><p>{row.review_note || '—'}</p></> : row.can_review && row.employee.id !== session.user.employee?.id ? <Space direction="vertical"><Button type="primary" aria-label={`Duyệt ${row.employee.code} ${row.work_date}`} disabled={busy} onClick={() => { setError(''); form.resetFields(); setAction({ row, approve: true }); }}>Duyệt</Button><Button danger aria-label={`Từ chối ${row.employee.code} ${row.work_date}`} disabled={busy} onClick={() => { setError(''); form.resetFields(); setAction({ row, approve: false }); }}>Từ chối</Button></Space> : <span className="muted">{row.employee.id === session.user.employee?.id ? 'Không tự duyệt' : 'Chờ người có quyền duyệt'}</span> },
      ]} />
    </section>
    <Modal open={!!action} title={action?.approve ? 'Duyệt giải trình' : 'Từ chối giải trình'} okText={action?.approve ? 'Xác nhận duyệt' : 'Xác nhận từ chối'} cancelText="Hủy" confirmLoading={busy} closable={!busy} maskClosable={!busy} cancelButtonProps={{ disabled: busy }} onCancel={() => setAction(undefined)} onOk={() => form.submit()}>
      {error && <Alert role="alert" type="error" message={error} />}<p>{action?.row.employee.full_name} · {action?.row.work_date.split('-').reverse().join('/')}</p><Form form={form} layout="vertical" disabled={busy} onFinish={values => void save(values.note)}><Form.Item name="note" label={action?.approve ? 'Ghi chú (không bắt buộc)' : 'Lý do từ chối'} rules={[{ required: !action?.approve, whitespace: true, message: 'Nhập lý do từ chối' }]}><Input.TextArea rows={3} /></Form.Item></Form>
    </Modal>
  </>;
}

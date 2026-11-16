import { useMemo, useState } from 'react';
import { Alert, Button, DatePicker, Modal, Select, Space, Table, Tabs, Tooltip } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import type { Dayjs } from 'dayjs';
import { api, type Session } from '../../api/client';
import type { components } from '../../api/schema';
import { HttpError, readResult, requestMessage } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { QueryState } from '../../components/QueryState';
import { StatusPill } from '../../components/StatusPill';
import { companyDate } from '../../shared/companyDate';
import { cos, dateTime } from '../../shared/format';
import { statusInfo, statusMaps } from '../../theme/status';
import { allEmployees } from '../attendance/data';
import { EventSnapshot } from '../monitor/EventSnapshot';
import type { Event } from '../monitor/MonitorProvider';

type Result = components['schemas']['EventResult'];
export function EventsPage({ session }: { session: Session }) {
  const location = useLocation(); const initial = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const requestedDate = initial.get('date'); const validDate = requestedDate && /^\d{4}-\d{2}-\d{2}$/.test(requestedDate) && companyDate(`${requestedDate}T00:00:00+07:00`).isValid();
  const [range, setRange] = useState<[Dayjs, Dayjs]>(validDate ? [companyDate(`${requestedDate}T00:00:00+07:00`), companyDate(`${requestedDate}T23:59:59+07:00`)] : [companyDate().startOf('day'), companyDate().endOf('day')]);
  const [gate, setGate] = useState<string>(); const [results, setResults] = useState<Result[]>([]); const [employee, setEmployee] = useState(initial.get('employee_id') || undefined); const [performer, setPerformer] = useState<string>();
  const [page, setPage] = useState(1); const [snapshot, setSnapshot] = useState<string>(); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const broad = session.user.roles.some(role => ['OWNER', 'HR', 'SECURITY'].includes(role.role));
  const query = { from_ts: range[0].toISOString(), to_ts: range[1].toISOString(), gate_id: gate, result: results.length ? results : undefined, employee_id: employee, performed_by: performer, page, size: 20 };
  const events = useQuery({ queryKey: ['events', query], queryFn: async ({ signal }) => readResult(await api.GET('/events', { params: { query }, signal })) });
  const employees = useQuery({ queryKey: ['event-employees', session.user.id], queryFn: ({ signal }) => allEmployees(signal) });
  const gates = useQuery({ queryKey: ['gates'], enabled: broad, queryFn: async ({ signal }) => readResult(await api.GET('/gates', { signal })) });
  const report = useQuery({ queryKey: ['manual-report', range[0].format('YYYY-MM-DD'), range[1].format('YYYY-MM-DD')], enabled: broad, queryFn: async ({ signal }) => readResult(await api.GET('/events/manual-report', { params: { query: { from: range[0].format('YYYY-MM-DD'), to: range[1].format('YYYY-MM-DD') } }, signal })) });
  async function download() {
    if (busy) return; setBusy(true); setError('');
    try {
      const result = await api.GET('/events/export', { params: { query: { from_ts: query.from_ts, to_ts: query.to_ts, gate_id: gate, result: query.result } }, parseAs: 'blob' });
      if (!result.response.ok || !result.data) throw new HttpError(result.response.status, result.error?.error.message || 'Không tải được CSV.');
      const url = URL.createObjectURL(result.data); const link = document.createElement('a'); link.href = url; link.download = 'su-kien.csv'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (failure) { setError(requestMessage(failure)); } finally { setBusy(false); }
  }
  const content = <><Space wrap className="section-actions"><DatePicker.RangePicker showTime format="DD/MM/YYYY HH:mm" aria-label="Khoảng thời gian sự kiện" allowClear={false} value={range} onChange={value => { if (value?.[0] && value[1]) { setRange([value[0], value[1]]); setPage(1); } }} />{broad && <Select aria-label="Cửa sự kiện" style={{ width: 170 }} placeholder="Tất cả cửa" allowClear value={gate} options={gates.data?.map(row => ({ value: row.id, label: row.name }))} onChange={value => { setGate(value); setPage(1); }} />}<Select aria-label="Kết quả sự kiện" style={{ minWidth: 190 }} mode="multiple" placeholder="Kết quả" value={results} options={Object.keys(statusMaps['recognition_event.result']).map(value => ({ value, label: statusInfo('recognition_event.result', value).label }))} onChange={value => { setResults(value); setPage(1); }} /><Select aria-label="Nhân viên sự kiện" style={{ width: 230 }} showSearch optionFilterProp="label" placeholder="Nhân viên" allowClear value={employee} options={employees.data?.map(row => ({ value: row.id, label: `${row.code} · ${row.full_name}` }))} onChange={value => { setEmployee(value); setPage(1); }} />{broad && <Select aria-label="Người chấm hộ" style={{ width: 220 }} allowClear placeholder="Người chấm hộ" value={performer} options={report.data?.map(row => ({ value: row.performed_by.id, label: row.performed_by.full_name }))} onChange={value => { setPerformer(value); setPage(1); }} />}{broad && <Tooltip title={employee || performer ? 'CSV hỗ trợ thời gian, cửa và kết quả; bỏ lọc nhân viên/người chấm để xuất.' : undefined}><span><Button disabled={!!employee || !!performer} loading={busy} onClick={() => void download()}>Xuất CSV</Button></span></Tooltip>}</Space>
    <QueryState query={employees} /><QueryState query={events} />{error && <Alert type="error" role="alert" message={error} />}<Table rowKey="id" dataSource={events.data?.items} scroll={{ x: 1450 }} pagination={{ current: page, pageSize: 20, total: events.data?.total, showSizeChanger: false, onChange: setPage }} columns={[
      { title: 'Thời gian', render: (_, row: Event) => dateTime(row.occurred_at) }, { title: 'Cửa / thiết bị', render: (_, row: Event) => <>{row.gate.name}<p className="muted">{row.device_id?.slice(0, 8) || '—'}</p></> },
      { title: 'Kết quả', render: (_, row: Event) => <StatusPill domain="recognition_event.result" value={row.result} /> }, { title: 'Nhân viên', render: (_, row: Event) => row.employee ? `${row.employee.code} · ${row.employee.full_name}` : '—' },
      { title: 'Điểm / ngưỡng', render: (_, row: Event) => <>{cos(row.top1_score)} / {cos(row.threshold_used)}<p className="muted">{row.threshold_level ? statusInfo('threshold.level', row.threshold_level).label : '—'}</p></> }, { title: 'Khung', dataIndex: 'n_frames' },
      { title: 'Người thực hiện / lý do', render: (_, row: Event) => <>{row.performed_by || '—'}<p>{row.reason || '—'}</p></> },
      { title: 'Xử lý', render: (_, row: Event) => <>{row.handling && <><StatusPill domain="event_handling.status" value={row.handling.status} /><p>{row.handling.note}</p></>}{broad && row.has_snapshot && <Button onClick={() => setSnapshot(row.id)}>Xem ảnh cảnh báo</Button>}</> },
    ]} /></>;
  return <><PageHero title="Sự kiện" description="Lịch sử ra vào và các thao tác thủ công; dữ liệu được lọc theo quyền trên máy chủ." /><section className="content-panel"><Tabs items={[{ key: 'events', label: 'Tra cứu sự kiện', children: content }, ...(broad ? [{ key: 'manual', label: 'Báo cáo chấm công hộ', children: <><DatePicker.RangePicker aria-label="Khoảng ngày báo cáo chấm hộ" format="DD/MM/YYYY" allowClear={false} value={range} onChange={value => { if (value?.[0] && value[1]) setRange([value[0].startOf('day'), value[1].endOf('day')]); }} /><p className="muted">Số lượt và số nhân viên khác nhau hỗ trợ đối chiếu; không tự kết luận vi phạm.</p><QueryState query={report} /><Table rowKey={row => row.performed_by.id} dataSource={report.data} columns={[{ title: 'Người chấm', render: (_, row: components['schemas']['ManualReportRow']) => row.performed_by.full_name }, { title: 'Số lượt', dataIndex: 'count' }, { title: 'Số nhân viên khác nhau', dataIndex: 'distinct_employees' }]} /></> }] : [])]} /></section><Modal open={!!snapshot} title="Ảnh cảnh báo" onCancel={() => setSnapshot(undefined)} footer={<Button onClick={() => setSnapshot(undefined)}>Đóng</Button>}>{snapshot && <EventSnapshot id={snapshot} size={320} />}</Modal></>;
}

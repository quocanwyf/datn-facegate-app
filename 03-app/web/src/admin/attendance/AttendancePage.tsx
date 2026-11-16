import { useMemo, useRef, useState } from 'react';
import { Alert, Button, DatePicker, Descriptions, Drawer, Form, Input, Modal, Select, Space, Table, Tooltip } from 'antd';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs, { type Dayjs } from 'dayjs';
import { useLocation, useNavigate } from 'react-router-dom';
import { api, type Session } from '../../api/client';
import { HttpError, readResult, requestMessage } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { QueryState } from '../../components/QueryState';
import { StatusPill } from '../../components/StatusPill';
import { statusInfo } from '../../theme/status';
import { dateTime } from '../../shared/format';
import { companyDate } from '../../shared/companyDate';
import { allDays, allEmployees, dayMark, workStatuses, type Day, type Employee } from './data';

export function AttendancePage({ session }: { session: Session }) {
  const client = useQueryClient(); const navigate = useNavigate(); const location = useLocation();
  const employeeFilter = new URLSearchParams(location.search).get('employee_id') || undefined;
  const [month, setMonth] = useState(companyDate().startOf('month')); const [department, setDepartment] = useState<string>(); const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Day>(); const [edit, setEdit] = useState(false); const [leave, setLeave] = useState(false);
  const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [busy, setBusy] = useState(false); const lock = useRef(false);
  const [editForm] = Form.useForm<{ check_in_at?: Dayjs | null; check_out_at?: Dayjs | null; reason: string }>();
  const [leaveForm] = Form.useForm<{ employee_id: string; dates: Dayjs[]; reason: string }>();
  const write = session.user.roles.some(grant => ['OWNER', 'HR'].includes(grant.role));
  const start = month.format('YYYY-MM-DD'), end = month.endOf('month').format('YYYY-MM-DD');
  const days = useQuery({ queryKey: ['attendance', start, end, department, employeeFilter], queryFn: ({ signal }) => allDays(start, end, department, employeeFilter, signal) });
  const employees = useQuery({ queryKey: ['attendance-employees', session.user.id], queryFn: ({ signal }) => allEmployees(signal) });
  const departments = useQuery({ queryKey: ['departments'], queryFn: async ({ signal }) => readResult(await api.GET('/departments', { signal })) });
  const index = useMemo(() => new Map(days.data?.map(day => [`${day.employee.id}/${day.work_date}`, day])), [days.data]);
  const people = employees.data?.filter(row => (!department || row.department_id === department) && (!employeeFilter || row.id === employeeFilter) && `${row.code} ${row.full_name}`.toLocaleLowerCase('vi').includes(search.toLocaleLowerCase('vi')));
  async function run(action: () => Promise<void>) {
    if (lock.current) return; lock.current = true; setBusy(true); setError(''); setNotice('');
    try { await action(); } catch (failure) { setError(requestMessage(failure)); }
    finally { lock.current = false; setBusy(false); }
  }
  function openEdit() {
    if (!selected || selected.employee.id === session.user.employee?.id || !write) return;
    editForm.setFieldsValue({ check_in_at: selected.check_in_at ? companyDate(selected.check_in_at) : null, check_out_at: selected.check_out_at ? companyDate(selected.check_out_at) : null, reason: '' }); setError(''); setEdit(true);
  }
  async function download() {
    const result = await api.GET('/attendance/export', { params: { query: { month: month.format('YYYY-MM'), department_id: department } }, parseAs: 'blob' });
    if (!result.response.ok || !result.data) {
      throw new HttpError(result.response.status, result.error?.error.message || 'Không tải được bảng công.', result.error?.error.code);
    }
    const url = URL.createObjectURL(result.data); const link = document.createElement('a'); link.href = url; link.download = `bang-cong-${month.format('YYYY-MM')}.xlsx`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <><PageHero title={`Bảng công tháng ${month.format('MM/YYYY')}`} description="Ngày chưa chốt mang trạng thái tạm thời. Giờ hiển thị theo múi giờ công ty." />
    {notice && <Alert role="status" type="success" className="feedback" message={notice} />}{error && !edit && !leave && <Alert role="alert" type="error" className="feedback" message={error} />}
    <section className="content-panel"><Space wrap className="section-actions"><DatePicker aria-label="Tháng bảng công" picker="month" format="MM/YYYY" value={month} allowClear={false} disabled={busy} onChange={value => { if (value) { setMonth(value.startOf('month')); setSelected(undefined); } }} /><Select aria-label="Phòng ban bảng công" placeholder="Tất cả phòng ban" style={{ width: 220 }} allowClear value={department} disabled={busy} options={departments.data?.map(row => ({ value: row.id, label: row.name }))} onChange={setDepartment} /><Input aria-label="Tìm nhân viên bảng công" placeholder="Tìm mã hoặc họ tên" value={search} onChange={event => setSearch(event.target.value)} />{write && <Button disabled={busy} onClick={() => { leaveForm.resetFields(); setError(''); setLeave(true); }}>Đánh dấu nghỉ</Button>}<Button type="primary" loading={busy && !edit && !leave} onClick={() => void run(download)}>Xuất Excel</Button></Space>
      <QueryState query={departments} /><QueryState query={employees} /><QueryState query={days} />
      <Table rowKey="id" className="attendance-table" dataSource={people} pagination={{ pageSize: 20, showSizeChanger: false }} scroll={{ x: 1550 }} columns={[
        { title: 'Mã NV', dataIndex: 'code', fixed: 'left', width: 90 }, { title: 'Họ tên', dataIndex: 'full_name', fixed: 'left', width: 180 },
        ...Array.from({ length: month.daysInMonth() }, (_, indexOfDay) => { const date = month.date(indexOfDay + 1).format('YYYY-MM-DD'); return { title: String(indexOfDay + 1), key: date, width: 40, render: (_: unknown, employee: Employee) => { const day = index.get(`${employee.id}/${date}`); const info = statusInfo('attendance_day.status', day?.status); return <Tooltip title={`${dayjs(date).format('DD/MM/YYYY')} · ${day ? info.label : 'Chưa có ngày công'}`}><button className="attendance-cell" disabled={!day || busy} style={{ background: info.bg, color: info.fg }} aria-label={`${employee.code} ${date} ${day ? info.label : 'Chưa có ngày công'}`} onClick={() => { setSelected(day); setError(''); }}>{day ? dayMark[day.status] : '—'}</button></Tooltip>; } }; }),
        { title: 'Ngày công', width: 95, render: (_, employee: Employee) => days.data?.filter(day => day.employee.id === employee.id && workStatuses.has(day.status)).length ?? 0 },
        { title: 'Lần muộn', width: 95, render: (_, employee: Employee) => days.data?.filter(day => day.employee.id === employee.id && (day.late_min > 0 || ['LATE', 'LATE_EARLY'].includes(day.status))).length ?? 0 },
        { title: 'Phút muộn', width: 100, render: (_, employee: Employee) => days.data?.filter(day => day.employee.id === employee.id).reduce((sum, day) => sum + day.late_min, 0) ?? 0 },
      ]} />
      <div className="attendance-legend">{Object.entries(dayMark).map(([value, mark]) => { const info = statusInfo('attendance_day.status', value); return <span key={value}><i style={{ background: info.bg, color: info.fg }}>{mark}</i>{info.label}</span>; })}</div>
    </section>
    <Drawer width={480} title="Chi tiết ngày công" open={!!selected} onClose={() => { if (!busy) { setSelected(undefined); setEdit(false); } }} maskClosable={!busy}>
      {selected && <><h2>{selected.employee.full_name}</h2><p>{selected.work_date.split('-').reverse().join('/')} · {selected.shift?.name || 'Không có ca'}</p><StatusPill domain="attendance_day.status" value={selected.status} />{!selected.finalized && <Alert type="info" className="feedback" message="Ngày công chưa chốt — kết quả tạm thời" />}<Descriptions column={1} items={[{ key: 'in', label: 'Giờ vào', children: dateTime(selected.check_in_at) }, { key: 'out', label: 'Giờ ra', children: dateTime(selected.check_out_at) }, { key: 'late', label: 'Muộn / về sớm', children: `${selected.late_min} / ${selected.early_min} phút` }, { key: 'worked', label: 'Thời gian trong ca', children: `${selected.worked_min} phút` }, { key: 'source', label: 'Nguồn', children: <StatusPill domain="attendance_day.source" value={selected.source} /> }, { key: 'reason', label: 'Ghi chú', children: selected.edit_reason || '—' }]} />{selected.suspect_forgot_out && <Alert type="warning" message="Có thể quên quét khi quay lại sau giờ nghỉ." />}<Space className="section-actions">{write && selected.employee.id !== session.user.employee?.id && <Button onClick={openEdit}>Sửa ngày công</Button>}<Button onClick={() => navigate(`/admin/events?employee_id=${selected.employee.id}&date=${selected.work_date}`)}>Lịch sử sự kiện</Button></Space></>}
    </Drawer>
    <Modal open={edit} title="Sửa ngày công" okText="Lưu ngày công" cancelText="Hủy" confirmLoading={busy} closable={!busy} maskClosable={!busy} cancelButtonProps={{ disabled: busy }} onCancel={() => setEdit(false)} onOk={() => editForm.submit()}>{error && <Alert role="alert" type="error" message={error} />}<Form form={editForm} layout="vertical" disabled={busy} onFinish={values => void run(async () => { if (!selected) return; const changed = readResult(await api.PATCH('/attendance/days/{id}', { params: { path: { id: selected.id } }, body: { check_in_at: values.check_in_at?.toISOString() ?? null, check_out_at: values.check_out_at?.toISOString() ?? null, reason: values.reason } })); setSelected(changed); setEdit(false); setNotice('Đã sửa ngày công'); await client.invalidateQueries({ queryKey: ['attendance'] }); })}><Form.Item name="check_in_at" label="Giờ vào"><DatePicker showTime={{ format: 'HH:mm' }} format="DD/MM/YYYY HH:mm" /></Form.Item><Form.Item name="check_out_at" label="Giờ ra"><DatePicker showTime={{ format: 'HH:mm' }} format="DD/MM/YYYY HH:mm" /></Form.Item><Form.Item name="reason" label="Lý do sửa" rules={[{ required: true, whitespace: true }]}><Input.TextArea rows={3} /></Form.Item></Form></Modal>
    <Modal open={leave} title="Đánh dấu nghỉ phép" okText="Lưu nghỉ phép" cancelText="Hủy" confirmLoading={busy} closable={!busy} maskClosable={!busy} cancelButtonProps={{ disabled: busy }} onCancel={() => setLeave(false)} onOk={() => leaveForm.submit()}>{error && <Alert role="alert" type="error" message={error} />}<Form form={leaveForm} layout="vertical" disabled={busy} onFinish={values => void run(async () => { readResult(await api.POST('/attendance/leave', { body: { employee_id: values.employee_id, dates: values.dates.map(value => value.format('YYYY-MM-DD')), reason: values.reason } })); setLeave(false); setNotice('Đã đánh dấu nghỉ phép'); await client.invalidateQueries({ queryKey: ['attendance'] }); })}><Form.Item name="employee_id" label="Nhân viên nghỉ phép" rules={[{ required: true }]}><Select showSearch optionFilterProp="label" options={employees.data?.map(row => ({ value: row.id, label: `${row.code} · ${row.full_name}` }))} /></Form.Item><Form.Item name="dates" label="Các ngày nghỉ" rules={[{ required: true }]}><DatePicker multiple format="DD/MM/YYYY" /></Form.Item><Form.Item name="reason" label="Lý do nghỉ" rules={[{ required: true, whitespace: true }]}><Input.TextArea rows={3} /></Form.Item></Form></Modal>
  </>;
}

import { useRef, useState } from 'react';
import { Alert, Button, DatePicker, Drawer, Empty, Form, Input, InputNumber, Modal, Segmented, Select, Space, Table, Tabs, TimePicker } from 'antd';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs, { type Dayjs } from 'dayjs';
import { api } from '../../api/client';
import type { components } from '../../api/schema';
import { HttpError, readResult, requestMessage } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { QueryState } from '../../components/QueryState';
import { allEmployees } from '../attendance/data';
import { companyDate } from '../../shared/companyDate';

type Shift = components['schemas']['Shift'];
type ShiftForm = Omit<components['schemas']['ShiftInput'], 'start_time' | 'end_time' | 'break_start' | 'break_end'> & { start_time: Dayjs; end_time: Dayjs; break_start?: Dayjs | null; break_end?: Dayjs | null };
type AssignmentForm = { shift_id: string; weekdays: number[]; effective_from: Dayjs; effective_to?: Dayjs | null };
const weekdays = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'];

export function SchedulesPage() {
  const client = useQueryClient(); const lock = useRef(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [notice, setNotice] = useState('');
  const [editor, setEditor] = useState<Shift | 'new' | null>(null); const [assign, setAssign] = useState(false); const [holiday, setHoliday] = useState(false);
  const [year, setYear] = useState(companyDate().year()); const [kind, setKind] = useState('department'); const [target, setTarget] = useState<string>();
  const [shiftForm] = Form.useForm<ShiftForm>(); const [assignmentForm] = Form.useForm<AssignmentForm>(); const [holidayForm] = Form.useForm<{ date: Dayjs; name: string }>();
  const shifts = useQuery({ queryKey: ['shifts'], queryFn: async ({ signal }) => readResult(await api.GET('/shifts', { signal })) });
  const departments = useQuery({ queryKey: ['departments'], queryFn: async ({ signal }) => readResult(await api.GET('/departments', { signal })) });
  const employees = useQuery({ queryKey: ['schedule-employees'], queryFn: ({ signal }) => allEmployees(signal) });
  const assignments = useQuery({ queryKey: ['assignments', kind, target], enabled: !!target, queryFn: async ({ signal }) => readResult(await api.GET('/shift-assignments', { params: { query: kind === 'department' ? { department_id: target } : { employee_id: target } }, signal })) });
  const holidays = useQuery({ queryKey: ['holidays', year], queryFn: async ({ signal }) => readResult(await api.GET('/holidays', { params: { query: { year } }, signal })) });
  async function run(action: () => Promise<void>) {
    if (lock.current) return; lock.current = true; setBusy(true); setError(''); setNotice('');
    try { await action(); setNotice('Đã lưu thay đổi'); await Promise.all(['shifts', 'assignments', 'holidays', 'attendance'].map(key => client.invalidateQueries({ queryKey: [key] }))); }
    catch (failure) { setError(failure instanceof HttpError && failure.code === 'ASSIGNMENT_OVERLAP' ? 'Đã có phân ca trùng thời gian cho thứ này' : requestMessage(failure)); }
    finally { lock.current = false; setBusy(false); }
  }
  function edit(shift: Shift | 'new') {
    setError(''); shiftForm.resetFields(); setEditor(shift);
    if (shift !== 'new') shiftForm.setFieldsValue({ ...shift, start_time: dayjs(`2000-01-01T${shift.start_time}`), end_time: dayjs(`2000-01-01T${shift.end_time}`), break_start: shift.break_start ? dayjs(`2000-01-01T${shift.break_start}`) : null, break_end: shift.break_end ? dayjs(`2000-01-01T${shift.break_end}`) : null });
  }
  const options = kind === 'department' ? departments.data?.map(row => ({ value: row.id, label: row.name })) : employees.data?.map(row => ({ value: row.id, label: `${row.code} · ${row.full_name}` }));
  return <><PageHero title="Ca & lịch" description="Ca làm việc, phân ca theo thứ và ngày lễ toàn công ty." />
    {error && !editor && !assign && !holiday && <Alert role="alert" type="error" message={error} />}{notice && <Alert className="feedback" role="status" type="success" message={notice} />}
    <section className="content-panel"><Tabs items={[
      { key: 'shifts', label: 'Ca', children: <><Button type="primary" onClick={() => edit('new')}>Thêm ca</Button><QueryState query={shifts} /><Table rowKey="id" dataSource={shifts.data} pagination={false} columns={[{ title: 'Tên ca', dataIndex: 'name' }, { title: 'Giờ làm', render: (_, row: Shift) => `${row.start_time}–${row.end_time}` }, { title: 'Nghỉ', render: (_, row: Shift) => row.break_start ? `${row.break_start}–${row.break_end}` : '—' }, { title: 'Cho phép muộn / sớm', render: (_, row: Shift) => `${row.grace_in_min} / ${row.grace_out_min} phút` }, { title: 'Thao tác', render: (_, row: Shift) => <Button onClick={() => edit(row)} aria-label={`Sửa ca ${row.name}`}>Sửa</Button> }]} /></> },
      { key: 'assignments', label: 'Phân ca', children: <><Space wrap className="section-actions"><Segmented aria-label="Loại đối tượng phân ca" options={[{ label: 'Phòng ban', value: 'department' }, { label: 'Nhân viên', value: 'employee' }]} value={kind} disabled={busy} onChange={value => { setKind(value); setTarget(undefined); }} /><Select aria-label="Đối tượng phân ca" showSearch optionFilterProp="label" style={{ width: 300 }} options={options} value={target} disabled={busy} placeholder="Chọn đối tượng" onChange={setTarget} /><Button type="primary" disabled={!target || busy} onClick={() => { setError(''); assignmentForm.resetFields(); setAssign(true); }}>Thêm phân ca</Button></Space><QueryState query={kind === 'department' ? departments : employees} />{target ? <><QueryState query={assignments} /><div className="week-grid">{weekdays.map((label, index) => <section className="week-column" key={label}><h3>{label}</h3>{assignments.data?.filter(row => row.weekday === index + 1).map(row => <article className="assignment-card" key={row.id}><b>{row.shift_name}</b><p>{dayjs(row.effective_from).format('DD/MM/YYYY')} → {row.effective_to ? dayjs(row.effective_to).format('DD/MM/YYYY') : 'Không giới hạn'}</p><Button danger size="small" disabled={busy} onClick={() => Modal.confirm({ title: 'Xóa phân ca?', content: `${label} · ${row.shift_name}`, okText: 'Xóa phân ca', cancelText: 'Hủy', onOk: () => run(async () => { readResult(await api.DELETE('/shift-assignments/{id}', { params: { path: { id: row.id } } })); }) })}>Xóa</Button></article>)}</section>)}</div></> : <Empty description="Chọn phòng ban hoặc nhân viên để xem lịch." />}</> },
      { key: 'holidays', label: 'Ngày lễ', children: <><Space wrap><InputNumber aria-label="Năm ngày lễ" value={year} min={1900} max={9998} onChange={value => { if (value) setYear(value); }} /><Button type="primary" onClick={() => { holidayForm.resetFields(); setError(''); setHoliday(true); }}>Thêm ngày lễ</Button></Space><QueryState query={holidays} /><Table rowKey="date" pagination={false} dataSource={holidays.data} columns={[{ title: 'Ngày', dataIndex: 'date', render: value => dayjs(value).format('DD/MM/YYYY') }, { title: 'Tên ngày lễ', dataIndex: 'name' }, { title: 'Thao tác', render: (_, row: components['schemas']['Holiday']) => <Button danger disabled={busy} onClick={() => Modal.confirm({ title: `Xóa ngày lễ ${row.name}?`, okText: 'Xóa ngày lễ', cancelText: 'Hủy', onOk: () => run(async () => { readResult(await api.DELETE('/holidays/{date}', { params: { path: { date: row.date } } })); }) })}>Xóa</Button> }]} /></> },
    ]} /></section>
    <Drawer width={480} title={editor === 'new' ? 'Thêm ca' : 'Sửa ca'} open={!!editor} onClose={() => { if (!busy) setEditor(null); }} maskClosable={!busy} footer={<Button type="primary" loading={busy} onClick={() => shiftForm.submit()}>Lưu ca</Button>}>
      {error && <Alert role="alert" type="error" message={error} />}<Form form={shiftForm} layout="vertical" disabled={busy} initialValues={{ grace_in_min: 5, grace_out_min: 5 }} onFinish={values => void run(async () => {
        const start = values.start_time.hour() * 60 + values.start_time.minute(), end = values.end_time.hour() * 60 + values.end_time.minute();
        if (end <= start || end - start > 17 * 60) { shiftForm.setFields([{ name: 'end_time', errors: ['Giờ kết thúc phải sau giờ bắt đầu, ca tối đa 17 giờ.'] }]); throw new HttpError(422, 'Giờ kết thúc phải sau giờ bắt đầu, ca tối đa 17 giờ.'); }
        const body = { ...values, start_time: values.start_time.format('HH:mm'), end_time: values.end_time.format('HH:mm'), break_start: values.break_start?.format('HH:mm') ?? null, break_end: values.break_end?.format('HH:mm') ?? null };
        if (editor === 'new') readResult(await api.POST('/shifts', { body })); else if (editor) readResult(await api.PATCH('/shifts/{id}', { params: { path: { id: editor.id } }, body })); setEditor(null);
      })}><Form.Item name="name" label="Tên ca" rules={[{ required: true, whitespace: true }]}><Input /></Form.Item>{(['start_time', 'end_time', 'break_start', 'break_end'] as const).map((name, index) => <Form.Item key={name} name={name} label={['Giờ bắt đầu', 'Giờ kết thúc', 'Bắt đầu nghỉ', 'Kết thúc nghỉ'][index]} rules={[{ required: index < 2 }]}><TimePicker format="HH:mm" needConfirm={false} /></Form.Item>)}<Form.Item name="grace_in_min" label="Cho phép muộn (phút)"><InputNumber min={0} max={120} /></Form.Item><Form.Item name="grace_out_min" label="Cho phép sớm (phút)"><InputNumber min={0} max={120} /></Form.Item></Form>
    </Drawer>
    <Modal open={assign} title="Thêm phân ca" okText="Lưu phân ca" cancelText="Hủy" confirmLoading={busy} closable={!busy} maskClosable={!busy} cancelButtonProps={{ disabled: busy }} onCancel={() => setAssign(false)} onOk={() => assignmentForm.submit()}>
      {error && <Alert role="alert" type="error" message={error} />}<Form form={assignmentForm} layout="vertical" disabled={busy} onFinish={values => void run(async () => { if (!target) return; readResult(await api.POST('/shift-assignments', { body: { shift_id: values.shift_id, weekdays: values.weekdays, effective_from: values.effective_from.format('YYYY-MM-DD'), effective_to: values.effective_to?.format('YYYY-MM-DD') ?? null, ...(kind === 'department' ? { department_id: target } : { employee_id: target }) } })); setAssign(false); })}><Form.Item name="shift_id" label="Ca làm việc" rules={[{ required: true }]}><Select options={shifts.data?.map(row => ({ value: row.id, label: row.name }))} /></Form.Item><Form.Item name="weekdays" label="Các thứ" rules={[{ required: true, type: 'array', min: 1 }]}><Select mode="multiple" options={weekdays.map((label, index) => ({ label, value: index + 1 }))} /></Form.Item><Form.Item name="effective_from" label="Hiệu lực từ" rules={[{ required: true }]}><DatePicker format="DD/MM/YYYY" /></Form.Item><Form.Item name="effective_to" label="Hiệu lực đến"><DatePicker format="DD/MM/YYYY" /></Form.Item></Form>
    </Modal>
    <Modal open={holiday} title="Thêm ngày lễ" okText="Lưu ngày lễ" cancelText="Hủy" confirmLoading={busy} closable={!busy} maskClosable={!busy} cancelButtonProps={{ disabled: busy }} onCancel={() => setHoliday(false)} onOk={() => holidayForm.submit()}>{error && <Alert role="alert" type="error" message={error} />}<Form form={holidayForm} layout="vertical" disabled={busy} onFinish={values => void run(async () => { const selected = values.date; readResult(await api.POST('/holidays', { body: { date: selected.format('YYYY-MM-DD'), name: values.name } })); setYear(selected.year()); setHoliday(false); })}><Form.Item name="date" label="Ngày nghỉ lễ" rules={[{ required: true }]}><DatePicker format="DD/MM/YYYY" /></Form.Item><Form.Item name="name" label="Tên ngày lễ" rules={[{ required: true, whitespace: true }]}><Input /></Form.Item></Form></Modal>
  </>;
}

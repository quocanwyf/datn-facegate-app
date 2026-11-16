import { useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Button, Empty, Form, Input, Modal, Pagination, Select, Space } from 'antd';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { api, type Session } from '../../api/client';
import type { components } from '../../api/schema';
import { readResult, requestMessage } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { QueryState } from '../../components/QueryState';
import { StatusPill } from '../../components/StatusPill';
import { cos, dateTime } from '../../shared/format';
import { allEmployees } from '../attendance/data';
import { useMonitor, type Event } from './MonitorProvider';
import { EventSnapshot } from './EventSnapshot';

gsap.registerPlugin(useGSAP);
type QuickForm = { gate_id: string; employee_id?: string; reason: string };
type HandleForm = components['schemas']['EventHandleInput'];
function mergeEvents(...groups: Event[][]) {
  const result = new Map<string, Event>();
  for (const row of groups.flat()) { const previous = result.get(row.id); result.set(row.id, { ...row, handling: row.handling ?? previous?.handling }); }
  return [...result.values()].sort((a, b) => Date.parse(b.occurred_at) - Date.parse(a.occurred_at));
}

export function MonitorPage({ session }: { session: Session }) {
  const stream = useMonitor(); const client = useQueryClient(); const root = useRef<HTMLDivElement>(null);
  const [action, setAction] = useState<'open' | 'attendance'>('attendance'); const [alert, setAlert] = useState<Event>(); const [alertPage, setAlertPage] = useState(1);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const lock = useRef(false);
  const [sound, setSound] = useState(false); const audio = useRef<AudioContext>(); const lastSound = useRef('');
  const [quick] = Form.useForm<QuickForm>(); const [handle] = Form.useForm<HandleForm>(); const handlingStatus = Form.useWatch('status', handle);
  const roles = session.user.roles.map(role => role.role); const operate = roles.some(role => ['OWNER', 'SECURITY'].includes(role));
  const gates = useQuery({ queryKey: ['gates'], queryFn: async ({ signal }) => readResult(await api.GET('/gates', { signal })) });
  const people = useQuery({ queryKey: ['monitor-employees', session.user.id], queryFn: ({ signal }) => allEmployees(signal) });
  const recent = useQuery({ queryKey: ['recent-events', 20], queryFn: async ({ signal }) => readResult(await api.GET('/events', { params: { query: { page: 1, size: 20 } }, signal })) });
  const pending = useQuery({ queryKey: ['monitor-alerts'], queryFn: async ({ signal }) => {
    const items: Event[] = [];
    for (let page = 1; ; page++) { const result = readResult(await api.GET('/events', { params: { query: { result: ['UNKNOWN', 'SPOOF'], handled: false, page, size: 100 } }, signal })); items.push(...result.items); if (items.length >= result.total || !result.items.length) return items; }
  } });
  const events = useMemo(() => mergeEvents(recent.data?.items ?? [], stream.events).slice(0, 40), [recent.data, stream.events]);
  const alerts = useMemo(() => mergeEvents(pending.data ?? [], events).filter(row => ['UNKNOWN', 'SPOOF'].includes(row.result) && !row.handling), [pending.data, events]);
  const choices = useMemo(() => {
    const result = new Map<string, components['schemas']['EmployeeBrief']>();
    for (const row of people.data ?? []) result.set(row.id, row);
    // Tái sử dụng danh tính đã được phép thấy trong event; không mở thêm API hồ sơ.
    for (const row of events) if (row.employee && !result.has(row.employee.id)) result.set(row.employee.id, row.employee);
    return [...result.values()];
  }, [people.data, events]);
  const head = events[0];
  useGSAP(() => {
    const media = gsap.matchMedia(); media.add('(prefers-reduced-motion: no-preference)', () => {
      const element = root.current?.querySelector('.live-event'); if (!element) return;
      const timeline = gsap.timeline(); timeline.fromTo(element, { x: 16, autoAlpha: 0 }, { x: 0, autoAlpha: 1, duration: .25, clearProps: 'transform,opacity,visibility' });
      if (head?.result === 'SPOOF') timeline.to(element, { x: 5, duration: .05, repeat: 3, yoyo: true }).set(element, { clearProps: 'transform' });
    }); return () => media.revert();
  }, { scope: root, dependencies: [head?.id], revertOnUpdate: true });
  useEffect(() => {
    if (!sound || !head || lastSound.current === head.id || !['UNKNOWN', 'SPOOF'].includes(head.result) || !audio.current) return;
    lastSound.current = head.id;
    const oscillator = audio.current.createOscillator(), gain = audio.current.createGain(); gain.gain.value = .035;
    oscillator.frequency.value = head.result === 'SPOOF' ? 440 : 660; oscillator.connect(gain); gain.connect(audio.current.destination);
    oscillator.start(); oscillator.stop(audio.current.currentTime + .14);
  }, [head, sound]);
  useEffect(() => () => { void audio.current?.close(); }, []);
  async function run(callback: () => Promise<void>) {
    if (lock.current) return; lock.current = true; setBusy(true); setError(''); setNotice('');
    try { await callback(); await Promise.all(['events', 'recent-events', 'monitor-alerts', 'dashboard'].map(key => client.invalidateQueries({ queryKey: [key] }))); }
    catch (failure) { setError(requestMessage(failure)); } finally { lock.current = false; setBusy(false); }
  }
  return <div ref={root}><PageHero title="Giám sát" description="Luồng sự kiện và cảnh báo từ các cửa trong phạm vi được cấp quyền." action={<Button onClick={() => { if (!audio.current) audio.current = new AudioContext(); void audio.current.resume(); setSound(value => !value); }}>{sound ? 'Tắt âm cảnh báo' : 'Bật âm cảnh báo'}</Button>} />
    {stream.status !== 'online' && <Alert role="status" className="feedback" type={stream.status === 'offline' ? 'error' : 'info'} showIcon message={stream.status === 'offline' ? 'Mất kết nối thời gian thực — đang nối lại' : 'Đang kết nối giám sát thời gian thực…'} />}
    {notice && <Alert role="status" type="success" className="feedback" message={notice} />}{error && !alert && <Alert role="alert" type="error" className="feedback" message={error} />}
    <div className="monitor-grid"><section className="content-panel"><h2>Sự kiện mới nhất</h2><QueryState query={recent} />{!events.length && !recent.isPending && <Empty description="Chưa có sự kiện" />}{events.map(row => <article key={row.id} className="live-event" data-event-id={row.id}><Space wrap><b>{dateTime(row.occurred_at)}</b><span>{row.gate.name}</span><StatusPill domain="recognition_event.result" value={row.result} /></Space><h3>{row.employee?.full_name || (['UNKNOWN', 'SPOOF'].includes(row.result) ? 'Người lạ' : 'Thao tác thủ công')}</h3><p className="muted">{row.employee?.code || '—'} · Điểm {cos(row.top1_score)} · Ngưỡng {cos(row.threshold_used)}</p></article>)}</section>
    <div className="monitor-side"><section className="content-panel"><h2>Cảnh báo chưa xử lý · {alerts.length}</h2><QueryState query={pending} />{!alerts.length && !pending.isPending && <Empty description="Không có cảnh báo chưa xử lý" />}{alerts.slice((alertPage-1)*10, alertPage*10).map(row => <article key={row.id} className="alert-card" data-alert-id={row.id}>{row.has_snapshot && <EventSnapshot id={row.id} />}<div><StatusPill domain="recognition_event.result" value={row.result} /><p>{dateTime(row.occurred_at)} · {row.gate.name}</p>{operate && <Button type="primary" disabled={busy} onClick={() => { setError(''); handle.resetFields(); handle.setFieldValue('status', 'RESOLVED'); setAlert(row); }}>Xử lý</Button>}</div></article>)}<Pagination current={alertPage} total={alerts.length} pageSize={10} showSizeChanger={false} onChange={setAlertPage} /></section>
    <section className="content-panel"><h2>Thao tác nhanh</h2><QueryState query={gates} /><QueryState query={people} /><Space className="section-actions">{operate && <Button type={action === 'open' ? 'primary' : 'default'} disabled={busy} onClick={() => { setAction('open'); quick.resetFields(); }}>Mở cửa mô phỏng</Button>}<Button type={action === 'attendance' ? 'primary' : 'default'} disabled={busy} onClick={() => { setAction('attendance'); quick.resetFields(); }}>Chấm công hộ</Button></Space><Form form={quick} layout="vertical" disabled={busy} onFinish={values => void run(async () => {
      if (action === 'open') { readResult(await api.POST('/gates/{id}/manual-open', { params: { path: { id: values.gate_id } }, body: { reason: values.reason } })); setNotice('Đã ghi nhận mở cửa mô phỏng'); }
      else { if (!values.employee_id) return; readResult(await api.POST('/attendance/manual', { body: { employee_id: values.employee_id, gate_id: values.gate_id, reason: values.reason } })); setNotice('Đã ghi nhận chấm công hộ'); }
      quick.resetFields(['reason']);
    })}>{action === 'attendance' && <Form.Item name="employee_id" label="Nhân viên chấm hộ" rules={[{ required: true }]}><Select showSearch optionFilterProp="label" placeholder="Tìm mã hoặc tên" options={people.data?.filter(row => row.status === 'ACTIVE' && row.attendance_method === 'MANUAL' && row.id !== session.user.employee?.id).map(row => ({ value: row.id, label: `${row.code} · ${row.full_name}` }))} /></Form.Item>}<Form.Item name="gate_id" label="Cửa thao tác" rules={[{ required: true }]}><Select options={gates.data?.filter(row => row.is_active && (action === 'open' || row.mode === 'ATTENDANCE_ACCESS')).map(row => ({ value: row.id, label: row.name }))} /></Form.Item><Form.Item name="reason" label="Lý do thao tác" rules={[{ required: true, whitespace: true }]}><Input.TextArea rows={3} /></Form.Item><Button type="primary" htmlType="submit" loading={busy}>{action === 'open' ? 'Xác nhận mở mô phỏng' : 'Xác nhận chấm hộ'}</Button></Form></section></div></div>
    <Modal open={!!alert} title="Xử lý cảnh báo" okText="Lưu xử lý" cancelText="Hủy" confirmLoading={busy} closable={!busy} maskClosable={!busy} cancelButtonProps={{ disabled: busy }} onCancel={() => setAlert(undefined)} onOk={() => handle.submit()}>{error && <Alert role="alert" type="error" message={error} />}{alert?.has_snapshot && <EventSnapshot id={alert.id} size={280} />}<p>{alert && dateTime(alert.occurred_at)} · {alert?.gate.name}</p><Form form={handle} layout="vertical" disabled={busy} onFinish={values => void run(async () => { if (!alert) return; readResult(await api.POST('/events/{id}/handle', { params: { path: { id: alert.id } }, body: { status: values.status, linked_employee_id: values.status === 'IS_EMPLOYEE' ? values.linked_employee_id : null, note: values.note } })); setAlert(undefined); setNotice('Đã lưu xử lý cảnh báo'); })}><Form.Item name="status" label="Kết quả xử lý" rules={[{ required: true }]}><Select onChange={() => handle.setFieldValue('linked_employee_id', undefined)} options={[{ value: 'RESOLVED', label: 'Đã xử lý' }, { value: 'FALSE_ALARM', label: 'Báo động giả' }, { value: 'IS_EMPLOYEE', label: 'Là nhân viên' }]} /></Form.Item>{handlingStatus === 'IS_EMPLOYEE' && <Form.Item name="linked_employee_id" label="Nhân viên được xác nhận" rules={[{ required: true, message: 'Chọn nhân viên' }]}><Select showSearch optionFilterProp="label" options={choices.map(row => ({ value: row.id, label: `${row.code} · ${row.full_name}` }))} /></Form.Item>}<Form.Item name="note" label="Ghi chú xử lý"><Input.TextArea rows={3} /></Form.Item></Form><p className="muted">Không thêm ảnh này vào hồ sơ khuôn mặt.</p></Modal>
  </div>;
}

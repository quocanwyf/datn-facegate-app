import { useFormExitWarning } from '../../shared/useFormExitWarning';
import { AnimatedTable as Table } from '../../components/AnimatedTable';
import { useEffect, useRef, useState } from 'react';
import { Alert, Button, Empty, Form, Input, InputNumber, Modal, QRCode, Select, Space, Statistic, Switch } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { api, type Session } from '../../api/client';
import type { components } from '../../api/schema';
import { readResult, requestMessage } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { QueryState } from '../../components/QueryState';
import { StatusPill } from '../../components/StatusPill';
import { cos, dateTime } from '../../shared/format';
type Gate = components['schemas']['Gate'];
type Fields = components['schemas']['GateInput'] & { allowed_department_ids: string[] };
export function GatesPage({ session }: { session: Session }) {
  const owner = session.user.roles.some(grant => grant.role === 'OWNER');
  const gates = useQuery({ queryKey: ['gates'], queryFn: async () => readResult(await api.GET('/gates')) });
  const departments = useQuery({ queryKey: ['departments', session.user.id], queryFn: async () => readResult(await api.GET('/departments')) });
  const model = useQuery({ queryKey: ['model'], queryFn: async () => readResult(await api.GET('/models/active')) });
  const [selected, setSelected] = useState<string>(); const [creating, setCreating] = useState(false);
  const gate = gates.data?.find(item => item.id === selected) ?? gates.data?.[0];
  const devices = useQuery({ queryKey: ['devices', gate?.id], enabled: !!gate && owner, queryFn: async () => readResult(await api.GET('/devices', { params: { query: { gate_id: gate!.id } } })), refetchInterval: 15000 });
  const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [busy, setBusy] = useState(false); const locked = useRef(false);
  const [deviceName, setDeviceName] = useState<string>(); const [pairing, setPairing] = useState<components['schemas']['DevicePairing']>();
  const [revoke, setRevoke] = useState<components['schemas']['Device']>();
  const [form] = Form.useForm<Fields>(); const level = Form.useWatch('threshold_level', form); const policy = Form.useWatch('default_policy', form);
  useFormExitWarning(form);
  const selectedThreshold = model.data?.thresholds.find(item => item.level === level);
  useEffect(() => { form.resetFields(); form.setFieldsValue(creating ? { mode: 'ATTENDANCE_ACCESS', default_policy: 'ALLOW_ALL_ACTIVE', threshold_level: 'DEFAULT_VAL', is_active: true, allowed_department_ids: [] } : gate ?? {}); }, [gate, creating, form]);
  async function run(action: () => Promise<unknown>) { if (locked.current) return; locked.current = true; setBusy(true); setError(''); setNotice(''); try { await action(); await Promise.all([gates.refetch(), devices.refetch()]); } catch (failure) { setError(requestMessage(failure)); } finally { locked.current = false; setBusy(false); } }
  async function save(values: Fields) { await run(async () => {
    // HR chỉ gửi chính sách; không gửi những trường chỉ OWNER được sửa.
    const body: components['schemas']['GateInput'] = owner ? { name: values.name, mode: values.mode, default_policy: values.default_policy, threshold_level: values.threshold_level, custom_threshold: values.threshold_level === 'CUSTOM' ? values.custom_threshold : null, is_active: values.is_active } : { default_policy: values.default_policy };
    const updated: Gate = creating ? readResult(await api.POST('/gates', { body })) : readResult(await api.PATCH('/gates/{id}', { params: { path: { id: gate!.id } }, body }));
    readResult(await api.PUT('/gates/{id}/allowed-departments', { params: { path: { id: updated.id } }, body: { department_ids: values.allowed_department_ids ?? [] } }));
    setSelected(updated.id); setCreating(false); setNotice('Đã lưu cửa và chính sách');
  }); }
  return <><PageHero title="Cửa & thiết bị" description="Quản lý chính sách ra vào và ghép Kiosk." action={owner && <Button type="primary" onClick={() => { setCreating(true); setError(''); }}>Thêm cửa</Button>} />
    {!owner && <Alert className="feedback" type="info" message="Bạn chỉ được sửa chính sách và phòng ban được phép." />}{error && <Alert className="feedback" type="error" role="alert" message={error} />}{notice && <Alert className="feedback" type="success" role="status" message={notice} />}
    <QueryState query={gates} /><div className="split-layout"><section className="content-panel"><h2>Danh sách cửa</h2>{gates.data?.map(item => <button className={`selection-card ${!creating && gate?.id === item.id ? 'selected' : ''}`} key={item.id} disabled={busy} onClick={() => { setSelected(item.id); setCreating(false); setNotice(''); }}><b>{item.name}</b><Space wrap><StatusPill domain="gate.mode" value={item.mode} /><StatusPill domain="threshold.level" value={item.threshold_level} /></Space><span>{item.devices_online ?? 0}/{item.devices_total ?? 0} thiết bị trực tuyến</span></button>)}</section>
      <section className="content-panel">{gate || creating ? <><h2>{creating ? 'Cửa mới' : gate?.name}</h2><Form autoComplete="off" scrollToFirstError form={form} layout="vertical" disabled={busy} onFinish={values => void save(values)}>
        <Form.Item name="name" label="Tên cửa" rules={[{ required: true, whitespace: true, message: 'Nhập tên cửa' }]}><Input disabled={!owner || busy} /></Form.Item>
        <Form.Item name="mode" label="Chế độ"><Select disabled={!owner || busy} options={[{ value: 'ATTENDANCE_ACCESS', label: 'Chấm công + ra vào' }, { value: 'ACCESS_ONLY', label: 'Chỉ ra vào' }]} /></Form.Item>
        <Form.Item name="default_policy" label="Chính sách"><Select options={[{ value: 'ALLOW_ALL_ACTIVE', label: 'Mọi nhân viên đang làm việc' }, { value: 'DEPARTMENTS_ONLY', label: 'Chỉ phòng ban được phép' }]} /></Form.Item>
        {policy === 'DEPARTMENTS_ONLY' && <Form.Item name="allowed_department_ids" label="Phòng ban được phép"><Select mode="multiple" options={departments.data?.map(item => ({ value: item.id, label: item.name }))} /></Form.Item>}
        <Form.Item name="threshold_level" label="Mức ngưỡng"><Select disabled={!owner || busy} options={[{ value: 'DEFAULT_VAL', label: 'Mặc định' }, { value: 'STRICT_TEST', label: 'Nghiêm ngặt' }, { value: 'CUSTOM', label: 'Tuỳ chỉnh' }]} /></Form.Item>
        {level === 'CUSTOM' ? <Form.Item name="custom_threshold" label="Ngưỡng cos tuỳ chỉnh" rules={[{ required: true, message: 'Nhập ngưỡng từ -1 đến 1' }]}><InputNumber min={-1} max={1} step={0.0001} disabled={!owner || busy} /></Form.Item> : <p className="muted">Cos {cos(selectedThreshold?.cos_threshold)} · {selectedThreshold?.label}<br />Nguồn: {selectedThreshold?.source_ref}</p>}
        <Form.Item name="is_active" valuePropName="checked" label="Cửa hoạt động"><Switch disabled={!owner || busy} /></Form.Item><Button type="primary" htmlType="submit" loading={busy}>Lưu cửa</Button>
      </Form>{!creating && owner && <><div className="panel-heading section-actions"><h2>Thiết bị</h2>{owner && <Button onClick={() => setDeviceName('')}>Thêm thiết bị</Button>}</div><QueryState query={devices} /><Table rowKey="id" dataSource={devices.data} pagination={false} scroll={{ x: 600 }} columns={[{ title: 'Tên thiết bị', dataIndex: 'name' }, { title: 'Trạng thái', render: (_, row) => <><StatusPill domain="device.status" value={row.status} /><span> · {row.online ? 'Trực tuyến' : 'Ngoại tuyến'}</span></> }, { title: 'Thấy cuối', render: (_, row) => dateTime(row.last_seen_at) }, { title: 'Phiên bản', dataIndex: 'app_version' }, ...(owner ? [{ title: 'Thao tác', render: (_: unknown, row: components['schemas']['Device']) => <Button danger disabled={row.status === 'REVOKED'} onClick={() => setRevoke(row)}>Thu hồi</Button> }] : [])]} /></>}</> : <Empty description="Chưa có cửa" />}</section></div>
    <Modal open={deviceName !== undefined} title="Thêm thiết bị" okText="Tạo mã ghép" cancelText="Hủy" confirmLoading={busy} okButtonProps={{ disabled: !deviceName?.trim() }} onCancel={() => { if (!busy) setDeviceName(undefined); }} onOk={() => void run(async () => { if (!gate || !deviceName) return; setPairing(readResult(await api.POST('/devices', { body: { gate_id: gate.id, name: deviceName.trim() } }))); setDeviceName(undefined); })}><label htmlFor="device-name">Tên thiết bị</label><Input id="device-name" value={deviceName} onChange={event => setDeviceName(event.target.value)} /></Modal>
    <Modal open={!!pairing} title="Ghép Kiosk" onCancel={() => setPairing(undefined)} footer={<Button onClick={() => setPairing(undefined)}>Đóng mã ghép</Button>}>{pairing && <div className="pairing-code"><QRCode value={pairing.qr_payload} /><Statistic title="Mã 6 số" value={pairing.pairing_code} formatter={() => pairing.pairing_code} /><p>Địa chỉ Hub: {JSON.parse(pairing.qr_payload).hub}</p><Statistic.Countdown title="Mã hết hạn sau" value={new Date(pairing.expires_at).getTime()} onFinish={() => { setPairing(undefined); setNotice('Mã ghép đã hết hạn. Tạo lại thiết bị để lấy mã mới.'); }} /></div>}</Modal>
    <Modal open={!!revoke} title="Thu hồi thiết bị" okText="Thu hồi" cancelText="Hủy" confirmLoading={busy} onCancel={() => { if (!busy) setRevoke(undefined); }} onOk={() => void run(async () => { if (!revoke) return; readResult(await api.POST('/devices/{id}/revoke', { params: { path: { id: revoke.id } } })); setRevoke(undefined); })}><p>Ngắt kết nối và thu hồi quyền truy cập của {revoke?.name}?</p>{error && <Alert type="error" message={error} />}</Modal>
  </>;
}

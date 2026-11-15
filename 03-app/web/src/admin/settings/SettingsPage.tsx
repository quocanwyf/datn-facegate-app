import { useFormExitWarning } from '../../shared/useFormExitWarning';
import { AnimatedTable as Table } from '../../components/AnimatedTable';
import { useRef, useState } from 'react';
import { Alert, Button, Descriptions, Form, InputNumber, Modal, Switch, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { api, type Session } from '../../api/client';
import type { components } from '../../api/schema';
import { readResult, requestMessage } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { QueryState } from '../../components/QueryState';
import { cos, dateTime } from '../../shared/format';
const fields: { key: keyof components['schemas']['RecognitionSettings']; label: string; unit: string; min: number; max?: number; step?: number }[] = [
  { key: 'window_size', label: 'Cửa sổ W', unit: 'khung', min: 1 }, { key: 'match_min', label: 'Ngưỡng MATCH', unit: 'khung', min: 1 }, { key: 'unknown_min', label: 'Ngưỡng UNKNOWN', unit: 'khung', min: 1 }, { key: 'spoof_min', label: 'Ngưỡng SPOOF', unit: 'khung', min: 1 },
  { key: 'lost_face_sec', label: 'Mất mặt', unit: 'giây', min: 0, step: .1 }, { key: 'iou_reset', label: 'Đặt lại theo IoU', unit: '', min: 0, max: 1, step: .01 },
  { key: 'cooldown_employee_sec', label: 'Giãn lượt nhân viên', unit: 'giây', min: 0 }, { key: 'cooldown_alert_sec', label: 'Giãn cảnh báo', unit: 'giây', min: 0 }, { key: 'result_display_sec', label: 'Hiển thị kết quả', unit: 'giây', min: 1 },
  { key: 'max_fps', label: 'Khung hình tối đa', unit: 'khung/giây', min: 1 }, { key: 'frame_long_side', label: 'Cạnh dài ảnh', unit: 'px', min: 80 }, { key: 'jpeg_quality', label: 'Chất lượng JPEG', unit: '%', min: 1, max: 100 }, { key: 'min_face_px', label: 'Kích thước mặt tối thiểu', unit: 'px', min: 1 }, { key: 'max_abs_yaw_ratio', label: 'Độ nghiêng tối đa', unit: '', min: 0, max: 1, step: .01 },
  { key: 'attendance_window_before_h', label: 'Cửa sổ trước ca', unit: 'giờ', min: 0 }, { key: 'attendance_window_after_h', label: 'Cửa sổ sau ca', unit: 'giờ', min: 0 }, { key: 'min_checkout_after_checkin_min', label: 'Giãn lượt vào và ra', unit: 'phút', min: 0 }, { key: 'forgot_out_before_end_h', label: 'Nghi quên quét trước cuối ca', unit: 'giờ', min: 0 },
];
export function SettingsPage({ session }: { session: Session }) {
  const owner = session.user.roles.some(grant => grant.role === 'OWNER');
  const settings = useQuery({ queryKey: ['recognition-settings'], queryFn: async () => readResult(await api.GET('/settings/recognition')) });
  const model = useQuery({ queryKey: ['model'], queryFn: async () => readResult(await api.GET('/models/active')) });
  const health = useQuery({ queryKey: ['health'], queryFn: async () => readResult(await api.GET('/health')) });
  const [form] = Form.useForm<components['schemas']['RecognitionSettings']>(); const [confirm, setConfirm] = useState(false); const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [busy, setBusy] = useState(false); const lock = useRef(false);
  useFormExitWarning(form);
  async function save() { if (lock.current || !owner) return; lock.current = true; setBusy(true); setError(''); setNotice(''); try { readResult(await api.PUT('/settings/recognition', { body: form.getFieldsValue() })); setConfirm(false); await settings.refetch(); setNotice('Đã lưu toàn bộ cấu hình'); } catch (failure) { setError(requestMessage(failure)); } finally { lock.current = false; setBusy(false); } }
  return <><PageHero title="Cấu hình nhận dạng" description="Một mô hình UniFace + V1 s3 · cấu hình dùng chung tại Hub." />
    {!owner && <Alert className="feedback" type="info" message="Bạn chỉ có quyền xem cấu hình." />}{error && <Alert className="feedback" type="error" role="alert" message={error} />}{notice && <Alert className="feedback" type="success" role="status" message={notice} />}
    <section className="content-panel profile-section"><h2>Mô hình đang chạy</h2><QueryState query={model} /><QueryState query={health} />
      {health.data && <Alert type={health.data.model_verified && health.data.status === 'ok' ? 'success' : 'warning'} showIcon message={health.data.model_verified && health.data.status === 'ok' ? 'Mô hình đã kiểm tra · nhận dạng sẵn sàng' : 'Nhận dạng chưa sẵn sàng hoặc đang tạm ngưng'} description={`Gallery: ${health.data.gallery_size} nhân viên · CPU/GPU: ${health.data.gpu ? 'GPU' : 'CPU'}`} />}
      {model.data && <Descriptions column={1} items={[{ key: 'name', label: 'Tên', children: `${model.data.name} · epoch ${model.data.epoch}` }, { key: 'sha', label: 'SHA-256 nguồn', children: <Typography.Text copyable={{ text: model.data.source_sha256 }}>{model.data.source_sha256.slice(0, 16)}…</Typography.Text> }, { key: 'runtime', label: 'Runtime', children: <pre>{JSON.stringify(model.data.runtime, null, 2)}</pre> }, { key: 'verified', label: 'Kiểm tra lúc', children: dateTime(model.data.verified_at) }]} />}
    </section>
    <section className="content-panel profile-section"><h2>Ngưỡng nhận dạng</h2><Table rowKey="level" pagination={false} dataSource={model.data?.thresholds} columns={[{ title: 'Mức', dataIndex: 'label' }, { title: 'Cos', render: (_, item) => cos(item.cos_threshold) }, { title: 'Nguồn', dataIndex: 'source_ref' }]} /><p>b̃/s: {cos(model.data?.t_bs)} — chỉ tham khảo.</p>
      <Table pagination={false} rowKey="level" dataSource={[{ level: 'Mặc định', fpir: '5,0% ± 0,7', fnir: '10,6% ± 0,9' }, { level: 'Nghiêm ngặt', fpir: '1% (hiệu chỉnh trên chính tập test)', fnir: '≈ 16,4%' }]} columns={[{ title: 'Mức ngưỡng', dataIndex: 'level' }, { title: 'FPIR', dataIndex: 'fpir' }, { title: 'FNIR rank-1', dataIndex: 'fnir' }]} />
      <Alert type="info" showIcon message="Số đo trên BLUFR (gallery 1000 người), chưa đo tại văn phòng" description="Mặc định giảm từ chối nhầm nhưng tăng nhận nhầm người lạ. Mức theo từng cửa chỉnh tại Cửa & thiết bị." />
    </section><section className="content-panel"><h2>Bộ quyết định</h2><QueryState query={settings} />
      {settings.data && <Form key={settings.dataUpdatedAt} form={form} initialValues={settings.data} layout="vertical" disabled={!owner || busy} onFinish={() => setConfirm(true)}>
        <div className="settings-grid">{fields.map(field => <Form.Item key={field.key} name={field.key} label={`${field.label}${field.unit ? ` (${field.unit})` : ''}`} rules={[{ required: true, message: 'Nhập giá trị' }, ...(['match_min', 'unknown_min', 'spoof_min'].includes(field.key) ? [({ getFieldValue }: { getFieldValue: (name: string) => number }) => ({ validator: async (_: unknown, value: number) => { if (value > getFieldValue('window_size')) throw new Error('Ngưỡng đếm không được lớn hơn W'); } })] : [])]} dependencies={['window_size']}><InputNumber min={field.min} max={field.max} step={field.step ?? 1} precision={field.step ? undefined : 0} className="full-width" /></Form.Item>)}</div>
        <h2>Chống giả mạo</h2><Form.Item name="anti_spoof_enabled" valuePropName="checked" label="Bật chống giả mạo"><Switch disabled /></Form.Item><Form.Item name="liveness_threshold" label="Ngưỡng L"><InputNumber min={0} max={1} disabled /></Form.Item><p>Chưa hiệu chỉnh — bật sau T13</p>{owner && <Button htmlType="submit" type="primary" loading={busy}>Lưu cấu hình</Button>}
      </Form>}
    </section><Modal open={confirm} title="Lưu cấu hình nhận dạng" okText="Xác nhận lưu" cancelText="Hủy" confirmLoading={busy} onCancel={() => { if (!busy) setConfirm(false); }} onOk={() => void save()}><p>Cấu hình mới áp dụng cho Hub và các Kiosk đang kết nối.</p>{error && <Alert type="error" message={error} />}</Modal>
  </>;
}

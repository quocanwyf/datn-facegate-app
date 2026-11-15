import { useState } from 'react';
import { Alert, Button, Descriptions, Empty, Modal, Space, Tabs } from 'antd';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import { api, type Session } from '../../api/client';
import { readResult, requestMessage } from '../../api/result';
import { PageHero } from '../../components/PageHero';
import { QueryState } from '../../components/QueryState';
import { StatusPill } from '../../components/StatusPill';
import { FaceImages } from '../../components/FaceImages';
import { EmployeeEditor } from './EmployeeEditor';
import { dateTime } from '../../shared/format';
export function EmployeeDetail({ session }: { session: Session }) {
  const id = useLocation().pathname.split('/').pop()!; const navigate = useNavigate(); const client = useQueryClient();
  const [edit, setEdit] = useState(false); const [remove, setRemove] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const write = session.user.roles.some(grant => ['OWNER', 'HR'].includes(grant.role));
  const employee = useQuery({ queryKey: ['employee', id], queryFn: async ({ signal }) => readResult(await api.GET('/employees/{id}', { params: { path: { id } }, signal })) });
  const profiles = useQuery({ queryKey: ['employee-faces', id], enabled: write, queryFn: async ({ signal }) => readResult(await api.GET('/face-profiles', { params: { query: { employee_id: id } }, signal })) });
  const departments = useQuery({ queryKey: ['departments', session.user.id], queryFn: async () => readResult(await api.GET('/departments')) });
  async function deleteFace() {
    if (busy) return; setBusy(true); setError('');
    try { readResult(await api.DELETE('/employees/{id}/face', { params: { path: { id } } })); setRemove(false); await Promise.all([client.invalidateQueries({ queryKey: ['employee', id] }), client.invalidateQueries({ queryKey: ['employee-faces', id] }), client.invalidateQueries({ queryKey: ['faces'] })]); }
    catch (failure) { setError(requestMessage(failure)); } finally { setBusy(false); }
  }
  const item = employee.data;
  return <><PageHero title={item?.full_name ?? 'Chi tiết nhân viên'} description={`Nhân viên / ${item?.code ?? '…'}`} action={<Button onClick={() => navigate('/admin/employees')}>Danh sách nhân viên</Button>} /><QueryState query={employee} />
    {item && <section className="content-panel"><Space wrap><StatusPill domain="employee.status" value={item.status} /><StatusPill domain="employee.attendance_method" value={item.attendance_method} /><StatusPill domain="face_profile.status" value={item.face_profile_status} /></Space><Tabs items={[
      { key: 'info', label: 'Thông tin', children: <><Descriptions column={2} items={[{ key: 'code', label: 'Mã nhân viên', children: item.code }, { key: 'name', label: 'Họ tên', children: item.full_name }, { key: 'department', label: 'Phòng ban', children: item.department_name }, { key: 'email', label: 'Email', children: item.email || '—' }, { key: 'phone', label: 'Số điện thoại', children: item.phone || '—' }, { key: 'joined', label: 'Ngày vào làm', children: item.joined_at?.split('-').reverse().join('/') || '—' }]} />{write && <Button onClick={() => setEdit(true)}>Sửa nhân viên</Button>}</> },
      ...(write ? [{ key: 'face', label: 'Khuôn mặt', children: <><p>Đồng ý sử dụng khuôn mặt: {dateTime(item.face_consent_at)}</p><QueryState query={profiles} />{profiles.data?.items.length ? profiles.data.items.map(profile => <section key={profile.id} className="profile-section"><StatusPill domain="face_profile.status" value={profile.status} /><p>Người đăng ký: {profile.enrolled_by} · {dateTime(profile.enrolled_at)}</p><FaceImages samples={profile.samples} /></section>) : !profiles.isPending && <Empty description="Chưa có hồ sơ. Đăng ký tại Kiosk bằng PIN HR." />}<Button danger className="section-actions" onClick={() => { setError(''); setRemove(true); }}>Xoá dữ liệu khuôn mặt</Button></> }] : []),
      { key: 'shifts', label: 'Ca', children: <Button onClick={() => navigate('/admin/schedules')}>Xem ca và phân ca</Button> },
      { key: 'attendance', label: 'Chấm công', children: <Button onClick={() => navigate(`/admin/attendance?employee_id=${id}`)}>Xem bảng công nhân viên</Button> },
      { key: 'events', label: 'Sự kiện', children: <Button onClick={() => navigate(`/admin/events?employee_id=${id}`)}>Xem sự kiện nhân viên</Button> },
    ]} /></section>}
    {edit && item && <EmployeeEditor employee={item} session={session} departments={departments.data ?? []} onClose={() => setEdit(false)} onSaved={() => { setEdit(false); void client.invalidateQueries({ queryKey: ['employee', id] }); void client.invalidateQueries({ queryKey: ['employees'] }); }} />}
    <Modal title="Xoá dữ liệu khuôn mặt" open={remove} okText="Xoá dữ liệu khuôn mặt" cancelText="Hủy" okButtonProps={{ danger: true }} confirmLoading={busy} closable={!busy} maskClosable={!busy} cancelButtonProps={{ disabled: busy }} onCancel={() => setRemove(false)} onOk={() => void deleteFace()}>{error && <Alert role="alert" type="error" message={error} />}<p>Xoá toàn bộ hồ sơ, ảnh mẫu và đặc trưng của {item?.full_name}? Nhân viên chuyển sang chấm công hộ. Lịch sử công và sự kiện được giữ lại.</p></Modal>
  </>;
}
